from aim import Run
import os
from urllib.parse import urlparse, urlunparse
from typing import Optional, Dict, Any
from aim import Text

from .catalog import parse_item_path, build_item_path
from .fs import open_object

EXPERIMENT_ENDPOINT = os.getenv("EXPERIMENT_ENDPOINT")

def new_run(*args, **kwargs) -> Run:
    """Creates an Aim Run at default repository location."""

    parsed_endpoint = urlparse(EXPERIMENT_ENDPOINT)
    endpoint_no_scheme = urlunparse(('',) + parsed_endpoint[1:])
    
    return Run(repo=f"aim:{endpoint_no_scheme}", *args, **kwargs)

def log_artifact(
    run: Run,
    data: bytes,
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    **aim_kwargs
) -> None:
    """
    Logs an arbitrary artifact into the Flint catalog as an object and tracks 
    its reference in Aim as `aim.Text`. If `path` is not provided, falls back 
    to `name` and `tags`.
    """
    if path:
        name, tags = parse_item_path(path)

    tags = {**tags, "run_id": run.name.split(" ")[-1]}

    with open_object(name=name, tags=tags, mode="wb") as fp:
        fp.write(data)

    new_path = build_item_path(name, tags)

    run.track(
        Text(new_path),
        name="flint-artifact-reference",
        **aim_kwargs
    )