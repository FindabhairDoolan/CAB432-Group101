import os, json, time, boto3
from configure import SQS_QUEUE_URL, AWS_REGION
from aws import now_iso
from transcoder.controllers import run_transcode
from transcoder import models

sqs = boto3.client("sqs", region_name=AWS_REGION)

def handle_message(msg):
    body = json.loads(msg["Body"])
    owner     = body["owner"]
    task_id   = body["taskId"]
    input_key = body["inputKey"]
    output    = body["outputKey"]
    preset    = body["preset"]

    #Flip to running
    models.update_task_status(uploaded_by=owner, task_id=task_id, status="running", started_at=now_iso())

    #Do the work
    run_transcode(owner, task_id, input_key, output, preset)

def main():
    while True:
        resp = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,    
            VisibilityTimeout=900    
        )
        msgs = resp.get("Messages", [])
        if not msgs:
            continue
        for m in msgs:
            receipt = m["ReceiptHandle"]
            try:
                handle_message(m)
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)
            except Exception as e:
                print("Worker error:", e)
        time.sleep(1)

if __name__ == "__main__":
    main()
