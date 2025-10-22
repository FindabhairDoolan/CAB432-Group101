import os, threading, subprocess, tempfile
from datetime import datetime
from fastapi import UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from auth import authenticate_token

from aws import s3, now_iso, new_file_id
from configure import S3_BUCKET
from transcoder import models

import boto3, json
from configure import SQS_QUEUE_URL, AWS_REGION
sqs = boto3.client("sqs", region_name=AWS_REGION)

#uploade to s3
async def upload_video(file: UploadFile = File(...), user=Depends(authenticate_token)):
    username = user['username']
    filename = os.path.basename(file.filename)
    created_at = now_iso()
    file_id = new_file_id()

    #S3 key with by user and fileId
    s3_key = f"uploads/{username}/{file_id}/{filename}"

    #stream file to temp file then uploads
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
        tmp_path = tmp.name

    size = os.path.getsize(tmp_path)
    try:
        s3.upload_file(tmp_path, S3_BUCKET, s3_key, ExtraArgs={"ContentType": file.content_type or "application/octet-stream"})
    finally:
        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass

    meta = models.create_video_metadata(file_id, filename, s3_key, size, username, created_at)
    return {"file": meta}

#presigned url for browser upload
async def presign_upload(filename: str, user=Depends(authenticate_token)):
    import urllib.parse
    username = user['username']
    file_id = new_file_id()
    created_at = now_iso()
    safe_name = os.path.basename(filename)
    s3_key = f"uploads/{username}/{file_id}/{safe_name}"

    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": S3_BUCKET, "Key": s3_key},
        ExpiresIn=300
    )
    #metadata
    models.create_video_metadata(file_id, safe_name, s3_key, 0, username, created_at)
    return {"uploadUrl": url, "fileId": file_id, "s3Key": s3_key}

#transcodes(download from s3 then uploads new thing to s3)
def run_transcode(task_owner, task_id, input_key, output_key, preset):
    started = now_iso()
    models.update_task_status(task_owner, task_id, "running", started_at=started)

    allowed_presets = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
    height = allowed_presets.get(preset, 1080)

    in_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{preset}.mp4").name

    try:
        #Download from S3
        s3.download_file(S3_BUCKET, input_key, in_tmp)

        #Transcode
        cmd = [
            "ffmpeg", "-y",
            "-i", in_tmp,
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-crf", "28",
            "-vf", f"scale=-2:{height}",
            "-threads", "0",
            out_tmp
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #Upload output to S3
        s3.upload_file(out_tmp, S3_BUCKET, output_key, ExtraArgs={"ContentType": "video/mp4"})

        finished = now_iso()
        models.update_task_status(task_owner, task_id, "finished", output_key=output_key, finished_at=finished)
    except subprocess.CalledProcessError as e:
        models.update_task_status(task_owner, task_id, "failed", error=str(e))
    finally:
        for p in (in_tmp, out_tmp):
            try: os.remove(p)
            except FileNotFoundError: pass

#start transcode
async def start_transcode(
    file_id: str,
    preset: str = Query("1080p", description="Resolution presets: '1080p', '720p', '480p', '360p'"),
    user=Depends(authenticate_token)
):
    username = user['username']
    file_meta = models.get_video_by_id(file_id, uploaded_by=username) if not user.get("admin") else None

    if user.get("admin"):
        file_meta = file_meta or models.get_video_by_id(file_id, uploaded_by=username)
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")

    allowed_presets = ["1080p", "720p", "480p", "360p"]
    if preset not in allowed_presets:
        raise HTTPException(status_code=400, detail=f"Invalid preset: {preset}")

    task = models.create_task_record(uploaded_by=username, file_id=file_id, preset=preset, created_at=now_iso())
    task_id = task["id"]

    #Output S3 key mirrors input under outputs/
    base_name = os.path.splitext(os.path.basename(file_meta["s3Key"]))[0]
    output_key = f"outputs/{username}/{file_id}/{base_name}_{preset}.mp4"

    #Create the task record
    task = models.create_task_record(uploaded_by=username, file_id=file_id, preset=preset, created_at=now_iso())
    task_id = task["id"]

    #queue a job to SQS for the worker service
    msg = {
        "taskId": task_id,
        "fileId": file_id,
        "preset": preset,
        "owner": username,
        "inputKey": file_meta["s3Key"],
        "outputKey": output_key
    }
    sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(msg))

    # leave task status as 'queued' – worker will flip to 'running'
    return {"task_id": task_id, "status": "queued"}

#listening and fetching(per user)
async def list_videos(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    user=Depends(authenticate_token)
):
    if user.get("admin"):
        return models.get_all_videos(limit=limit, offset=offset, sort_by=sort_by, order=order)
    return models.get_all_videos(limit=limit, offset=offset, sort_by=sort_by, order=order, uploaded_by=user["username"])

#get video
async def get_video(file_id: str, user=Depends(authenticate_token)):
    if user.get("admin"):
        v = models.get_video_by_id_any(file_id)  # admin sees any file
    else:
        v = models.get_video_by_id(file_id, uploaded_by=user["username"])
    if not v:
        raise HTTPException(status_code=404, detail="File not found")
    return v

async def list_tasks(
    status: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("id"),
    order: str = Query("desc"),
    user=Depends(authenticate_token)
):
    if user.get("admin"):
        return models.get_tasks(uploaded_by=None, status=status, limit=limit, offset=offset, sort_by=sort_by, order=order)
    return models.get_tasks(uploaded_by=user["username"], status=status, limit=limit, offset=offset, sort_by=sort_by, order=order)

async def get_task(task_id: str, user=Depends(authenticate_token)):
    if user.get("admin"):
        t = models.get_task_by_id_any(task_id)
    else:
        t = models.get_task_by_id(uploaded_by=user["username"], task_id=task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t

#download via presigned get
async def download_transcoded(task_id: str, user=Depends(authenticate_token)):
    t = models.get_task_by_id(uploaded_by=user["username"], task_id=task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    if t["status"] != "finished" or not t.get("output_key"):
        raise HTTPException(status_code=400, detail="Transcoding not finished yet")

    #presigned get
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": S3_BUCKET, "Key": t["output_key"]},
        ExpiresIn=300
    )
    return JSONResponse({"downloadUrl": url})


