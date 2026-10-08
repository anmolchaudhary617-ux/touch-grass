from fastapi import APIRouter, HTTPException
from app.models.mission import MissionRequest, MissionResponse
from app.services.mission_service import generate_mission

router = APIRouter(prefix="/api", tags=["Missions"])

@router.post("/missions", response_model=MissionResponse)
async def create_mission(request: MissionRequest):
    """Endpoint to generate a new Touch Grass mission.

    The request validates `adventure_type` and `duration`. The service builds the
    prompt, calls Ollama, parses the JSON, validates it against ``MissionResponse``
    and returns the mission data.
    """
    try:
        mission = await generate_mission(request)
        return mission
    except HTTPException:
        # Propagate HTTPExceptions from the service (e.g., Ollama failures or JSON errors)
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
