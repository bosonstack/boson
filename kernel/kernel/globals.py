import os
import polars as pl
from perspective.widget import PerspectiveWidget
from aim import Run
import boto3

def write_delta(df: pl.DataFrame, table_name: str, *args, **kwargs):
    """
    Save a Polars DataFrame to a Delta Lake table in blob storage.
    """
    s3_uri = f"s3://metastore/delta/{table_name}"

    storage_options = {
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": os.environ.get("STORAGE_USER"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("STORAGE_PASSWORD"),
        "AWS_ALLOW_HTTP": "true",
        "AWS_ENDPOINT_URL": f"http://storage:{os.environ.get("STORAGE_PORT")}"
    }

    # Force storage_options + target, pass everything else through
    kwargs["storage_options"] = storage_options

    df.write_delta(s3_uri, *args, **kwargs)

def read_delta(table_name: str, *args, **kwargs) -> pl.DataFrame:
    """
    Read a Delta Lake table from blob storage via Polars.
    """
    s3_uri = f"s3://metastore/delta/{table_name}"

    storage_options = {
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": os.environ.get("STORAGE_USER"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("STORAGE_PASSWORD"),
        "AWS_ALLOW_HTTP": "true",
        "AWS_ENDPOINT_URL": f"http://storage:{os.environ.get("STORAGE_PORT")}"
    }

    kwargs["storage_options"] = storage_options

    df = pl.read_delta(s3_uri, *args, **kwargs)
    return df

def scan_delta(table_name: str, *args, **kwargs) -> pl.LazyFrame:
    """
    Lazily scan a Delta Lake table from blob storage via Polars.
    """
    s3_uri = f"s3://metastore/delta/{table_name}"

    storage_options = {
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": os.environ.get("STORAGE_USER"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("STORAGE_PASSWORD"),
        "AWS_ALLOW_HTTP": "true",
        "AWS_ENDPOINT_URL": f"http://storage:{os.environ.get("STORAGE_PORT")}"
    }

    kwargs["storage_options"] = storage_options

    lf = pl.scan_delta(s3_uri, *args, **kwargs)
    return lf

def drop_delta(table_name: str):
    """
    Drop (delete) a Delta Lake table from cloud storage by removing all underlying files.
    """
    bucket = "metastore"
    prefix = f"delta/{table_name}"

    access_key = os.environ.get("STORAGE_USER")
    secret_key = os.environ.get("STORAGE_PASSWORD")
    endpoint_url = f"http://storage:{os.environ.get('STORAGE_PORT')}"

    # Initialize S3 client
    s3 = boto3.resource(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    bucket_obj = s3.Bucket(bucket)

    deleted = bucket_obj.objects.filter(Prefix=prefix).delete()
    return deleted

def display(df: pl.DataFrame | pl.LazyFrame):
    """
    Displays a Polars df or lf inline with notebook.
    """
    return PerspectiveWidget(
        df,
        plugin="Datagrid",
        theme="Monokai"
    )

def new_run(*args, **kwargs) -> Run:
    """Creates an Aim Run at default repository location."""
    
    return Run(repo="/aim-repo", *args, **kwargs)

import builtins
builtins.write_delta = write_delta
builtins.read_delta = read_delta
builtins.scan_delta = scan_delta
builtins.drop_delta = drop_delta
builtins.display = display
builtins.new_run = new_run