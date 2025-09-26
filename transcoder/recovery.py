import os, threading
from aws import now_iso
from transcoder import models
from transcoder.controllers import run_transcode 
from aws import S3_BUCKET 

def _compute_output_key(username: str, file_s3_key: str, file_id: str, preset: str) -> str:
    base_name = os.path.splitext(os.path.basename(file_s3_key))[0]
    return f"outputs/{username}/{file_id}/{base_name}_{preset}.mp4"

def resume_incomplete_tasks():
    candidates = models.get_tasks_by_statuses({"queued", "running"})
    if not candidates:
        return

    for t in candidates:
        file_meta = models.get_video_by_id_any(t["file_id"])
        if not file_meta:
            #If the file metadata is gone, fail task
            models.update_task_status(
                uploaded_by=t["uploaded_by"],
                task_id=t["id"],
                status="failed",
                error="Missing source file metadata"
            )
            continue

        input_key = file_meta["s3Key"]
        output_key = t.get("output_key") or _compute_output_key(
            t["uploaded_by"], input_key, t["file_id"], t["preset"]
        )

        #remarks status as running
        if t["status"] != "running":
            models.update_task_status(
                uploaded_by=t["uploaded_by"],
                task_id=t["id"],
                status="running",
                started_at=now_iso()
            )

        #Relaunch transcode
        thread = threading.Thread(
            target=run_transcode,
            args=(t["uploaded_by"], t["id"], input_key, output_key, t["preset"]),
            daemon=True
        )
        thread.start()
