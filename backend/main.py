from fastapi import FastAPI

app = FastAPI(title="Touch Grass API")


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