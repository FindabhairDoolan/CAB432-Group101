from fastapi import FastAPI
from auth import router as auth_router
from transcoder.routes import router as trans_router

# Create FastAPI instance
app = FastAPI(title="Video Transcoder API", version="0.0.1")

# Include API routers
app.include_router(auth_router, prefix="")
app.include_router(trans_router, prefix="/videos")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
