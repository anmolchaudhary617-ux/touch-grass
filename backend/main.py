from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.mission import router as mission_router

app = FastAPI(title="Touch Grass API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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