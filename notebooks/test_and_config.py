# Databricks notebook source
# MAGIC %md
# MAGIC Fully UC-compliant and serverless-ready.

# COMMAND ----------
from pyspark.sql import SparkSession
from src_module.core.demo_data_fetcher import DemoDataFetcher

spark = SparkSession.builder.getOrCreate()

CATALOG = "joo"

fetcher = DemoDataFetcher(CATALOG, "dev", True)
