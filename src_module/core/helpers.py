import random
import time
import uuid
import json
from pyspark.sql import SparkSession
from pyspark.dbutils import DBUtils
from src_module.schemas import JOB_STATUS_SCHEMA, SOME_SCHEMA
from azure.storage.queue import QueueClient
from azure.identity import (
    DefaultAzureCredential,
)


class BaseRunner:
    def __init__(self, catalog, environment, create_schemas=False):

        self.catalog = catalog
        self.environment = environment
        self.spark = SparkSession.builder.getOrCreate()
        self.job_status_table = f"{self.catalog}.bronze.job_processing_status"
        self.worker_id = str(uuid.uuid4())
        self.storage_account_name = f"stagedemo{environment}1234"
        self.secret_scope = "my-scope"
        self.sas_token = None
        self.credentials = None

        if create_schemas:
            self.init_schemas()

    def _run_and_delete(self, queue_client: QueueClient, message: dict, job: dict):
        self.run_job(job["job_name"], job)

        try:
            queue_client.delete_message(message)
        except Exception as e:  # pylint:disable=broad-except
            print("deleting message failed:", e)

    def run_job(self, job_name: str, job: dict):
        pass

    def add_jobs_to_queue(self, job_list: list, queue_name: str):

        # dbutils = DBUtils(self.spark)

        # sas_token = dbutils.secrets.get(self.secret_scope, "que-sas-token")
        self.credentials = DefaultAzureCredential()
        queue_client = QueueClient(
            account_url=f"https://{self.storage_account_name}.queue.core.windows.net",
            queue_name=queue_name,
            credential=self.credentials,
        )

        # clear old if any, from failed
        for _ in range(20000):
            msg = queue_client.receive_message(visibility_timeout=30)

            if msg is None:
                break

            queue_client.delete_message(msg)

        for job in job_list:
            queue_client.send_message(json.dumps(job))

        print(f"messages sent to {queue_name}")

    def dequeue_messages(self, queue_name, max_messages=2000, visibility_timeout=900):

        if not self.credentials:
            # dbutils = DBUtils(self.spark)
            # sas_token = dbutils.secrets.get(self.secret_scope, "que-sas-token")
            # self.sas_token = sas_token
            self.credentials = DefaultAzureCredential()

        queue_client = QueueClient(
            account_url=f"https://{self.storage_account_name}.queue.core.windows.net",
            queue_name=queue_name,
            credential=self.credentials,
        )

        for _ in range(max_messages):
            message = queue_client.receive_message(
                visibility_timeout=visibility_timeout
            )

            if message is None:
                break

            yield queue_client, message

    def init_jobs_for_organisations(
        self, source_jobs: dict, organisations: list, skip_jobs: list
    ):
        job_entries = []

        for organisation in organisations:
            source_system = organisation["source_system"]
            jobs_to_init = source_jobs.get(source_system, [])
            print("jobs--", jobs_to_init)

            for job in jobs_to_init:
                if job["job_name"] not in skip_jobs:
                    job_entry = {
                        "id": str(uuid.uuid4()),
                        "status": "pending",
                        "job_name": job["job_name"],
                        "company_name": organisation["name"],
                        "company_id": organisation["id"],
                        "source_system": source_system,
                        "source_system_key_id": job["source_system_key_id"],
                    }
                    job_entries.append(job_entry)

        return job_entries

    def init_schemas(self):
        """
        Init schemas under the selected catalog.
        """

        structures = self.get_schema_structure()
        for schema, tables in structures.items():
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema}")
            for table_name, table_schema in tables:
                self.spark.createDataFrame([], table_schema).write.format("delta").mode(
                    "ignore"
                ).saveAsTable(f"{self.catalog}.{schema}.{table_name}")
                print(f"Created/checked table {self.catalog}.{schema}.{table_name}")

    def run_migration(self, migration):

        self.spark.sql(migration)
        print("Ran migration:", migration)

    def drop_table(self, schema: str, table_name: str):
        """
        Drop job processing status table.
        """
        table_to_drop = f"{self.catalog}.{schema}.{table_name}"
        self.spark.sql(f"DROP TABLE IF EXISTS {table_to_drop}")
        print(f"Dropped table {table_to_drop}")

    def random_sleep(self, min_val: int, max_val: int):
        """
        Sleep for a random time between min and max seconds
        """

        sleep_time = random.randint(min_val, max_val)
        print(f"Sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)

    def get_schema_structure(self) -> dict:
        return {
            "bronze": [
                ("job_processing_status", JOB_STATUS_SCHEMA),
                ("some_table", SOME_SCHEMA),
            ],
            "silver": [],
        }
