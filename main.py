import os
from databricks.sdk import WorkspaceClient
from azure.identity import (
    DefaultAzureCredential,
)
from databricks import sql
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("DATABRICKS_HOST")
PAT_TOKEN = os.getenv("PAT_TOKEN")


def run_stuff():
    print("running stuff")
    # credential = DefaultAzureCredential()
    # token = credential.get_token(
    # )

    w = WorkspaceClient(token=PAT_TOKEN, host=HOST)
    # print("kata--", w.current_user.me())
    # for c in w.clusters.list():
    #     print(c.cluster_name)

    # query_id = w.sql.execute("SELECT COUNT(*) FROM table")
    # result = w.sql.get_results(query_id)
    # print("res--", lista)


run_stuff()
