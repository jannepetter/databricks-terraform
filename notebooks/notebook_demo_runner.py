# Databricks notebook source
# MAGIC %md
# MAGIC Fully UC-compliant and serverless-ready.

# COMMAND ----------
from pyspark.sql import SparkSession
from pyspark.dbutils import DBUtils
from src_module.core.demo_data_fetcher import DemoDataFetcher

spark = SparkSession.builder.getOrCreate()
dbutils = DBUtils(spark)
dbutils.widgets.text("env", "")
dbutils.widgets.text("catalog", "")
dbutils.widgets.text("task_name", "")
dbutils.widgets.text("source", "nosource")

env = dbutils.widgets.get("env")
catalog = dbutils.widgets.get("catalog")
task_name = dbutils.widgets.get("task_name")
source = dbutils.widgets.get("source")

fetcher = DemoDataFetcher(catalog, env, True)


print(
    f"""
Running with:
  env       = {env}
  catalog   = {catalog}
  schema    = {task_name}
  run_mode  = {source}
"""
)

fetcher.run_job(task_name, source)
