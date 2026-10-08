from typing import Literal
from pydantic import BaseModel

class NextClueRequest(BaseModel):
    title: str
    type: Literal["investigate", "observe", "discover"]
    premise: str
    objective: str
    current_clue: str
    observation: str

class NextClueResponse(BaseModel):
    next_clue: str
