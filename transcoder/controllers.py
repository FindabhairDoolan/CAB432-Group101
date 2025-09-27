import os
import threading
import subprocess
from datetime import datetime
from fastapi import UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from transcoder import models
from auth import authenticate_token
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
UPLOADS = os.path.join(DATA_DIR, "uploads")
OUTPUTS = os.path.join(DATA_DIR, "outputs")
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

#upload video
async def upload_video(file: UploadFile = File(...), user=Depends(authenticate_token)):
    username = user['username']
    filename = os.path.basename(file.filename)
    timestamp = int(datetime.utcnow().timestamp())
    storage_name = f"{timestamp}__{filename}"
    dest_path = os.path.join(UPLOADS, storage_name)
    
    with open(dest_path, "wb") as out:
        while True:
            chunk = await file.read(1024*1024)
            if not chunk:
                break
            out.write(chunk)
    
    size = os.path.getsize(dest_path)
    meta = models.create_video_metadata(filename, dest_path, size, username)
    return {"file": meta}

#run the transcode
def run_transcode(task_id, input_path, output_path, preset):
    started = datetime.utcnow()
    models.update_task_status(task_id, "running", started_at=started)
    
    allowed_presets = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
    height = allowed_presets.get(preset, 1080)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "veryslow",
        "-crf", "28",
        "-vf", f"scale=-2:{height}",
        "-threads", "0",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        finished = datetime.utcnow()
        models.update_task_status(task_id, "finished", output_path=output_path, finished_at=finished)
    except subprocess.CalledProcessError as e:
        models.update_task_status(task_id, "failed", error=str(e))

#Start transcode
async def start_transcode(
    file_id: int,
    preset: str = Query("1080p", description="Resolution presets: '1080p', '720p', '480p', '360p'"),
    user=Depends(authenticate_token)
):
    
    file_meta = models.get_video_by_id(file_id)
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")

    allowed_presets = ["1080p", "720p", "480p", "360p"]
    if preset not in allowed_presets:
        raise HTTPException(status_code=400, detail=f"Invalid preset: {preset}")


    if not user.get("admin") and file_meta["uploaded_by"] != user["username"]:
        raise HTTPException(status_code=403, detail="Forbidden: cannot transcode files of other users")

    task = models.create_task_record(file_id, preset)
    task_id = task["id"]

    base = os.path.basename(file_meta["storage_path"])
    out_name = f"task{task_id}__{preset}__{base}.mp4"
    out_path = os.path.join(OUTPUTS, out_name)

    t = threading.Thread(
        target=run_transcode,
        args=(task_id, file_meta["storage_path"], out_path, preset),
        daemon=True
    )
    t.start()
    
    return {"task_id": task_id, "status": "started"}

#get videos
async def list_videos(
    limit: int = Query(10, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort by 'created_at','id', 'filename' or 'size'" ),
    order: str = Query("desc", description="Order by 'asc' (ascending) or 'desc' descending"),
    user=Depends(authenticate_token)
):

    if user.get("admin"):
        # Admin sees all files
        return models.get_all_videos(limit=limit, offset=offset, sort_by=sort_by, order=order)
    else:
        # Regular user sees only their files
        return models.get_all_videos(limit=limit, offset=offset, sort_by=sort_by, order=order, uploaded_by=user["username"])

#get video
async def get_video(file_id: int, user=Depends(authenticate_token)):
    file_meta = models.get_video_by_id(file_id)

    #Ownership check
    if not user.get("admin") and file_meta["uploaded_by"] != user["username"]:
        raise HTTPException(status_code=403, detail="Forbidden: cannot access this video")
    
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
    return file_meta

#get tasks
async def list_tasks(
    status: str = Query(None, description="Filter tasks by 'queued', 'started', 'running', 'finished', 'failed'"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("id", description="Sort by 'id', 'file_id', 'preset', 'status', 'started_at', 'finished_at'"),
    order: str = Query("desc", description="Order by 'asc' (ascending) or 'desc' descending"),
    user=Depends(authenticate_token)
):

    if user.get("admin"):
        return models.get_tasks(status=status, limit=limit, offset=offset, sort_by=sort_by, order=order)
    else:
        return models.get_tasks(status=status, limit=limit, offset=offset, sort_by=sort_by, order=order, username=user["username"])

#get task
async def get_task(task_id: int, user=Depends(authenticate_token)):
    task = models.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    file_meta = models.get_video_by_id(task["file_id"])
    if not user.get("admin") and file_meta["uploaded_by"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not allowed to view this task")


    return task

#download
async def download_transcoded(task_id: int, user=Depends(authenticate_token)):
    task = models.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    file_meta = models.get_video_by_id(task["file_id"])
    if not user.get("admin") and file_meta["uploaded_by"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not allowed to download this task")


    if task["status"] != "finished" or not task.get("output_path"):
        raise HTTPException(status_code=400, detail="Transcoding not finished yet")

    output_path = task["output_path"]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        path=output_path,
        filename=os.path.basename(output_path),
        media_type="application/octet-stream"
    )
