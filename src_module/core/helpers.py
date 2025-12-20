import random
import time
import uuid
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
from pyspark.sql import functions as F
from src_module.schemas import (
    JOB_STATUS_SCHEMA,
)


class BaseRunner:
    def __init__(self, catalog, environment, create_schemas=False):

        self.catalog = catalog
        self.environment = environment
        self.spark = SparkSession.builder.getOrCreate()
        self.job_status_table = f"{self.catalog}.bronze.job_processing_status"
        self.worker_id = str(uuid.uuid4())

        if create_schemas:
            self.init_schemas()

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

        print("job entries:", job_entries)
        df = self.spark.createDataFrame(job_entries, schema=JOB_STATUS_SCHEMA)

        df = (
            df.withColumn("last_run_start_time", lit(None).cast("timestamp"))
            .withColumn("last_run_end_time", lit(None).cast("timestamp"))
            .withColumn("worker_id", lit(None).cast("string"))
            .withColumn("error_message", lit(None).cast("string"))
            .withColumn("updated_at", current_timestamp())
            .withColumn("ETLInsertTime", current_timestamp())
        )
        df.write.format("delta").mode("append").saveAsTable(self.job_status_table)

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

    def get_next_pending_job(self, job_name: str, source_system: str) -> dict | None:
        """
        Atomically claims one pending job by stamping worker_id with self.worker_id.
        Returns the claimed job as a dict, or None if no job is available.

        Assumptions:
        - worker_id is a stable identifier for this worker
        - id is unique
        - Delta table
        """

        table = self.job_status_table
        max_attempts = 5
        sleep_seconds = 1

        for attempt in range(max_attempts):
            try:
                # 1) Select ONE candidate job id (read-only)
                candidate = (
                    self.spark.table(table)
                    .where(
                        (F.col("status") == "pending")
                        & (F.col("job_name") == job_name)
                        & (F.col("source_system") == source_system)
                    )
                    .select("id", "company_id", "company_name", "source_system_key_id")
                    .limit(1)
                    .collect()
                )

                # No jobs left → exit immediately
                if not candidate:
                    return None

                job_id = candidate[0]["id"]

                # 2) Try to claim THAT EXACT job id (atomic condition)
                self.spark.sql(
                    f"""
                    UPDATE {table}
                    SET
                        status = 'processing',
                        worker_id = '{self.worker_id}',
                        last_run_start_time = current_timestamp(),
                        updated_at = current_timestamp()
                    WHERE id = '{job_id}'
                    AND status = 'pending'
                """
                )

                # 3) Check if successfully claimed it
                claimed = (
                    self.spark.table(table)
                    .where(
                        (F.col("id") == job_id)
                        & (F.col("worker_id") == self.worker_id)
                        & (F.col("status") == "processing")
                    )
                    .limit(1)
                    .collect()
                )

                if claimed:
                    return claimed[0].asDict()

                # Someone else claimed it first → backoff and retry
                time.sleep(sleep_seconds)

            except Exception as e:  # pylint:disable=broad-exception-caught
                print(f"Error claiming job (attempt {attempt + 1}/{max_attempts}): {e}")
                self.random_sleep(sleep_seconds, 10)

        # Give up after bounded retries
        return None

    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: str = None,
        start_time: bool = False,
        end_time: bool = False,
    ):
        print("updating", job_id, status)
        try:
            table_name = self.job_status_table
            update_parts = []
            update_parts.append(f"status = '{status}'")
            update_parts.append("updated_at = current_timestamp()")
            update_parts.append(f"worker_id = '{self.worker_id}'")

            if error_message is not None:
                # Escape single quotes to avoid SQL errors
                safe_error = error_message.replace("'", "''")
                update_parts.append(f"error_message = '{safe_error}'")

            if start_time:
                update_parts.append("last_run_start_time = current_timestamp()")

            if end_time:
                update_parts.append("last_run_end_time = current_timestamp()")

            update_sql = ", ".join(update_parts)

            query = f"""
                UPDATE {table_name}
                SET {update_sql}
                WHERE id = '{job_id}'
            """

            self.spark.sql(query)
            return True

        except Exception as e:  # pylint:disable=broad-exception-caught
            print("failed to update job status", str(e))
            return False

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
            ],
            "silver": [],
        }
