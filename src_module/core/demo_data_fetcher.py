from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pyspark.sql.functions import current_timestamp
from src_module.core.helpers import BaseRunner
from src_module.core.source_jobs import DEMO_SOURCE_JOBS
from src_module.schemas import SOME_SCHEMA

test_organisations = [
    {
        "id": "123",
        "name": "Testi Oy",
        "source_system": "somesource",
    }
]


class DemoDataFetcher(BaseRunner):
    def __init__(self, catalog, environment, create_schemas=False):
        super().__init__(catalog, environment, create_schemas=create_schemas)

    def run_job(self, job_name: str, job: dict):

        match job_name:
            case "init_jobs":
                self.init_jobs_for_organisations(
                    DEMO_SOURCE_JOBS, test_organisations, []
                )

            case "handle_dequeue":
                print("dequeue handle")
                self.handle_dequeue("job-queue-1", 1, 50)

            case "dippadai_jobs":
                self.run_dippadai_jobs(job_name, job)

            case "dappadai_jobs":
                self.run_dappadai_jobs(job_name, job)

            case _:
                raise ValueError(f"Unknown job name: {job_name}")

    def run_dippadai_jobs(self, job_name: str, job):
        print("Running DIPPADAI jobs...", job_name, job)
        self.do_writing(job)

    def run_dappadai_jobs(self, job_name: str, job: str):
        print("Running DAPPADAI jobs...", job_name, job)
        self.do_writing(job)

    def handle_dequeue(self, queue_name, workers, max_messages):
        max_workers = workers

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for queue_client, message in self.dequeue_messages(
                queue_name, max_messages
            ):
                job = json.loads(message.content)

                future = executor.submit(
                    self._run_and_delete,
                    queue_client,
                    message,
                    job,
                )
                futures.append(future)

            for future in as_completed(futures):
                future.result()

    def do_writing(self, job):
        """
        Some nonsense write task for testing.
        """
        target_table = f"{self.catalog}.bronze.some_table"

        df = self.spark.createDataFrame([job], schema=SOME_SCHEMA)
        df = df.withColumn("ETLInsertTime", current_timestamp())
        (df.write.format("delta").mode("append").saveAsTable(target_table))
