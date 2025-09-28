import datetime, uuid, boto3
from configure import AWS_REGION

s3 = boto3.client("s3", region_name=AWS_REGION)
dynamo = boto3.client("dynamodb", region_name=AWS_REGION)

def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def new_file_id():
    # sortable-ish ID with timestamp prefix
    return f"FILE#{now_iso()}#{uuid.uuid4().hex[:8]}"

def new_task_id():
    return f"TASK#{now_iso()}#{uuid.uuid4().hex[:8]}"
