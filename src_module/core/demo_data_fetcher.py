from src_module.core.helpers import BaseRunner
from src_module.core.source_jobs import DEMO_SOURCE_JOBS

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

    def run_job(self, job_name: str, source_system=None):

        match job_name:
            case "init_jobs":
                self.init_jobs_for_organisations(
                    DEMO_SOURCE_JOBS, test_organisations, []
                )

            case "dippadai_jobs":
                self.run_dippadai_jobs(job_name, source_system)

            case "dappadai_jobs":
                self.run_dappadai_jobs(job_name, source_system)

            case _:
                raise ValueError(f"Unknown job name: {job_name}")

    def run_dippadai_jobs(self, job_name: str, source_system: str):
        print("Running DIPPADAI jobs...", job_name, source_system)
        for _ in range(10):
            job = self.get_next_pending_job(job_name, source_system)

            if job is None:
                break

            organization_id = job["company_id"]
            organization_name = job["company_name"]
            source_system_key_id = job["source_system_key_id"]
            print(
                "DIPPA job data check: ",
                organization_id,
                organization_name,
                source_system_key_id,
            )
            # do stuff

            self.update_job_status(job["id"], "completed")

    def run_dappadai_jobs(self, job_name: str, source_system: str):
        print("Running DAPPADAI jobs...", job_name, source_system)

        for _ in range(10):
            job = self.get_next_pending_job(job_name, source_system)

            if job is None:
                break

            organization_id = job["company_id"]
            organization_name = job["company_name"]
            source_system_key_id = job["source_system_key_id"]
            print(
                "DAPPA job data check: ",
                organization_id,
                organization_name,
                source_system_key_id,
            )
            # do stuff

            self.update_job_status(job["id"], "completed")
