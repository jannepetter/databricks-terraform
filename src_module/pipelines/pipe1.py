from src_module.core.helpers import CatalogTool
import argparse


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args(argv)
    print(f"Pipe1 running with catalog: {args.catalog}")

    pipeline = CatalogTool(args.catalog)
    pipeline.create_schemas()

    df = pipeline.create_demo_dataframe()
    pipeline.write(df, "bronze", "users")

    df = pipeline.read("bronze", "users")
    df.show(10, truncate=False)
