
import json
import random
from typing import Any

from fastapi import HTTPException

from app.models.mission import MissionRequest, MissionResponse
from app.models.next_clue import NextClueRequest, NextClueResponse
from app.services.clue_progression import (
    build_progression_block,
    fallback_clue,
    is_repetitive,
    select_next_step,
)
from app.services.ollama import generate


MISSION_BLUEPRINTS = {
    "comparison": {
        "title": "The Curious Contrast",
        "premise": (
            "Two ordinary features may seem alike at first. "
            "A closer comparison may reveal a difference worth noticing."
        ),
        "objective": (
            "Compare two visible features. Identify one similarity "
            "and one difference using evidence you can directly observe."
        ),
        "first_clue": (
            "Choose two features visible from your current safe position. "
            "Compare their shape, appearance, orientation, or placement. "
            "If no suitable pair stands out, choose any two visible features."
        ),
    },
    "hidden_detail": {
        "title": "The Overlooked Detail",
        "premise": (
            "An ordinary scene can look different when you pay attention "
            "to a detail you previously overlooked."
        ),
        "objective": (
            "Notice one visible detail and explain how it relates to "
            "the larger scene. Use direct observations, not guesses."
        ),
        "first_clue": (
            "Observe a scene from a safe position. Choose a detail you "
            "can clearly see and consider how it relates to its surroundings. "
            "If nothing stands out, compare two visible features."
        ),
    },
    "mismatch": {
        "title": "The Unexpected Difference",
        "premise": (
            "Features in the same surroundings do not always look or "
            "appear arranged in the same way."
        ),
        "objective": (
            "Find a visible difference between comparable features. "
            "Describe what differs without assuming why."
        ),
        "first_clue": (
            "Look at two comparable visible features. Compare their shape, "
            "position, or appearance. If nothing seems unusual, simply "
            "record a clear difference between them."
        ),
    },
    "pattern_break": {
        "title": "The Pattern Detective",
        "premise": (
            "Repeated shapes, spacing, or arrangements can make small "
            "variations easier to notice."
        ),
        "objective": (
            "Identify a naturally occurring visual pattern and one "
            "observable variation. If no clear pattern exists, compare "
            "two visible features instead."
        ),
        "first_clue": (
            "Look for a pattern already present in your surroundings. "
            "Do not arrange or move anything. If no clear pattern is visible, "
            "compare two features instead."
        ),
    },
    "boundary": {
        "title": "Where Things Meet",
        "premise": (
            "The transition between two adjacent features can reveal "
            "interesting differences in shape or appearance."
        ),
        "objective": (
            "Examine a visible transition between adjacent features. "
            "Describe its shape or appearance without guessing its cause."
        ),
        "first_clue": (
            "Look for two adjacent features that meet or transition. "
            "Observe their visible relationship from a safe position. "
            "If no clear transition is available, compare two nearby features."
        ),
    },
}


ADVENTURE_TYPE_BLUEPRINTS: dict[str, list[str]] = {
    "investigate": ["comparison", "mismatch"],
    "observe": ["hidden_detail", "pattern_break"],
    "discover": ["boundary", "pattern_break"],
}

DURATION_SCOPES: dict[str, str] = {
    "10-15": "For a quick 10â€“15 minute scan from your immediate safe position:",
    "20-30": "Over a 20â€“30 minute exploration of your safe surroundings:",
    "30-45": "During an unhurried 30â€“45 minute walk through your safe surroundings:",
}


async def generate_mission(request: MissionRequest) -> MissionResponse:
    """Generate an AI-themed mission using a Python-controlled blueprint."""

    allowed_concepts = ADVENTURE_TYPE_BLUEPRINTS.get(
        request.adventure_type,
        list(MISSION_BLUEPRINTS.keys()),
    )
    previous = getattr(generate_mission, f"_last_concept_{request.adventure_type}", None)

    # Avoid repeating the same concept on consecutive requests of the same type.
    choices = [name for name in allowed_concepts if name != previous]
    concept_name = random.choice(choices or allowed_concepts)
    setattr(generate_mission, f"_last_concept_{request.adventure_type}", concept_name)

    blueprint = MISSION_BLUEPRINTS[concept_name]

    print(f"[MISSION] Blueprint selected for {request.adventure_type}: {concept_name}")

    prompt = (
        "Create one short, intriguing title for an outdoor observation "
        "adventure.\n"
        f"Adventure type: {request.adventure_type}\n"
        f"Duration: {request.duration} minutes\n"
        f"Investigation mechanic: {concept_name}\n"
        f"Task: {blueprint['objective']}\n"
        f"Reference title style: {blueprint['title']}\n"
        "The title must accurately match the task. Use broad, "
        "environment-neutral language suitable for parks, streets, "
        "campuses, gardens, or other safe surroundings.\n"
        "Do not mention a specific object, animal, location, event, "
        "or hidden cause unless the task explicitly requires it. "
        "Use 3 to 7 words. Avoid generic titles such as 'Nature's "
        "Visual Puzzle'.\n"
        'Return only a JSON object: {"title": "your title"}'
    )

    try:
        raw_response = await generate(prompt)
        cleaned = raw_response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        data = json.loads(cleaned)

        if not isinstance(data, dict):
            raise ValueError("AI response must be a JSON object.")

        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("AI returned an invalid title.")

        title = title.strip()

        if not 3 <= len(title.split()) <= 7:
            raise ValueError("AI title must contain 3 to 7 words.")

    except Exception as exc:
        print(f"[MISSION] Using blueprint title. Reason: {exc}")
        title = blueprint["title"]

    duration_prefix = DURATION_SCOPES.get(request.duration, "")
    first_clue = f"{duration_prefix} {blueprint['first_clue']}".strip()

    return MissionResponse(
        title=title,
        type=request.adventure_type,
        estimated_time=request.duration,
        premise=blueprint["premise"],
        objective=blueprint["objective"],
        safety_brief=(
            "Stay in a safe, permitted public area. Observe without "
            "touching unknown objects, approaching strangers, crossing "
            "roads for clues, climbing, or entering restricted areas. "
            "You may pause or stop at any time."
        ),
        first_clue=first_clue,
    )


async def generate_next_clue(
    request: NextClueRequest,
) -> NextClueResponse:
    """Generate the next clue using the user's reported observation."""

    required_step = select_next_step(request.current_clue, request.observation)
    progression_block = build_progression_block(
        request.current_clue,
        request.observation,
        required_step,
    )

    prompt = (
        "You guide a real-world outdoor observation adventure.\n"
        "Write wording for the next clue. Python has already chosen the "
        "investigative step. Do not choose a different step.\n"
        "\n"
        f"{progression_block}\n"
        "SAFETY AND EXPERIENCE:\n"
        "- Encourage the user to put their phone away while exploring.\n"
        "- Keep the task safe and suitable for a public setting.\n"
        "- Never require touching unknown objects, approaching strangers, "
        "crossing roads for clues, climbing, or entering restricted areas.\n"
        "- Do not require special equipment, GPS, or location-specific facts.\n"
        "- Keep the clue concise: one or two sentences.\n"
        "- Ask exactly one clear, actionable question or task.\n"
        "- Never invent details or claim to know the cause of a feature.\n"
        "- The user may pause or stop at any time.\n"
        "\n"
        "OUTPUT FORMAT:\n"
        "Return only a JSON object with exactly one string field: "
        "\"next_clue\". No Markdown or additional text.\n"
        "\n"
        f"Mission title: {request.title}\n"
        f"Mission type: {request.type}\n"
        f"Mission premise: {request.premise}\n"
        f"Mission objective: {request.objective}\n"
        f"Current clue: {request.current_clue}\n"
        f"User observation: {request.observation}\n"
        f"Required next step: {required_step}\n"
    )

    try:
        raw_response = await generate(prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to contact Ollama: {exc}",
        ) from exc

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

        if not isinstance(data, dict):
            raise ValueError("The model response must be a JSON object.")

        if "next_clue" not in data:
            for alt_key in ("clue", "nextClue", "next_step", "response"):
                if alt_key in data and isinstance(data[alt_key], str):
                    data = {"next_clue": data[alt_key]}
                    break

    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid JSON from LLM: {exc}",
        ) from exc

    try:
        response = NextClueResponse.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Next clue validation error: {exc}",
        ) from exc

    next_clue = response.next_clue.strip()

    if not next_clue or is_repetitive(
        next_clue,
        request.current_clue,
        request.observation,
        required_step,
    ):
        next_clue = fallback_clue(
            required_step,
            observation=request.observation,
            current_clue=request.current_clue,
        )

    return NextClueResponse(next_clue=next_clue)
