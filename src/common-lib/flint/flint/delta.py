"""
This module is a wrapper around the Flint catalog for the purposes 
of exposing an API for the manipulation of Delta tables.

Each helper function represents an intent against the Catalog.
"""

import polars as pl
from .catalog import (
    CatalogItemType, 
    get_catalog_item, 
    POLARS_STORAGE_OPTIONS, 
    DELTALAKE_STORAGE_OPTIONS, 
    STORAGE_CREDENTIALS, 
    WriteCatalogItemTxn,
    DeleteCatalogItemTxn,
    mv_catalog_item
)
from typing import Dict, Tuple, Any, Optional
from deltalake import DeltaTable
import fsspec
from urllib.parse import parse_qsl

def _parse_path(path: str) -> Tuple[str, Dict[str, str]]:
    if "?" in path:
        name, query = path.split("?", 1)
        tags = dict(parse_qsl(query))
    else:
        name = path
        tags = {}
    return name, tags

def read_delta(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    **polars_kwargs: Any,
) -> pl.DataFrame:
    """
    Load a materialised Polars DataFrame from the Flint catalog.
    If `path` is not provided, falls back to `name` and `tags`.

    Mirrors the signature of `polars.read_delta`.
    """
    if path:
        name, tags = _parse_path(path)

    polars_kwargs["storage_options"] = POLARS_STORAGE_OPTIONS

    catalog_item = get_catalog_item(
        item_type=CatalogItemType.TABLE,
        name=name,
        tags=tags
    )

    return pl.read_delta(
        catalog_item.uri,
        **polars_kwargs
    )

def scan_delta(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    **polars_kwargs: Any,
) -> pl.LazyFrame:
    """
    Lazy scan a Polars LazyFrame from the Flint catalog.
    If `path` is not provided, falls back to `name` and `tags`.

    Mirrors the signature of `polars.scan_delta`.
    """
    if path:
        name, tags = _parse_path(path)

    polars_kwargs["storage_options"] = POLARS_STORAGE_OPTIONS

    catalog_item = get_catalog_item(
        item_type=CatalogItemType.TABLE,
        name=name,
        tags=tags
    )

    return pl.scan_delta(
        catalog_item.uri,
        **polars_kwargs
    )

def write_delta(
    df: pl.DataFrame,
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    **polars_kwargs: Any,
) -> pl.LazyFrame:
    """
    Lazy scan a Polars LazyFrame from the Flint catalog.
    If `path` is not provided, falls back to `name` and `tags`.

    Mirrors the signature of `polars.DataFrame.write_delta`.
    """
    if path:
        name, tags = _parse_path(path)

    polars_kwargs["storage_options"] = POLARS_STORAGE_OPTIONS

    with WriteCatalogItemTxn(
        item_type=CatalogItemType.TABLE,
        name=name,
        tags=tags,
    ) as physical_uri:
        return df.write_delta(physical_uri, **polars_kwargs)

def open_delta(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    **deltalake_kwargs: Any,
) -> DeltaTable:
    """
    Resolve a logical table to a DeltaTable for management operations.
    If `path` is not provided, falls back to `name` and `tags`.

    Mirrors the signature of `deltalake.DeltaTable`.
    """
    if path:
        name, tags = _parse_path(path)

    catalog_item = get_catalog_item(
        item_type=CatalogItemType.TABLE,
        name=name,
        tags=tags
    )

    return DeltaTable(
        catalog_item.uri, 
        storage_options=DELTALAKE_STORAGE_OPTIONS,
        **deltalake_kwargs
    )

def drop_delta(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Delete a Delta table's data and remove its catalog entry.
    If `path` is not provided, falls back to `name` and `tags`.
    """
    if path:
        name, tags = _parse_path(path)

    with DeleteCatalogItemTxn(
        item_type=CatalogItemType.TABLE,
        name=name,
        tags=tags,
    ) as physical_uri:
        fs = fsspec.filesystem("s3", **STORAGE_CREDENTIALS)
        fs.rm(physical_uri, recursive=True)

def move_delta(
    old_name: str,
    old_tags: Dict[str, str],
    new_name: str,
    new_tags: Dict[str, str],
) -> None:
    """
    Moves a Delta table's logical location by updating its name and tags.
    """
    mv_catalog_item(
        CatalogItemType.TABLE, 
        old_name,
        old_tags,
        new_name,
        new_tags
    )
