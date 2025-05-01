# Builtins

Boson simplifies usage by abstracting repetitive implemention details into convenient builtin functions. These functions are automatically installed in the Jupyter kernel and require no manual imports to be made available.

For the full reference, please see [globals.py](../kernel/kernel/globals.py)

### `write_delta(df: polars.DataFrame, table_name: str, *args, **kwargs)`

```python
write_delta(my_df, "my_table")
```

Save a Polars DataFrame to a Delta Table in blob storage.

### `read_delta(table_name: str, *args, **kwargs) -> polars.DataFrame`

```python
df = read_delta("my_table")
```

Read a Delta Table from blob storage via Polars.

### `scan_delta(table_name: str, *args, **kwargs) -> polars.LazyFrame`

```python
lf = scan_delta("my_table")
```

Lazily scan a Delta Table from blob storage via Polars.

### `drop_delta(table_name: str)`

```python
drop_delta("my_table")
```

Drop (delete) a Delta Table from cloud storage by removing all underlying files.

### `display(df: polars.DataFrame | polars.LazyFrame)`

```python
display(my_df)
```

Drop (delete) a Delta Table from cloud storage by removing all underlying files.

### `new_run(*args, **kwargs) -> Run`

```python
run = new_run()
```

Creates an Aim Run at the default repository location.