from fastapi import FastAPI

from app.routers.mission import router as mission_router

app = FastAPI(title="Touch Grass API")

app.include_router(mission_router)


@app.get("/")
def root():
    return {
        "message": "Touch Grass API is running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }