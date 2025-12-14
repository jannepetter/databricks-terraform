# Databricks notebook source
# MAGIC %md
# MAGIC # Demo Delta Tables Notebook with UAMI Authentication
# MAGIC before creating demo Delta tables.

# COMMAND ----------
# MAGIC %md
# MAGIC ## 0️⃣ Configure Authentication

# COMMAND ----------
import logging
from pyspark.sql import SparkSession

# Standard_D2ds_v6      1.12 DBU/h      8GB Memory  2 core

tenant_id = dbutils.secrets.get(scope="joo-scope", key="tenant-id")
client_id = dbutils.secrets.get(scope="joo-scope", key="client-id")
client_secret = dbutils.secrets.get(scope="joo-scope", key="client-secret")
MOUNT_NAME = "/mnt/joo-scope"

bronze_path = f"{MOUNT_NAME}/bronze"
silver_path = f"{MOUNT_NAME}/silver"

spark = SparkSession.builder.getOrCreate()

storage_account = "testadlsdbdemo123"
container_name = "datalake"
base_path = f"abfss://{container_name}@{storage_account}.dfs.core.windows.net/demo"


def mount_exists(path):
    try:
        dbutils.fs.ls(path)
        return True
    except:
        return False


def ensure_mount():
    # Check if already mounted
    if not mount_exists(MOUNT_NAME):
        logging.info("Not mounted, mounting now")
        config_mount()
    else:
        logging.info("Already mounted")


def config_mount():
    extra_configs = {
        "fs.azure.account.auth.type": "OAuth",
        "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
        "fs.azure.account.oauth2.client.id": client_id,
        "fs.azure.account.oauth2.client.secret": client_secret,
        "fs.azure.account.oauth2.client.endpoint": f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
    }
    try:
        dbutils.fs.mount(
            source=base_path, mount_point=MOUNT_NAME, extra_configs=extra_configs
        )
    except Exception as e:
        print("Error mounting", e)


ensure_mount()

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
# MAGIC ## 2️⃣ Write Demo Data to Bronze Delta Table

# COMMAND ----------
df.write.format("delta").mode("overwrite").save(bronze_path)
print(f"✅ Bronze Delta table created at: {bronze_path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3️⃣ Read Bronze Table Back

# COMMAND ----------
df_bronze = spark.read.format("delta").load(bronze_path)
df_bronze.show(truncate=False)
# display(df_bronze)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4️⃣ Simple Transformation and Silver Table

# COMMAND ----------
from pyspark.sql.functions import col

df_silver = df_bronze.withColumn("status", col("spend") > 120.0)
df_silver.write.format("delta").mode("overwrite").save(silver_path)

print(f"✅ Silver Delta table created at: {silver_path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5️⃣ Read Silver Table Back

# COMMAND ----------
df_silver_read = spark.read.format("delta").load(silver_path)
df_silver_read.show(truncate=False)
