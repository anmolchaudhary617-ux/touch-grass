
from typing import Literal

from pydantic import BaseModel, Field


class NextClueRequest(BaseModel):
    title: str
    type: Literal["investigate", "observe", "discover"]
    premise: str
    objective: str
    current_clue: str
    observation: str
    observation_count: int | None = Field(default=None, ge=1)


class NextClueResponse(BaseModel):
    next_clue: str
