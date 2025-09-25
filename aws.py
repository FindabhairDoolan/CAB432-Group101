import os, datetime, uuid
import boto3

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.environ["S3_BUCKET"]
TABLE_FILES = os.environ["DDB_TABLE_FILES"]
TABLE_TASKS = os.environ["DDB_TABLE_TASKS"]
QUT_USERNAME = os.environ["QUT_USERNAME"]  # e.g., n1234567@qut.edu.au

s3 = boto3.client("s3", region_name=AWS_REGION)
dynamo = boto3.client("dynamodb", region_name=AWS_REGION)

def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def new_file_id():
    # sortable-ish ID with timestamp prefix
    return f"FILE#{now_iso()}#{uuid.uuid4().hex[:8]}"

def new_task_id():
    return f"TASK#{now_iso()}#{uuid.uuid4().hex[:8]}"
