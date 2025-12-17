import random
import time
import uuid
from pyspark.sql.functions import current_timestamp, lit
from pyspark.sql import functions as F
from pyspark.sql import SparkSession
from src_module.schemas.job_processing_status import JOB_STATUS_SCHEMA


class BaseRunner:
    def __init__(self, catalog, environment, create_schemas=False):

        self.catalog = catalog
        self.environment = environment
        self.spark = SparkSession.builder.getOrCreate()
        self.job_status_table = f"{self.catalog}.bronze.job_processing_status"
        self.worker_id = str(uuid.uuid4())

        if create_schemas:
            self.create_schemas(["bronze", "silver"])
            self._create_job_data_schema()

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
                        "job_name": job["job_name"],
                        "company_name": organisation["name"],
                        "company_id": organisation["id"],
                        "source_system": source_system,
                        "source_system_key_id": job["source_system_key_id"],
                    }
                    job_entries.append(job_entry)

        print("job entries--:", job_entries)
        df = self.spark.createDataFrame(job_entries)

        df = (
            df.withColumn("status", lit("pending"))
            .withColumn("last_run_start_time", lit(None).cast("timestamp"))
            .withColumn("last_run_end_time", lit(None).cast("timestamp"))
            .withColumn("worker_id", lit(None).cast("string"))
            .withColumn("error_message", lit(None).cast("string"))
            .withColumn("id", F.expr("uuid()"))
            .withColumn("updated_at", current_timestamp())
            .withColumn("ETLInsertTime", current_timestamp())
        )
        df.write.format("delta").mode("append").saveAsTable(self.job_status_table)

    def create_schemas(self, schema_list: list):
        """
        Create schemas under the selected catalog.
        """
        for schema in schema_list:
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema}")

    def _create_job_data_schema(self):
        """
        Create job processing status table if it does not exist.
        """
        self.spark.createDataFrame([], JOB_STATUS_SCHEMA).write.format("delta").mode(
            "ignore"
        ).saveAsTable(self.job_status_table)
        print(f"Job status table ready at {self.job_status_table}")

    def drop_job_data_schema(self):
        """
        Drop job processing status table.
        """
        self.spark.sql(f"DROP TABLE IF EXISTS {self.job_status_table}")
        print(f"Dropped table {self.job_status_table}")

    def get_next_pending_job(
        self,
        job_name: str,
        source_system: str,
    ) -> dict | None:
        """
        Atomically claim the next pending job.
        Returns None if no jobs are available.
        Retries on contention or transient errors.
        """

        table = self.job_status_table

        while True:
            try:
                # 1. Atomically claim ONE job
                self.spark.sql(
                    f"""
                    UPDATE {table}
                    SET
                        status = 'processing',
                        worker_id = '{self.worker_id}',
                        last_run_start_time = current_timestamp(),
                        updated_at = current_timestamp()
                    WHERE id IN (
                        SELECT id
                        FROM {table}
                        WHERE status = 'pending'
                        AND job_name = '{job_name}'
                        AND source_system = '{source_system}'
                        ORDER BY updated_at
                        LIMIT 1
                    )
                    AND status = 'pending'
                """
                )

                # 2. Read the job we just claimed
                claimed = self.spark.sql(
                    f"""
                    SELECT *
                    FROM {table}
                    WHERE worker_id = '{self.worker_id}'
                    AND status = 'processing'
                    ORDER BY updated_at DESC
                    LIMIT 1
                """
                ).collect()

                if not claimed:
                    return None

                return claimed[0].asDict()

            except Exception as e:  # pylint:disable=broad-exception-caught
                print(f"Error claiming job: {e}, retrying...")
                self.random_sleep(2, 10)

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
