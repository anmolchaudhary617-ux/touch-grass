from typing import Literal
from pydantic import BaseModel


class MissionRequest(BaseModel):
    adventure_type: Literal["investigate", "observe", "discover"]
    duration: Literal["10-15", "20-30", "30-45"]


class MissionResponse(BaseModel):
    title: str
    type: Literal["investigate", "observe", "discover"]
    estimated_time: str
    premise: str
    objective: str
    safety_brief: str
    first_clue: str
