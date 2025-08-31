from fastapi import APIRouter
from transcoder.controllers import (
    upload_video,
    start_transcode,
    list_videos,
    list_tasks,
    get_task,
    get_video,
    download_transcoded
)

router = APIRouter()

# File endpoints
router.post("/upload")(upload_video)
router.get("/files")(list_videos)
router.get("/files/{file_id}")(get_video)

# Task endpoints
router.post("/tasks/start/{file_id}")(start_transcode)
router.get("/tasks")(list_tasks)
router.get("/tasks/{task_id}")(get_task)
router.get("/tasks/download/{task_id}")(download_transcoded)
