# Databricks notebook source
# MAGIC %md
# MAGIC # Simple Delta Table Notebook
# MAGIC This notebook demonstrates creating sample data and saving it to ADLS Gen2 as Delta tables.

# COMMAND ----------

# Import libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import pandas as pd
import os

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1️⃣ Initialize Spark
spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2️⃣ Configure Storage
# Replace these with your storage account, container, and folder
storage_account = "adlsdbdemo123"
container_name = "datalake"
bronze_path = f"abfss://{container_name}@{storage_account}.dfs.core.windows.net/bronze"
silver_path = f"abfss://{container_name}@{storage_account}.dfs.core.windows.net/silver"

# Optional: Service Principal credentials if needed
tenant_id = dbutils.secrets.get(scope="joo-scope", key="tenant-id")
client_id = dbutils.secrets.get(scope="joo-scope", key="client-id")
client_secret = dbutils.secrets.get(scope="joo-scope", key="client-secret")

extra_configs = {
    f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net": "OAuth",
    f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net": client_id,
    f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net": client_secret,
    f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net": f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
}

# Set Spark configs for ADLS access
for k, v in extra_configs.items():
    spark.conf.set(k, v)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3️⃣ Create Sample Data
data = [
    (1, "Alice", "2025-01-01", 100.0),
    (2, "Bob", "2025-01-05", 150.5),
    (3, "Charlie", "2025-01-10", 200.75),
]

columns = ["customer_id", "name", "signup_date", "spend"]

pdf = pd.DataFrame(data, columns=columns)
df = spark.createDataFrame(pdf)

df.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4️⃣ Write Data to Bronze Delta Table
df.write.format("delta").mode("overwrite").save(bronze_path)
print(f"✅ Bronze Delta table saved to: {bronze_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5️⃣ Read Bronze Table Back
df_bronze = spark.read.format("delta").load(bronze_path)
df_bronze.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6️⃣ Transform Data and Write Silver Table
df_silver = df_bronze.withColumn("high_spender", col("spend") > 120.0)
df_silver.write.format("delta").mode("overwrite").save(silver_path)
print(f"✅ Silver Delta table saved to: {silver_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7️⃣ Read Silver Table Back
df_silver_read = spark.read.format("delta").load(silver_path)
df_silver_read.show(truncate=False)
