
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
    register_initial_clue,
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
        "first_clues": {
            "10-15": (
                "For a quick 10-15 minute scan from your current safe position: "
                "Find two similar, safely observable objects or features nearby, such as two trees, benches, lampposts, or planter boxes. "
                "Compare their shape, height, or surface appearance, and identify one clear similarity and one visible difference. "
                "If no matching pair is nearby, compare two visible sections of a wall, fence, or pavement instead. "
                "Stay in your safe area and do not touch unknown objects or climb anything."
            ),
            "20-30": (
                "Over a 20-30 minute exploration of your safe surroundings: "
                "Find two similar objects or structures positioned slightly apart, such as two light poles, trees, benches, or architectural columns. "
                "Compare their condition, alignment, or surface wear, noting one shared trait and one unmistakable contrast between them. "
                "If suitable pairs are scarce along your path, compare two separate paving sections, windows, or building edges. "
                "Keep to permitted walkways, do not cross roadways for clues, and do not touch unknown objects."
            ),
            "30-45": (
                "During an unhurried 30-45 minute walk through your safe surroundings: "
                "Scan for recurring pairs of features across your route, such as pairs of gates, benches, trees, or structural supports. "
                "Compare how their placement, weathering, or surrounding ground differ between the two locations. "
                "If paired features are hard to find, compare two distinct wall surfaces, path borders, or posted signs along your route. "
                "Stay on safe, public footpaths, do not touch unknown objects, and pause or stop whenever you choose."
            ),
        },
        "first_clue": (
            "Find two similar, safely observable objects or features nearby, such as two trees, benches, lampposts, or planter boxes. "
            "Compare their shape, height, or surface appearance, and identify one clear similarity and one visible difference. "
            "If no matching pair is nearby, compare two visible sections of a wall, fence, or pavement instead. "
            "Stay in your safe area and do not touch unknown objects or climb anything."
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
        "first_clues": {
            "10-15": (
                "For a quick 10-15 minute scan from your current safe position: "
                "Choose one ordinary nearby object or surface, such as a bench, tree trunk, lamppost base, or paved section. "
                "Examine it closely without touching to notice one easily overlooked visual detail, such as a texture change, subtle mark, edge variation, or seam. "
                "If nothing stands out on that feature, examine a different nearby surface or wall section instead. "
                "Stay in your safe area and do not touch unknown objects or step into restricted spaces."
            ),
            "20-30": (
                "Over a 20-30 minute exploration of your safe surroundings: "
                "Pick an everyday structure along your path, such as an exterior wall, railing, pillar, or ground fixture. "
                "Examine its surface for an unexpected detail—such as weathered markings, fastener patterns, subtle color variations, or seam lines—and note how it fits into the surrounding structure. "
                "If the first structure seems uniform, inspect a nearby curb, gate, or paved corner instead. "
                "Remain in safe public areas, do not approach strangers or touch unknown objects, and pause whenever you wish."
            ),
            "30-45": (
                "During an unhurried 30-45 minute walk through your safe surroundings: "
                "As you walk, look for an understated focal point on a larger structure or landscape feature, such as an engraved stamp, stone variation, joint work, or bracket. "
                "Examine how this small element relates to the rest of the object and whether it appears repeated elsewhere along your route. "
                "If no distinctive marking appears, inspect where different building materials or paving stones meet. "
                "Stay on safe, open paths, avoid private property, and do not touch unknown objects."
            ),
        },
        "first_clue": (
            "Choose one ordinary nearby object or surface, such as a bench, tree trunk, lamppost base, or paved section. "
            "Examine it closely without touching to notice one easily overlooked visual detail, such as a texture change, subtle mark, edge variation, or seam. "
            "If nothing stands out on that feature, examine a different nearby surface or wall section instead. "
            "Stay in your safe area and do not touch unknown objects or step into restricted spaces."
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
        "first_clues": {
            "10-15": (
                "For a quick 10-15 minute scan from your current safe position: "
                "Observe a visible group or cluster of similar features, such as a row of windows, fence posts, paving stones, or bollards. "
                "Identify one specific element in the group whose shape, spacing, color, or condition visibly differs from the rest. "
                "If no clear grouping is in view, choose any two comparable objects and identify one clear mismatch between them. "
                "Stay in your safe area and do not touch unknown objects or enter roadway areas."
            ),
            "20-30": (
                "Over a 20-30 minute exploration of your safe surroundings: "
                "Survey an organized series of features along your walking route, such as a line of trees, lampposts, parking barriers, or wall panels. "
                "Locate an individual member of that series that breaks uniformity in spacing, orientation, height, or surface condition. "
                "If the series looks completely uniform, find two adjacent structural features and identify an unexpected difference between them. "
                "Stay on safe walkways, never step into traffic, and do not touch unknown objects."
            ),
            "30-45": (
                "During an unhurried 30-45 minute walk through your safe surroundings: "
                "Trace a extended sequence of recurring objects across your surroundings, such as streetlamps, fence pickets, decorative tiles, or path borders. "
                "Spot an outlier whose alignment, material wear, or shade contrasts with the overall rhythm of the sequence. "
                "If no extended sequence is available, identify an isolated feature that looks distinctly out of place with nearby architecture or vegetation. "
                "Remain in safe public spaces, do not touch unknown objects, and stop or pause whenever needed."
            ),
        },
        "first_clue": (
            "Observe a visible group or cluster of similar features, such as a row of windows, fence posts, paving stones, or bollards. "
            "Identify one specific element in the group whose shape, spacing, color, or condition visibly differs from the rest. "
            "If no clear grouping is in view, choose any two comparable objects and identify one clear mismatch between them. "
            "Stay in your safe area and do not touch unknown objects or enter roadway areas."
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
        "first_clues": {
            "10-15": (
                "For a quick 10-15 minute scan from your current safe position: "
                "Notice a repeating visual pattern in your safe surroundings, such as repeated brick lines, tile joints, railings, or pavement slats. "
                "Identify where that repetition is interrupted, irregular, or changes alignment. "
                "If no repeated pattern is visible, observe any structured edge or seam and note where its line changes. "
                "Stay in your safe area and do not touch unknown objects or step off safe paths."
            ),
            "20-30": (
                "Over a 20-30 minute exploration of your safe surroundings: "
                "Follow a repeating visual rhythm along your route, such as paving grids, window mullions, fence pickets, or sidewalk expansion joints. "
                "Locate a point where the spacing interval widens, narrows, shifts angle, or contains a substituted material. "
                "If a regular pattern is hard to spot, inspect a straight curb line or wall for a sudden gap or contour shift. "
                "Remain on safe designated walkways, watch your footing, and do not touch unknown objects."
            ),
            "30-45": (
                "During an unhurried 30-45 minute walk through your safe surroundings: "
                "Observe larger architectural or landscape patterns across your walk, such as repeating facade bays, planted borders, or overhead canopy spans. "
                "Find an area where the continuous pattern breaks, alters its cadence, or gives way to a contrasting arrangement. "
                "If no broad pattern unfolds, pick two different patterned surfaces along your route and compare where each one changes. "
                "Stay in safe open areas, do not touch unknown objects, and feel free to pause at any time."
            ),
        },
        "first_clue": (
            "Notice a repeating visual pattern in your safe surroundings, such as repeated brick lines, tile joints, railings, or pavement slats. "
            "Identify where that repetition is interrupted, irregular, or changes alignment. "
            "If no repeated pattern is visible, observe any structured edge or seam and note where its line changes. "
            "Stay in your safe area and do not touch unknown objects or step off safe paths."
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
        "first_clues": {
            "10-15": (
                "For a quick 10-15 minute scan from your current safe position: "
                "Notice a visible transition between two adjacent surfaces or materials, such as grass meeting pavement, curb stone meeting asphalt, or light meeting shadow. "
                "Observe the seam line and describe whether the boundary is sharp, uneven, or overlapping. "
                "If no material transition is nearby, observe where a wall meets the ground or pavement. "
                "Stay in your safe area, do not touch unknown objects, and do not cross roads."
            ),
            "20-30": (
                "Over a 20-30 minute exploration of your safe surroundings: "
                "Walk along an edge where two distinct zones or ground materials meet, such as garden bed and walkway, brick and concrete, or shaded corridor and open area. "
                "Observe how the dividing line behaves over distance—does it remain crisp, waver, or gradually blur? "
                "If long boundaries are unavailable, inspect where an exterior wall or fence base meets the sidewalk. "
                "Keep to safe pedestrian routes, avoid stepping near traffic, and do not touch unknown objects."
            ),
            "30-45": (
                "During an unhurried 30-45 minute walk through your safe surroundings: "
                "Trace multiple transition zones between natural and built environments, such as tree lines meeting paving, stone retaining walls meeting soil, or covered walkways opening to open sky. "
                "Observe how the texture, cleanliness, and wear change across these dividing lines. "
                "If varied boundaries are limited, follow the perimeter edge of a courtyard, park lawn, or parking area from a safe path. "
                "Stick to permitted public pathways, do not touch unknown objects, and pause whenever you need."
            ),
        },
        "first_clue": (
            "Notice a visible transition between two adjacent surfaces or materials, such as grass meeting pavement, curb stone meeting asphalt, or light meeting shadow. "
            "Observe the seam line and describe whether the boundary is sharp, uneven, or overlapping. "
            "If no material transition is nearby, observe where a wall meets the ground or pavement. "
            "Stay in your safe area, do not touch unknown objects, and do not cross roads."
        ),
    },
}


ADVENTURE_TYPE_BLUEPRINTS: dict[str, list[str]] = {
    "investigate": ["comparison", "mismatch"],
    "observe": ["hidden_detail", "pattern_break"],
    "discover": ["boundary", "pattern_break"],
}

DURATION_SCOPES: dict[str, str] = {
    "10-15": "For a quick 10-15 minute scan from your immediate safe position:",
    "20-30": "Over a 20-30 minute exploration of your safe surroundings:",
    "30-45": "During an unhurried 30-45 minute walk through your safe surroundings:",
}

# Register all blueprint initial clues into clue_progression's initial registry
for _bp in MISSION_BLUEPRINTS.values():
    if "first_clues" in _bp:
        for _clue in _bp["first_clues"].values():
            register_initial_clue(_clue)
    if "first_clue" in _bp:
        register_initial_clue(_bp["first_clue"])


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

    first_clues_map = blueprint.get("first_clues", {})
    if request.duration in first_clues_map:
        first_clue = first_clues_map[request.duration]
    else:
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
    # Ensure at least 3 observation rounds occur before reflection is allowed
    if (
        request.observation_count is not None
        and request.observation_count < 4
        and required_step == "reflect"
    ):
        required_step = "examine"

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
        'Return only a JSON object with exactly one string field named "next_clue".\n'
        'Example: {"next_clue": "Compare the texture of the bark with a nearby branch."}\n'
        "Do not use other keys like 'answer' or put text outside the JSON.\n"
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

        extracted_clue: str | None = None

        # 1. Direct or known alternative keys
        for key in (
            "next_clue",
            "clue",
            "nextClue",
            "next_step",
            "answer",
            "observation",
            "task",
            "result",
            "response",
        ):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                extracted_clue = val.strip()
                break
            elif isinstance(val, dict):
                # Nested object case
                for sub_key in ("next_clue", "clue", "answer", "text"):
                    sub_val = val.get(sub_key)
                    if isinstance(sub_val, str) and sub_val.strip():
                        extracted_clue = sub_val.strip()
                        break
                if extracted_clue:
                    break

        # 2. If not found in known keys, check any string values
        if not extracted_clue:
            for val in data.values():
                if isinstance(val, str) and len(val.strip().split()) >= 3:
                    extracted_clue = val.strip()
                    break

        # 3. Model used a sentence as dictionary key (e.g., {"Look closely at...": ""})
        if not extracted_clue:
            for key in data.keys():
                if isinstance(key, str) and len(key.strip().split()) >= 3:
                    extracted_clue = key.strip()
                    break

        if extracted_clue:
            data = {"next_clue": extracted_clue}

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
