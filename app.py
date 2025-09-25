from fastapi import FastAPI
from transcoder.routes import router

# Create FastAPI instance
app = FastAPI(title="Video Transcoder API", version="0.0.1")

# Include API routers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
