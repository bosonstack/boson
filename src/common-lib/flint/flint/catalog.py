"""
The Flint catalog manages metadata that proxies and describes items
such as tables and objects that are stored in the metastore. The catalog
is not responsible for, and does not handle, item content. Items are unique
on (item type, name, *tags).
"""

import os
from typing import Dict, List, Union
from dataclasses import dataclass, field
import json
from enum import Enum
import polars as pl
import fsspec
from datetime import datetime
import uuid
import re
from typing import Tuple, Dict
from urllib.parse import parse_qsl
from urllib.parse import urlencode

STORAGE_BUCKET = "metastore"

def _get_storage_credentials() -> Dict[str, str]:
    return {
        "key": os.getenv("STORAGE_USER"),
        "secret": os.getenv("STORAGE_PASSWORD"),
        "client_kwargs": {
            "endpoint_url": os.getenv("FLINT_CONTROL_PLANE_ENDPOINT")
        }
    }
STORAGE_CREDENTIALS = _get_storage_credentials()

def _get_polars_storage_options() -> Dict[str, str]:
    return {
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": STORAGE_CREDENTIALS["key"],
        "AWS_SECRET_ACCESS_KEY": STORAGE_CREDENTIALS["secret"],
        "AWS_ALLOW_HTTP": "true",
        "AWS_ENDPOINT_URL": STORAGE_CREDENTIALS["client_kwargs"]["endpoint_url"]
    }
POLARS_STORAGE_OPTIONS = _get_polars_storage_options()

def _get_deltalake_storage_options() -> Dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": STORAGE_CREDENTIALS["key"],
        "AWS_SECRET_ACCESS_KEY": STORAGE_CREDENTIALS["secret"],
        "AWS_REGION": "us-east-1",
        "AWS_ALLOW_HTTP": "true",
        "AWS_ENDPOINT_URL": STORAGE_CREDENTIALS["client_kwargs"]["endpoint_url"],
    }
DELTALAKE_STORAGE_OPTIONS = _get_deltalake_storage_options()

def _prefix_exists(uri: str) -> bool:
    """
    Return True if the `uri` file exists.
    """
    uri = uri.rstrip("/")
    fs = fsspec.filesystem("s3", **STORAGE_CREDENTIALS)
    return fs.exists(uri)

def _catalog_exists() -> bool:
    """
    Return True if the catalog S3 prefix exists.
    """
    return _prefix_exists(f"s3://{STORAGE_BUCKET}/_catalog/_delta_log/")

def _create_catalog_if_not_exists():
    if _catalog_exists():
        return
        
    columns = {
        "uri": pl.Utf8,
        "name": pl.Utf8,
        "type": pl.Utf8,
        "tags": pl.Utf8,
        "schema": pl.Utf8,
        "created_at": pl.Int64,
        "updated_at": pl.Int64
    }

    empty_df = pl.DataFrame(
        { col: pl.Series([], dtype=dtype) for col, dtype in columns.items() }
    )

    empty_df.write_delta(
        f"s3://{STORAGE_BUCKET}/_catalog",
        storage_options=POLARS_STORAGE_OPTIONS,
        mode="overwrite",
    )

def _ensure_catalog(fn):
    """
    Decorator that creates the catalog Delta table if needed before running fn().
    """
    def wrapper(*args, **kwargs):
        _create_catalog_if_not_exists()
        return fn(*args, **kwargs)
    return wrapper

def get_delta_schema(uri: str) -> Dict[str, str]:
    """
    Read only the schema of a Delta table (no data load.)
    """
    lf = pl.scan_delta(uri, storage_options=POLARS_STORAGE_OPTIONS)
    raw_schema: Dict[str, pl.DataType] = lf.collect_schema()
    return {col: str(dtype) for col, dtype in raw_schema.items()}

class CatalogItemType(str, Enum):
    TABLE = "table"
    OBJECT = "object"

class CatalogItemTransactionViolationError(RuntimeError): ...

class WriteCatalogItemTxn:
    """
    An atomic transaction that facilitates writing an item to the metastore
    and tracking it in the catalog. Requires two steps to be committed:

    1) Determine and return the provisioned item storage uri to the caller
    2) If entity was correctly saved to uri, commits the item's metadata
       to the catalog, else raise

    Callers are responsible for actually manipulating content at the 
    uri. Transaction will create a new uri if it does not already exist
    for the item definition.
    """

    _VALID_NAME_TAG_RE = re.compile(r'^[A-Za-z0-9\-\_\.\/]+$')

    @_ensure_catalog
    def __init__(
        self,
        item_type: CatalogItemType,
        name: str,
        tags: Dict[str, str]
    ):
        if not isinstance(name, str) or not WriteCatalogItemTxn._VALID_NAME_TAG_RE.fullmatch(name):
            raise ValueError(
                f"Invalid characters in name '{name}'. "
                "Allowed characters are letters, digits, '-', '_', '.', and '/'."
            )

        # Validate each tag key and value
        for key, value in tags.items():
            if not isinstance(key, str) or not WriteCatalogItemTxn._VALID_NAME_TAG_RE.fullmatch(key):
                raise ValueError(
                    f"Invalid characters in tag key '{key}'. "
                    "Allowed characters are letters, digits, '-', '_', '.', and '/'."
                )
            if not isinstance(value, str) or not WriteCatalogItemTxn._VALID_NAME_TAG_RE.fullmatch(value):
                raise ValueError(
                    f"Invalid characters in tag value '{value}'. "
                    "Allowed characters are letters, digits, '-', '_', '.', and '/'."
                )
            
        self._item_type = item_type
        self._name = name
        tags_str = json.dumps(tags, sort_keys=True)
        self._tags_str = tags_str
    
        catalog_scan = pl.scan_delta(
            f"s3://{STORAGE_BUCKET}/_catalog",
            storage_options=POLARS_STORAGE_OPTIONS
        )

        existing = (
            catalog_scan
            .filter((pl.col("name") == name) &
                    (pl.col("type") == item_type.value) &
                    (pl.col("tags") == tags_str))
            .limit(1)
            .collect()
        )

        item_exists = existing.height > 0
        if item_exists:
            item_dict = existing.to_dicts()[0]
            self.uri: str = item_dict["uri"]
            self._existing_item_dict = item_dict
        else:
            current_timestamp = int(datetime.now().timestamp())
            _uuid = uuid.uuid4()
            self.uri = f"s3://{STORAGE_BUCKET}/{item_type.value}/{current_timestamp}/{_uuid}/{name}"
            self._existing_item_dict = None

    def __enter__(self):
        return self.uri
    
    def __exit__(self, exc_type, exc, tb):
        self._tags_str

        current_timestamp = int(datetime.now().timestamp())
        existing_created = (self._existing_item_dict["created_at"] 
                            if self._existing_item_dict is not None else None)

        if self._item_type == CatalogItemType.OBJECT:
            if not _prefix_exists(f"{self.uri}"):
                raise CatalogItemTransactionViolationError(
                    f"Could not find object at {self.uri}."
                )
            
            item_metadata = pl.DataFrame({
                "uri":    [self.uri],
                "name":   [self._name],
                "type":   [self._item_type.value],
                "tags":   [self._tags_str],
                "schema": pl.Series([None], dtype=pl.Utf8),
                "created_at": existing_created or current_timestamp,
                "updated_at": current_timestamp
            })
        elif self._item_type == CatalogItemType.TABLE:
            if not _prefix_exists(f"{self.uri}/_delta_log/"):
                raise CatalogItemTransactionViolationError(
                    f"Could not find delta table at {self.uri}."
                )

            schema_dict = get_delta_schema(self.uri)
            schema_json = json.dumps(schema_dict, sort_keys=True)

            item_metadata = pl.DataFrame({
                "uri":    [self.uri],
                "name":   [self._name],
                "type":   [self._item_type.value],
                "tags":   [self._tags_str],
                "schema": [schema_json],
                "created_at": existing_created or current_timestamp,
                "updated_at": current_timestamp
            })
        else:
            raise NotImplementedError(f"{self._item_type.value} is not a supported catalog item type.")

        # Update metadata record
        merge_opts: Dict[str, str] = {
            "predicate":    "source.name = target.name AND "
                            "source.type = target.type AND "
                            "source.tags = target.tags",
            "source_alias": "source",
            "target_alias": "target",
        }
        (
            item_metadata
            .write_delta(
                f"s3://{STORAGE_BUCKET}/_catalog",
                mode="merge",
                storage_options=POLARS_STORAGE_OPTIONS,
                delta_merge_options=merge_opts,
            )
            .when_matched_update({
                "schema": "source.schema",
                "updated_at": "source.updated_at",
            })
            .when_not_matched_insert_all()
            .execute()
        )

class CatalogItemNotFoundError(Exception): ...

@dataclass
class ItemMetadata:
    uri: str
    name: str
    type: CatalogItemType
    tags: Dict[str, str]
    created_at: int
    updated_at: int

@dataclass
class ObjectItemMetadata(ItemMetadata):
    type: CatalogItemType = field(default=CatalogItemType.OBJECT, init=False)

@dataclass
class TableItemMetadata(ItemMetadata):
    schema: Dict[str, str]
    type: CatalogItemType = field(default=CatalogItemType.TABLE, init=False)

@_ensure_catalog
def get_catalog_item(
    item_type: CatalogItemType,
    name: str,
    tags: Dict[str, str]
) -> Union[ObjectItemMetadata, TableItemMetadata]:
    """
    Returns the uri corresponding to the provided catalog item definition.
    Raises if the item does not exist.
    """
    tags_str = json.dumps(tags, sort_keys=True)
    catalog_scan = pl.scan_delta(
        f"s3://{STORAGE_BUCKET}/_catalog",
        storage_options=POLARS_STORAGE_OPTIONS
    )

    existing = (
        catalog_scan
        .filter((pl.col("name") == name) &
                (pl.col("type") == item_type.value) &
                (pl.col("tags") == tags_str))
        .limit(1)
        .collect()
    )

    item_exists = existing.height > 0
    if not item_exists:
        raise CatalogItemNotFoundError(
            f"No matching catalog item: name={name}, type={item_type}, tags={tags}"
        )
    item_dict = existing.to_dicts()[0]

    if item_type == CatalogItemType.OBJECT:
        return ObjectItemMetadata(
            uri=item_dict["uri"],
            name=name,
            tags=tags,
            created_at=item_dict["created_at"],
            updated_at=item_dict["updated_at"]
        )
    elif item_type == CatalogItemType.TABLE:
        return TableItemMetadata(
            uri=item_dict["uri"],
            name=name,
            tags=tags,
            schema=json.loads(item_dict["schema"]),
            created_at=item_dict["created_at"],
            updated_at=item_dict["updated_at"]
        )
    else:
        raise NotImplementedError(f"{item_type.value} is not a supported catalog item type.")

@_ensure_catalog
def mv_catalog_item(
    item_type: CatalogItemType,
    old_name: str,
    old_tags: Dict[str, str],
    new_name: str,
    new_tags: Dict[str, str]
) -> None:
    """
    Moves a catalog item by updating its name and tags. 
    """
    old_tags_str = json.dumps(old_tags, sort_keys=True)
    new_tags_str = json.dumps(new_tags, sort_keys=True)
    current_timestamp = int(datetime.now().timestamp())

    catalog_scan = pl.scan_delta(
        f"s3://{STORAGE_BUCKET}/_catalog",
        storage_options=POLARS_STORAGE_OPTIONS
    )

    existing = (
        catalog_scan
        .filter((pl.col("name") == old_name) &
                (pl.col("type") == item_type.value) &
                (pl.col("tags") == old_tags_str))
        .limit(1)
        .collect()
    )

    item_exists = existing.height > 0
    if not item_exists:
        raise CatalogItemNotFoundError(
            f"No matching catalog item: name={old_name}, type={item_type}, tags={old_tags}"
        )
    
    row = {
        "old_name":    [old_name],
        "old_type":    [item_type.value],
        "old_tags":    [old_tags_str],

        "new_name":    [new_name],
        "new_tags":    [new_tags_str],
        "new_updated": [current_timestamp],
    }
    source_df = pl.DataFrame(row)

    merge_opts = {
        "predicate":    "target.name = source.old_name AND "
                        "target.type = source.old_type AND "
                        "target.tags = source.old_tags",
        "source_alias": "source",
        "target_alias": "target",
    }

    (
        source_df
        .write_delta(
            f"s3://{STORAGE_BUCKET}/_catalog",
            mode="merge",
            storage_options=POLARS_STORAGE_OPTIONS,
            delta_merge_options=merge_opts,
        )
        .when_matched_update({
            "name": "source.new_name",
            "tags": "source.new_tags",
            "updated_at": "source.new_updated"
        })
        .execute()
    )

@_ensure_catalog
def query_catalog(
    *,
    name: str | None = None,
    item_type: CatalogItemType | None = None,
    created_at_lower: int | None = None,
    created_at_upper: int | None = None,
    updated_at_lower: int | None = None,
    updated_at_upper: int | None = None,
    tag_filter: dict[str, str] | None = None,
) -> list[dict]:
    """
    Retrieve catalog entries matching the given criteria.
    Returns a list of ObjectItemMetadata or TableItemMetadata dataclass instances.
    """
    lf = (
        pl.scan_delta(f"s3://{STORAGE_BUCKET}/_catalog", storage_options=POLARS_STORAGE_OPTIONS)
        .with_columns(
            pl.col("tags").str.json_decode().alias("tags_struct")
        )
    )

    predicates: List[pl.Expr] = []
    if name is not None:
        predicates.append(pl.col("name") == name)
    if item_type is not None:
        predicates.append(pl.col("type") == item_type.value)
    if created_at_lower is not None:
        predicates.append(pl.col("created_at") >= created_at_lower)
    if created_at_upper is not None:
        predicates.append(pl.col("created_at") <= created_at_upper)
    if updated_at_lower is not None:
        predicates.append(pl.col("updated_at") >= updated_at_lower)
    if updated_at_upper is not None:
        predicates.append(pl.col("updated_at") <= updated_at_upper)
    if tag_filter:
        for k, v in tag_filter.items():
            predicates.append(
                pl.col("tags").map_elements(
                    lambda js: json.loads(js).get(k) == v,
                    return_dtype=pl.Boolean()
                )
            )

    for p in predicates:
        lf = lf.filter(p)

    rows = lf.collect().to_dicts()
    results: List[ItemMetadata] = []

    for row in rows:
        uri = row["uri"]
        name = row["name"]
        item_type = CatalogItemType(row["type"])
        tags = json.loads(row["tags"])
        created = int(row["created_at"])
        updated = int(row["updated_at"])

        if item_type == CatalogItemType.OBJECT:
            results.append(ObjectItemMetadata(
                uri=uri,
                name=name,
                tags=tags,
                created_at=created,
                updated_at=updated
            ))
        elif item_type == CatalogItemType.TABLE:
            schema_dict = json.loads(row["schema"])
            results.append(TableItemMetadata(
                uri=uri,
                name=name,
                tags=tags,
                created_at=created,
                updated_at=updated,
                schema=schema_dict
            ))
        else:
            raise NotImplementedError(f"{item_type.value} is not a supported catalog item type.")

    return results

class DeleteCatalogItemTxn:
    """
    An atomic transaction that facilitates deleting an item's content from storage
    and removing its metadata from the catalog. The caller is responsible for
    actually removing the content at the provided URI. On exit, this verifies
    the content was deleted and then removes the metadata row.
    """
    @_ensure_catalog
    def __init__(
        self,
        item_type: CatalogItemType,
        name: str,
        tags: Dict[str, str]
    ):
        self._item_type = item_type
        self._name = name
        tags_str = json.dumps(tags, sort_keys=True)
        self._tags_str = tags_str

        catalog_scan = pl.scan_delta(
            f"s3://{STORAGE_BUCKET}/_catalog",
            storage_options=POLARS_STORAGE_OPTIONS
        )
        existing = (
            catalog_scan
            .filter((pl.col("name") == name) &
                    (pl.col("type") == item_type.value) &
                    (pl.col("tags") == tags_str))
            .limit(1)
            .collect()
        )

        item_exists = existing.height > 0
        if not item_exists:
            raise CatalogItemNotFoundError(
                f"No matching catalog item: name={name}, type={item_type}, tags={tags}"
            )

        item_dict = existing.to_dicts()[0]
        self.uri: str = item_dict["uri"]

    def __enter__(self):
        return self.uri

    def __exit__(self, exc_type, exc, tb):
        if self._item_type == CatalogItemType.OBJECT:
            if _prefix_exists(self.uri):
                raise CatalogItemTransactionViolationError(
                    f"Object still exists at {self.uri}."
                )
        elif self._item_type == CatalogItemType.TABLE:
            if _prefix_exists(f"{self.uri}/_delta_log/"):
                raise CatalogItemTransactionViolationError(
                    f"Delta table still exists at {self.uri}."
                )
        else:
            raise NotImplementedError(f"{self._item_type.value} is not a supported catalog item type.")

        # Remove metadata row from the catalog Delta table
        src = pl.DataFrame({
            "name": [self._name],
            "type": [self._item_type.value],
            "tags": [self._tags_str]
        })

        merge_opts: Dict[str, str] = {
            "predicate":    "target.name = source.name AND "
                            "target.type = source.type AND "
                            "target.tags = source.tags",
            "source_alias": "source",
            "target_alias": "target",
        }
        (
            src
            .write_delta(
                f"s3://{STORAGE_BUCKET}/_catalog",
                mode="merge",
                storage_options=POLARS_STORAGE_OPTIONS,
                delta_merge_options=merge_opts,
            )
            .when_matched_delete()
            .execute()
        )

def parse_item_path(path: str) -> Tuple[str, Dict[str, str]]:
    if "?" in path:
        name, query = path.split("?", 1)
        tags = dict(parse_qsl(query))
    else:
        name = path
        tags = {}
    return name, tags

def build_item_path(name: str, tags: Dict[str, str]) -> str:
    if tags:
        query = urlencode(tags)
        return f"{name}?{query}"
    else:
        return name