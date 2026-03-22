# Databricks notebook source
# MAGIC %md
# MAGIC Fully UC-compliant and serverless-ready.

# COMMAND ----------
from pyspark.sql import SparkSession
from src_module.core.demo_data_fetcher import DemoDataFetcher
from azure.keyvault.secrets import SecretClient
spark = SparkSession.builder.getOrCreate()

CATALOG = "devjoo"

fetcher = DemoDataFetcher(CATALOG, "dev", True)
fetcher.drop_table("bronze", "job_processing_status")
fetcher.init_schemas()
fetcher.add_jobs_to_queue([{"name": "joo"}, {"name": "juu"}], "job-queue-1")


credential = dbutils.credentials.getServiceCredentialsProvider('access-connector-name')

# Point to your Key Vault
vault_url = "https://kv-mytest-base.vault.azure.net/"
client = SecretClient(vault_url=vault_url, credential=credential)

# Fetch the secret
secret_value = client.get_secret("test-secret").value

print("testsecret: ",secret_value)
