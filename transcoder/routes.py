from fastapi import APIRouter
from transcoder.controllers import (
    upload_video,
    presign_upload,
    start_transcode,
    list_videos,
    list_tasks,
    get_task,
    get_video,
    download_transcoded
)
from auth import signup_user, confirm_user, login_user

router = APIRouter()


#Upload endpoints
router.post("/upload")(upload_video)            
router.post("/upload-url")(presign_upload)       

#File endpoints
router.get("/files")(list_videos)
router.get("/files/{file_id}")(get_video)       

#Task endpoints
router.post("/tasks/start/{file_id}")(start_transcode)  
router.get("/tasks")(list_tasks)
router.get("/tasks/{task_id}")(get_task)         
router.get("/tasks/download/{task_id}")(download_transcoded)

#auth endpoints
router.post("/auth/signup")(signup_user)
router.post("/auth/confirm")(confirm_user)
router.post("/auth/login")(login_user)


