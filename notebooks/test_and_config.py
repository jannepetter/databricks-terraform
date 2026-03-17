# Databricks notebook source
# MAGIC %md
# MAGIC Fully UC-compliant and serverless-ready.

# COMMAND ----------
from pyspark.sql import SparkSession
from src_module.core.demo_data_fetcher import DemoDataFetcher

spark = SparkSession.builder.getOrCreate()

CATALOG = "devjoo"

fetcher = DemoDataFetcher(CATALOG, "dev", True)
fetcher.drop_table("bronze", "job_processing_status")
fetcher.init_schemas()
fetcher.add_jobs_to_queue([{"name": "joo"}, {"name": "juu"}], "job-queue-1")
