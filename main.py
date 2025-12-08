import os
from databricks.sdk import WorkspaceClient
from azure.identity import (
    DefaultAzureCredential,
)
from databricks import sql
import duckdb
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("DATABRICKS_HOST")
PAT_TOKEN = os.getenv("PAT_TOKEN")
HOST_ENDPOINT = os.getenv("HOST_ENDPOINT")

print("do stuff?")
