# Reference

The following reference is for the public symbols exposed by the `flint` Python package (which is pre‑installed).

---

## `flint.new_run`

```python
def new_run(*args, **kwargs) -> Run:
    """Creates an Aim Run at default repository location."""
```

**Example**

```python
from flint import new_run

# Start a new experiment run and log a metric
with new_run(experiment="mnist-classifier") as run:
    for epoch, acc in enumerate([0.88, 0.92, 0.95]):
        run.track_metric("accuracy", acc, step=epoch)
```

---

## `flint.log_artifact`

```python
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
```

**Example**

```python
from flint import new_run, log_artifact

with new_run(experiment="audio-demo") as run:
    # Save an in‑memory bytes buffer as an artifact
    wav_bytes = b"RIFF...WAVEfmt...data..."  # e.g. a short synthesized tone
    log_artifact(run, wav_bytes, name="tone.wav", tags={"type": "audio"})
```

---

## `flint.display`

```python
def display(df: pl.DataFrame | pl.LazyFrame):
    """
    Displays a Polars df or lf inline with notebook.
    """
```

**Example**

```python
import polars as pl
from flint import display

df = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
# Shows a rich, interactive preview
display(df)
```

---

## `flint.read_delta`

```python
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
```

**Example**

```python
import polars as pl
from flint import read_delta

# Retrieve the latest version of a feature table by logical name & tags
features = read_delta(name="user_features", tags={"v": "2025‑06‑01"})
```

---

## `flint.scan_delta`

```python
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
```

**Example**

```python
from flint import scan_delta

# Build a lazy query that joins two logical tables, then collect synchronously
transactions = scan_delta(name="tx", tags={"v": "prod"})
users = scan_delta(name="users", tags={"v": "prod"})

report = (
    transactions
    .join(users, on="user_id")
    .group_by("country")
    .agg([pl.col("amount").sum().alias("total_spent")])
    .collect()
)
```

---

## `flint.write_delta`

```python
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
```

**Example**

```python
import polars as pl
from flint import write_delta

df = pl.DataFrame({"id": [1, 2, 3], "score": [98, 82, 91]})

# Store the DataFrame in the Flint Catalog
write_delta(df, name="exam_scores", tags={"subject": "math", "year": "2025"})
```

---

## `flint.open_delta`

```python
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
```

**Example**

```python
from flint import open_delta

dt = open_delta(name="exam_scores", tags={"subject": "math", "year": "2025"})
print("Current version:", dt.version())
```

---

## `flint.drop_delta`

```python
def drop_delta(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Delete a Delta table's data and remove its catalog entry.
    If `path` is not provided, falls back to `name` and `tags`.
    """
```

**Example**

```python
from flint import drop_delta

drop_delta(name="temporary_dataset", tags={"tmp": "yes"})
```

---

## `flint.move_delta`

```python
def move_delta(
    old_name: str,
    old_tags: Dict[str, str],
    new_name: str,
    new_tags: Dict[str, str],
) -> None:
    """
    Moves a Delta table's logical location by updating its name and tags.
    """
```

**Example**

```python
from flint import move_delta

move_delta(
    old_name="exam_scores",
    old_tags={"subject": "math", "year": "2025"},
    new_name="exam_scores_archive",
    new_tags={"subject": "math", "year": "2025", "archived": "true"},
)
```

---

## `flint.open_object`

```python
def open_object(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    mode: str = "rb",
    **fs_open_kwargs: Any,
) -> BinaryIO:
    """
    Open an object in a transaction‑aware way.
    If `path` is not provided, falls back to `name` and `tags`.

    Modes:
      - "rb" → read existing object.
      - "wb" → create or overwrite.
      - "ab" → append to existing.

    Returns
    -------
    BinaryIO
      A file‑like handle. On write/append, updates the Flint catalog.
    """
```

**Example**

```python
from flint import open_object

# Write bytes to a new object
with open_object(name="logo.png", tags={"project": "brand"}, mode="wb") as f:
    f.write(b"\x89PNG...")

# Read them back later
with open_object(name="logo.png", tags={"project": "brand"}, mode="rb") as f:
    logo_bytes = f.read()
```

---

## `flint.delete_object`

```python
def delete_object(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Delete an object's bytes and remove it from the Flint catalog.
    If `path` is not provided, falls back to `name` and `tags`.
    """
```

**Example**

```python
from flint import delete_object

delete_object(name="logo.png", tags={"project": "brand"})
```

---

## `flint.move_object`

```python
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
```

**Example**

```python
from flint import move_object

move_object(
    old_name="logo.png",
    old_tags={"project": "brand"},
    new_name="logo.png",
    new_tags={"project": "brand", "version": "v2"},
)
```

---

## `flint.exists_object`

```python
def exists_object(
    path: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Return True if an object with this name and exact tags exists in the
    Flint catalog. If `path` is not provided, falls back to `name` and `tags`.
    """
```

**Example**

```python
from flint import exists_object

if exists_object(name="logo.png", tags={"project": "brand", "version": "v2"}):
    print("Found the updated logo!")
```

---

## `flint.search_objects`

```python
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
      Only return objects whose tags contain all key‑value pairs here.
    created_at_lower, created_at_upper
      UNIX timestamps to filter on creation time.
    updated_at_lower, updated_at_upper
      UNIX timestamps to filter on last update time.

    Returns
    -------
    List of metadata dicts (each with keys: uri, name, tags, created_at, updated_at).
    """
```

**Example**

```python
from flint import search_objects

recent_models = search_objects(
    tag_filter={"category": "model"},
    created_at_lower=1654041600,  # e.g. 1 June 2022
)

for obj in recent_models:
    print(obj["name"], obj["tags"], obj["created_at"], obj["uri"])
```

