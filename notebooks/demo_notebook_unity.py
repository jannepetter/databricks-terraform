# Databricks notebook source
# MAGIC %md
# MAGIC # Demo Delta Tables (Unity Catalog Managed Tables Version)
# MAGIC This notebook:
# MAGIC - Creates UC catalog `demo` if you have permissions
# MAGIC - Creates schemas `bronze` and `silver`
# MAGIC - Writes UC-managed Delta tables using the 3-level namespace:
# MAGIC
# MAGIC   `default.bronze.users`
# MAGIC   `default.silver.users`
# MAGIC
# MAGIC Fully UC-compliant and serverless-ready.

# COMMAND ----------
# MAGIC %md
# MAGIC ## 0️⃣ Ensure Catalog & Schemas Exist

# COMMAND ----------
# Create schemas under the default catalog
from pyspark.sql import SparkSession

CATALOG_NAME = "devjoo"
spark = SparkSession.builder.getOrCreate()
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.bronze")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.silver")

print("Schemas 'bronze' and 'silver' are ready.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1️⃣ Create Demo Data

# COMMAND ----------
import pandas as pd

customer_data = [
    (1, "Alice", "2025-01-01", 100.0),
    (2, "Bob", "2025-01-05", 150.5),
    (3, "Charlie", "2025-01-10", 200.75),
]

columns = ["customer_id", "name", "signup_date", "spend"]

pdf = pd.DataFrame(customer_data, columns=columns)
df = spark.createDataFrame(pdf)

df.show(truncate=False)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2️⃣ Write Bronze Table (demo.bronze.users)

# COMMAND ----------
df.write.format("delta").mode("overwrite").saveAsTable(f"{CATALOG_NAME}.bronze.users")

print(f"✅ Bronze table created: {CATALOG_NAME}.bronze.users")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3️⃣ Read Bronze Table

# COMMAND ----------
df_bronze = spark.table(f"{CATALOG_NAME}.bronze.users")
df_bronze.show(truncate=False)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4️⃣ Transform Silver Table (demo.silver.users)

# COMMAND ----------
from pyspark.sql.functions import col

df_silver = df_bronze.withColumn("status", col("spend") > 120.0)
df_silver.write.format("delta").mode("overwrite").saveAsTable(
    f"{CATALOG_NAME}.silver.users"
)

print(f"✅ Silver table created: {CATALOG_NAME}.silver.users")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5️⃣ Read Silver Table

# COMMAND ----------
df_silver_read = spark.table(f"{CATALOG_NAME}.silver.users")
df_silver_read.show(truncate=False)
