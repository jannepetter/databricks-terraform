from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import pandas as pd


class DemoDeltaUC:
    def __init__(self, catalog_name="main"):
        """
        Create a helper for working with Unity Catalog managed tables.
        """
        self.catalog = catalog_name
        self.spark = SparkSession.builder.getOrCreate()

    # -------------------------
    #  Schema setup
    # -------------------------

    def create_schemas(self):
        """
        Create bronze/silver schemas under the selected catalog.
        """
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.bronze")
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.silver")
        print(f"Schemas {self.catalog}.bronze and {self.catalog}.silver are ready.")

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

    def write_bronze(self, df, table_name="users2"):
        """
        Write dataframe to the bronze layer.
        """
        full_name = f"{self.catalog}.bronze.{table_name}"
        df.write.format("delta").mode("overwrite").saveAsTable(full_name)
        print(f"Bronze table created: {full_name}")
        return full_name

    def read_bronze(self, table_name="users2"):
        """
        Load bronze table.
        """
        full_name = f"{self.catalog}.bronze.{table_name}"
        df = self.spark.table(full_name)
        print(f"Loaded {full_name}")
        return df

    def write_silver(self, df, table_name="users2"):
        """
        Transform bronze → silver.
        Adds status column.
        """
        df_silver = df.withColumn("status", col("spend") > 120.0)
        full_name = f"{self.catalog}.silver.{table_name}"
        df_silver.write.format("delta").mode("overwrite").saveAsTable(full_name)
        print(f"Silver table created: {full_name}")
        return full_name

    def read_silver(self, table_name="users2"):
        """
        Load silver table.
        """
        full_name = f"{self.catalog}.silver.{table_name}"
        df = self.spark.table(full_name)
        print(f"Loaded {full_name}")
        return df

    # -------------------------
    #  One-shot pipeline
    # -------------------------

    def run_demo_pipeline(self):
        """
        Convenience method to run the full
        bronze → silver pipeline.
        """
        print("Running full UC demo pipeline...")

        self.create_schemas()

        df = self.create_demo_dataframe()
        bronze_table = self.write_bronze(df)
        bronze_df = self.read_bronze()

        silver_table = self.write_silver(bronze_df)
        silver_df = self.read_silver()

        print("Pipeline completed.")
        return bronze_table, silver_table
