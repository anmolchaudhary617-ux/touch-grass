import json
from typing import Any

from fastapi import HTTPException

from app.models.mission import MissionRequest, MissionResponse
from app.services.ollama import generate


async def generate_mission(request: MissionRequest) -> MissionResponse:
    """Generate a mission using the Ollama model."""

    prompt = (
        "You are an AI that creates an outdoor adventure mission for a user.\n"
        "Create a mission that encourages the user to put their phone away and explore the real world.\n"
        "The mission must be safe, require no special equipment, GPS, or location-specific facts.\n"
        "Do NOT assume any specific environment (park, forest, pond, trail, campus, etc.); instead tell the user to observe and interact with whatever surroundings are actually around them.\n"
        "Use a public and appropriate setting and avoid illegal, dangerous, restricted, or trespassing activities.\n"
        "Return ONLY a single valid JSON object with these fields: "
        "title, type, estimated_time, premise, objective, safety_brief, first_clue.\n"
        "The type field must match the requested adventure type.\n"
        "The estimated_time field must match the requested duration.\n"
        "Do not include Markdown, code fences, explanations, or any text "
        "outside the JSON object.\n"
        f"Adventure type: {request.adventure_type}\n"
        f"Duration: {request.duration}\n"
    )

    try:
        raw_response: str = await generate(prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to contact Ollama: {exc}",
        )

    try:
        cleaned = raw_response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        data: Any = json.loads(cleaned)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON from LLM: {exc.msg}",
        )

    try:
        return MissionResponse.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Mission data validation error: {exc}",
        )