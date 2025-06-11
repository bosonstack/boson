"""
This module is a wrapper around the Flint catalog for the purposes 
of exposing an API for the manipulation of objects.

Each helper function represents an intent against the Catalog.
"""

from typing import Any, Dict, BinaryIO, Optional, List, Tuple

import fsspec
from flint.catalog import (
    CatalogItemType,
    STORAGE_CREDENTIALS,
    WriteCatalogItemTxn,
    DeleteCatalogItemTxn,
    mv_catalog_item,
    get_catalog_item,
    CatalogItemNotFoundError,
    query_catalog,
    parse_item_path
)

class _ObjectTxnFile:
    """
    Internal context manager tying a file handle to a catalog transaction.
    - mode starting with "r" → read-only (no txn).
    - mode "wb" or "ab" → two-phase commit via WriteCatalogItemTxn.
    """
    def __init__(
        self,
        name: str,
        tags: Dict[str, str],
        mode: str = "rb",
        fs_open_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.tags = tags
        self.mode = mode
        self.fs_open_kwargs = fs_open_kwargs or {}
        self._txn: Optional[WriteCatalogItemTxn] = None
        self._file: BinaryIO

    def __enter__(self) -> BinaryIO:
        fs = fsspec.filesystem("s3", **STORAGE_CREDENTIALS)

        if self.mode.startswith("r"):
            catalog_item = get_catalog_item(
                item_type=CatalogItemType.OBJECT,
                name=self.name,
                tags=self.tags,
            )
            uri = catalog_item.uri
            self._file = fs.open(uri, self.mode, **self.fs_open_kwargs)
            return self._file

        elif self.mode in ("wb", "ab"):
            self._txn = WriteCatalogItemTxn(
                item_type=CatalogItemType.OBJECT,
                name=self.name,
                tags=self.tags,
            )
            physical_uri = self._txn.__enter__()
            self._file = fs.open(physical_uri, self.mode, **self.fs_open_kwargs)
            return self._file

        else:
            raise ValueError(
                f"Unsupported mode '{self.mode}'. Use 'rb', 'wb', or 'ab'."
            )

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._file.close()

        if self._txn is not None:
            self._txn.__exit__(exc_type, exc_val, exc_tb)

def open_object(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    mode: str = "rb",
    **fs_open_kwargs: Any,
) -> BinaryIO:
    """
    Open an object in a transaction-aware way.
    If `path` is not provided, falls back to `name` and `tags`.

    Modes:
      - "rb" → read existing object.
      - "wb" → create or overwrite.
      - "ab" → append to existing.

    Returns
    -------
    BinaryIO
      A file-like handle. On write/append, updates the Flint catalog.
    """
    if path:
        name, tags = parse_item_path(path)

    return _ObjectTxnFile(name=name, tags=tags, mode=mode, fs_open_kwargs=fs_open_kwargs)

def delete_object(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Delete an object's bytes and remove it from the Flint catalog.
    If `path` is not provided, falls back to `name` and `tags`.
    """
    if path:
        name, tags = parse_item_path(path)

    with DeleteCatalogItemTxn(
        item_type=CatalogItemType.OBJECT,
        name=name,
        tags=tags
    ) as uri:
        fs = fsspec.filesystem("s3", **STORAGE_CREDENTIALS)
        fs.rm(uri)

def move_object(
    old_name: str,
    old_tags: Dict[str, str],
    new_name: str,
    new_tags: Dict[str, str],
) -> None:
    """
    Moves an object's logical location by updating its name and tags in
    the Flint catalog.
    """
    mv_catalog_item(
        CatalogItemType.OBJECT,
        old_name,
        old_tags,
        new_name,
        new_tags
    )

def exists_object(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Return True if an object with this name and exact tags exists in the 
    Flint catalog. If `path` is not provided, falls back to `name` and `tags`.
    """
    if path:
        name, tags = parse_item_path(path)
        
    try:
        get_catalog_item(
            item_type=CatalogItemType.OBJECT,
            name=name,
            tags=tags,
        )
        return True
    except CatalogItemNotFoundError:
        return False
    
def search_objects(
    tag_filter: Optional[Dict[str, str]] = None,
    created_at_lower: Optional[int] = None,
    created_at_upper: Optional[int] = None,
    updated_at_lower: Optional[int] = None,
    updated_at_upper: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    List all objects (and their metadata) matching the given filters.

    Parameters
    ----------
    tag_filter
      Only return objects whose tags contain all key-value pairs here.
    created_at_lower, created_at_upper
      UNIX timestamps to filter on creation time.
    updated_at_lower, updated_at_upper
      UNIX timestamps to filter on last update time.

    Returns
    -------
    List of metadata dicts (each with keys: uri, name, tags, created_at, updated_at).
    """
    results = query_catalog(
        item_type=CatalogItemType.OBJECT,
        tag_filter=tag_filter,
        created_at_lower=created_at_lower,
        created_at_upper=created_at_upper,
        updated_at_lower=updated_at_lower,
        updated_at_upper=updated_at_upper,
    )

    output: List[Dict[str, Any]] = []
    for item in results:
        # item is an ObjectItemMetadata dataclass
        output.append({
            "uri": item.uri,
            "name": item.name,
            "tags": item.tags,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        })

    return output