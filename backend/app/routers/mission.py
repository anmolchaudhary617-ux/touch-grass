from fastapi import APIRouter, HTTPException

from app.models.mission import MissionRequest, MissionResponse
from app.models.next_clue import NextClueRequest, NextClueResponse
from app.services.mission_service import generate_mission, generate_next_clue


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


@router.post("/missions/next-clue", response_model=NextClueResponse)
async def create_next_clue(request: NextClueRequest):
    """Generate the next adventure clue from the user's observation."""
    try:
        return await generate_next_clue(request)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
