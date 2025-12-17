import argparse
from src_module.core.demo_data_fetcher import DemoDataFetcher


def run(argv=None):
    """
    catalog: base catalog name
    environment: dev/test/prod
    task_name: name of the task to run

    Environment for skipping some events in test and dev environments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--task_name", required=True)
    parser.add_argument("--source", required=False, default="somesource")

    args = parser.parse_args(argv)

    catalog = args.catalog
    environment = args.environment
    task_name = args.task_name
    source = args.source

    print(f"Pipe1 running with catalog: {catalog} {environment} {task_name}")
    fetcher = DemoDataFetcher(catalog, environment, create_schemas=True)

    fetcher.run_job(task_name, source)
