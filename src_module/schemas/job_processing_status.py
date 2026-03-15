from pyspark.sql.types import StructType, StructField, StringType, TimestampType

JOB_STATUS_SCHEMA = StructType(
    [
        StructField("company_id", StringType(), True),
        StructField("company_name", StringType(), True),
        StructField("job_name", StringType(), False),
        StructField("source_system", StringType(), True),
        StructField("source_system_key_id", StringType(), True),
        StructField("status", StringType(), False),
        StructField("last_run_start_time", TimestampType(), True),
        StructField("last_run_end_time", TimestampType(), True),
        StructField("worker_id", StringType(), True),
        StructField("error_message", StringType(), True),
        StructField("id", StringType(), False),
        StructField("updated_at", TimestampType(), True),
        StructField("ETLInsertTime", TimestampType(), True),
    ]
)

SOME_SCHEMA = StructType(
    [
        StructField("company_id", StringType(), True),
        StructField("company_name", StringType(), True),
        StructField("ETLInsertTime", TimestampType(), True),
    ]
)
