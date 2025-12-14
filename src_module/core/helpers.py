from pyspark.sql import SparkSession

# from pyspark.sql.functions import col
import pandas as pd


class CatalogTool:
    def __init__(self, catalog_name="main"):
        """
        Create a helper for working with Unity Catalog managed tables.
        """
        self.catalog = catalog_name
        self.spark = SparkSession.builder.getOrCreate()

    def create_schemas(self, schema_list=["bronze", "silver"]):
        """
        Create schemas under the selected catalog.
        """
        for schema in schema_list:
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema}")

        print(f"Schemas under {self.catalog} are ready.")

    def create_demo_dataframe(self):
        """
        Create sample demo dataframe.
        """
        customer_data = [
            (1, "Alice", "2025-01-01", 100.0),
            (2, "Bob", "2025-01-05", 150.5),
            (3, "Charlie", "2025-01-10", 200.75),
        ]
        columns = ["customer_id", "name", "signup_date", "spend"]

        pdf = pd.DataFrame(customer_data, columns=columns)
        return self.spark.createDataFrame(pdf)

    def write(self, df, schema_name: str, table_name: str, mode: str = "overwrite"):
        """
        Write dataframe to the bronze layer.
        """
        full_name = f"{self.catalog}.{schema_name}.{table_name}"
        df.write.format("delta").mode(mode).saveAsTable(full_name)
        print(f"Df written to: {full_name}")
        return full_name

    def read(self, schema_name: str, table_name: str):
        """
        Load bronze table.
        """
        full_name = f"{self.catalog}.{schema_name}.{table_name}"
        df = self.spark.table(full_name)
        print(f"Loaded {full_name}")
        return df
