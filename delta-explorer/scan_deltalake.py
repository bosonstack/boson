from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import os
from deltalake import DeltaTable
from dotenv import load_dotenv
import boto3
from botocore.config import Config

@dataclass
class DeltaTableInfo:
    name: str
    path: str
    schema: Dict[str, str]
    created_time: Optional[datetime]
    last_updated_time: Optional[datetime]
    latest_version: int

@dataclass
class DeltaLake:
    delta_tables: List[DeltaTableInfo]

def scan_deltalake() -> DeltaLake:
    bucket = "metastore"
    delta_prefix = f"delta/"
    endpoint_url = f"http://storage:{os.environ.get("STORAGE_PORT")}"
    storage_key =  os.environ.get("STORAGE_USER")
    storage_password = os.environ.get("STORAGE_PASSWORD")

    storage_options = {
        "AWS_ACCESS_KEY_ID": storage_key,
        "AWS_SECRET_ACCESS_KEY": storage_password,
        "AWS_ENDPOINT_URL": endpoint_url,
        "AWS_REGION": "us-east-1",
        "AWS_ALLOW_HTTP": "true",
    }

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=storage_key,
        aws_secret_access_key=storage_password,
        config=Config(signature_version="s3v4"),
    )

    tables = []
    paginator = s3.get_paginator("list_objects_v2")
    result = paginator.paginate(Bucket=bucket, Prefix=delta_prefix, Delimiter="/")

    for page in result:
        for prefix in page.get("CommonPrefixes", []):
            table_name = prefix["Prefix"].replace(delta_prefix, "").strip("/")
            s3_path = f"s3://{bucket}/{delta_prefix}{table_name}"

            dt = DeltaTable(s3_path, storage_options=storage_options)
            metadata = dt.metadata()
            schema = {f.name: str(f.type) for f in dt.schema().fields}
            history = dt.history()
            latest_version = dt.version()

            last_updated_time = history[0].get("timestamp") if history else None

            table_info = DeltaTableInfo(
                name=table_name,
                path=s3_path,
                schema=schema,
                created_time=metadata.created_time,
                last_updated_time=last_updated_time,
                latest_version=latest_version,
            )
            tables.append(table_info)

    return DeltaLake(delta_tables=tables)