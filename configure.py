import boto3
import json
from botocore.exceptions import ClientError

region_name = "ap-southeast-2"

ssm = boto3.client('ssm', region_name=region_name)
secrets_client = boto3.client(service_name='secretsmanager', region_name=region_name)

def get_secret(secret_name: str) -> str:
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response.get('SecretString')
        return secret
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret {secret_name}: {e}")

def get_parameter(parameter_name: str) -> str:
    try:
        response = ssm.get_parameter(Name=parameter_name)
        return response['Parameter']['Value']
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve parameter {parameter_name}: {e}")

#hardcoded so it dosent tweak
SQS_QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/901444280953/group101-transcode-queue"

#Now load config
AWS_REGION = region_name
S3_BUCKET = get_parameter("/Group101/S3_BUCKET")
DDB_TABLE_FILES = get_parameter("/Group101/DDB_TABLE_FILES")
DDB_TABLE_TASKS = get_parameter("/Group101/DDB_TABLE_TASKS")
QUT_USERNAME = "n11957557@qut.edu.au"

USER_POOL_ID = get_parameter("/Group101/USER_POOL_ID")
CLIENT_ID = get_parameter("/Group101/CLIENT_ID")

#From Secrets Manager
secret_json = get_secret("group101-cognitosecret")
CLIENT_SECRET = json.loads(secret_json)["CLIENT_SECRET"]
