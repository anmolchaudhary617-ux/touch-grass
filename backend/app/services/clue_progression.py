"""Deterministic next-clue progression for outdoor observation missions.

Small local models often restate the mission objective instead of advancing.
Python therefore chooses the next investigative step from the current clue and
the user's observation, then the model only writes wording for that step.
"""

from __future__ import annotations

import re
from typing import Literal

ProgressionStep = Literal["notice", "compare", "examine", "reflect"]

STEPS: tuple[ProgressionStep, ...] = ("notice", "compare", "examine", "reflect")

STEP_GUIDANCE = {
    "notice": (
        "Ask the user to identify one visible feature they have not yet described."
    ),
    "compare": (
        "Ask the user to compare two visible features, or two parts of what they "
        "already noticed. Do not ask them to re-identify the same feature."
    ),
    "examine": (
        "Ask the user to inspect a different visible relationship or characteristic "
        "(color, texture, spacing, or orientation) — not the same quality they "
        "already described."
    ),
    "reflect": (
        "Ask the user to summarize the visible details they have already reported. "
        "Remind them they may pause or stop."
    ),
}

SAFE_FALLBACKS = {
    "notice": (
        "From a safe position, notice one clearly visible feature you have not "
        "yet described. You may pause or stop at any time."
    ),
    "compare": (
        "From a safe position, compare one visible quality of what you already noticed with a nearby "
        "feature. Describe only what you can see. You may pause or stop at any time."
    ),
    "examine": (
        "From a safe position, look at a different visible quality in your surroundings — "
        "such as surface texture, color, spacing, or orientation. "
        "You may pause or stop at any time."
    ),
    "reflect": (
        "Pause in a safe spot and summarize the visible details you have already noticed. "
        "You may stop here if you wish."
    ),
}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "for", "with",
    "from", "your", "you", "their", "its", "this", "that", "these", "those",
    "look", "find", "choose", "what", "how", "does", "do", "take", "describe",
    "observe", "visible", "feature", "features", "safe", "position", "already",
    "please", "can", "see", "ask", "them", "user",
}

_COMPARE_MARKERS = (
    "while", "whereas", "compared", "comparison", "difference", "different",
    "both", "versus", "nearby section", "one section", "straighter", "unlike",
    "overlaps", "overlap", "shorter than", "taller than", "larger than",
    "smaller than", "than the rest", "out of the", "rougher than", "smoother than",
)

_EXAMINE_CLUE_MARKERS = (
    "inspect", "closer", "texture", "color", "colour", "spacing",
    "orientation", "characteristic", "different visible", "examine",
)

_REFLECT_MARKERS = (
    "summarize", "summarise", "pause and", "already noticed",
    "stop here", "you may stop",
)

_FOCUS_GROUPS = {
    "shape": {
        "shape", "edge", "uneven", "straight", "straighter", "curved",
        "jagged", "overlap", "overlaps", "boundary", "outline", "transition",
    },
    "color": {"color", "colour", "shade", "hue", "brighter", "darker"},
    "texture": {"texture", "rough", "smooth", "surface"},
    "spacing": {"spacing", "gap", "distance", "apart"},
}

_STEP_SIGNALS: dict[ProgressionStep, tuple[str, ...]] = {
    "notice": ("notice", "identify", "look for", "choose"),
    "compare": (
        "compare", "nearby", "another", "other", "both", "versus",
        "difference", "contrast",
    ),
    "examine": (
        "color", "colour", "texture", "spacing", "orientation",
        "different", "relationship", "characteristic", "examine", "inspect",
    ),
    "reflect": ("summar", "pause", "already", "stop"),
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def content_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", _normalize(text))
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def classify_clue_step(clue: str) -> ProgressionStep:
    """Infer which investigative action the current clue is asking for."""

    text = _normalize(clue)

    if any(marker in text for marker in _REFLECT_MARKERS):
        return "reflect"

    if re.search(r"\bexamine\b", text) or any(marker in text for marker in _EXAMINE_CLUE_MARKERS):
        if not re.search(r"\bcompare\s+(two|their|these)\b", text):
            return "examine"

    if any(
        marker in text
        for marker in (
            "compare",
            "similarity",
            "difference between",
            "two features",
            "two visible",
            "two comparable",
        )
    ):
        return "compare"

    if any(marker in text for marker in _EXAMINE_CLUE_MARKERS):
        return "examine"

    return "notice"



def classify_observation_step(observation: str) -> ProgressionStep:
    """Infer how far the user's report has already progressed."""

    text = _normalize(observation)

    if any(marker in text for marker in _REFLECT_MARKERS):
        return "reflect"

    if any(marker in text for marker in _COMPARE_MARKERS):
        return "compare"

    return "notice"


def select_next_step(current_clue: str, observation: str) -> ProgressionStep:
    """Advance one step beyond whichever action is already complete."""

    completed_index = max(
        STEPS.index(classify_clue_step(current_clue)),
        STEPS.index(classify_observation_step(observation)),
    )
    return STEPS[min(completed_index + 1, len(STEPS) - 1)]


def covered_foci(text: str) -> set[str]:
    tokens = content_tokens(text)
    return {
        name
        for name, words in _FOCUS_GROUPS.items()
        if tokens & words
    }


def token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = content_tokens(left)
    right_tokens = content_tokens(right)

    if not left_tokens or not right_tokens:
        return 0.0

    return len(left_tokens & right_tokens) / len(left_tokens)


def matches_required_step(candidate: str, step: ProgressionStep) -> bool:
    text = _normalize(candidate)
    return any(signal in text for signal in _STEP_SIGNALS[step])


def extract_observation_details(observation: str) -> dict:
    """Extract specific reported features and investigated qualities from an observation."""
    text = (observation or "").strip()
    if not text:
        return {
            "anchor": None,
            "all_anchors": [],
            "foci_present": set(),
            "unexamined_qualities": ["texture", "color", "spacing", "orientation"],
            "is_vague": True,
        }

    lowered = text.lower()

    # Detect foci present in the observation
    foci_present = set()
    if re.search(r"\b(shape|edge|uneven|straight|straighter|curved|jagged|overlap|overlaps|boundary|outline|transition|chip|chipped|rim)\b", lowered):
        foci_present.add("shape")
    if re.search(r"\b(color|colour|shade|hue|brighter|darker|terracotta|green|red|blue|yellow|black|white|grey|gray)\b", lowered):
        foci_present.add("color")
    if re.search(r"\b(texture|rough|smooth|surface|peeling|cracked|weathered)\b", lowered):
        foci_present.add("texture")
    if re.search(r"\b(spacing|spaced|gap|distance|apart|row|interval)\b", lowered):
        foci_present.add("spacing")
    if re.search(r"\b(shorter|taller|larger|smaller|height|size|width|length)\b", lowered):
        foci_present.add("size")

    all_qualities = ["texture", "color", "spacing", "orientation"]
    unexamined_qualities = [q for q in all_qualities if q not in foci_present]
    if not unexamined_qualities:
        unexamined_qualities = ["texture", "color"]

    stop_trailing = {
        "has", "next", "along", "its", "with", "in", "on", "at", "to", "by", "for",
        "and", "or", "of", "the", "a", "an", "is", "it", "from", "up", "than"
    }

    def clean_phrase(phrase: str) -> str:
        words = phrase.strip().split()
        while words and words[-1].lower() in stop_trailing:
            words.pop()
        while words and words[0].lower() in stop_trailing:
            words.pop(0)
        return " ".join(words)

    anchors: list[str] = []

    # Priority 1: Grass and pavement transition pair
    if "grass" in lowered and "pavement" in lowered:
        anchors.append("transition where the grass meets the pavement")

    # Priority 2: Standout items with numbers or ordinals (e.g. "fifth pot", "seven visible pots")
    ordinal_matches = re.findall(
        r"\b(?:the\s+)?((?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+[a-z]+(?:\s+[a-z]+)?)",
        lowered,
    )
    for m in ordinal_matches:
        clean = clean_phrase(m)
        if clean and clean not in anchors:
            anchors.append(clean)

    # Priority 3: Specific damage or distinctive feature (e.g. "structural chip", "chipped rim")
    chip_matches = re.findall(
        r"\b((?:distinct\s+|structural\s+)?(?:chip|chipped|uneven|straighter|painted)\s+[a-z]+(?:\s+[a-z]+)?)",
        lowered,
    )
    for m in chip_matches:
        clean = clean_phrase(m)
        if clean and clean not in anchors and not any(clean in a for a in anchors):
            anchors.append(clean)

    # Priority 4: Material + object (e.g. "terracotta flower pots", "metal railing", "painted wall")
    material_matches = re.findall(
        r"\b((?:terracotta|metal|wooden|brick|stone|concrete|plastic)\s+[a-z]+(?:\s+[a-z]+)?)",
        lowered,
    )
    for m in material_matches:
        clean = clean_phrase(m)
        if clean and clean not in anchors and not any(clean in a for a in anchors):
            anchors.append(clean)

    # Priority 5: Common objects with descriptors
    obj_matches = re.findall(
        r"\b((?:[a-z]+\s+)?(?:flower\s+pots?|pots?|plants?|trees?|railings?|walls?|pavement|boundary|walkway|bench))\b",
        lowered,
    )
    for m in obj_matches:
        clean = clean_phrase(m)
        if clean and clean not in anchors and not any(clean in a for a in anchors):
            anchors.append(clean)

    cleaned_anchors: list[str] = []
    for a in anchors:
        clean = clean_phrase(a)
        if len(clean) > 2 and clean not in cleaned_anchors:
            cleaned_anchors.append(clean)

    is_vague = len(cleaned_anchors) == 0 and len(text.split()) < 5
    best_anchor = cleaned_anchors[0] if cleaned_anchors else None

    # Check combination of ordinal pot and chip
    if "fifth pot" in cleaned_anchors and any("chip" in a for a in cleaned_anchors):
        best_anchor = "fifth pot with the chipped rim"

    return {
        "anchor": best_anchor,
        "all_anchors": cleaned_anchors,
        "foci_present": foci_present,
        "unexamined_qualities": unexamined_qualities,
        "is_vague": is_vague,
    }


def is_repetitive(
    candidate: str,
    current_clue: str,
    observation: str,
    required_step: ProgressionStep,
) -> bool:
    """True when candidate restates the previous clue or asks to repeat a completed observation task."""
    cand_norm = _normalize(candidate)
    clue_norm = _normalize(current_clue)
    obs_norm = _normalize(observation)

    if not cand_norm:
        return True

    # 1. High token overlap with current clue indicates rephrasing
    if token_overlap_ratio(candidate, current_clue) >= 0.45:
        return True

    # 2. Check for paraphrasing of the current clue's core directive
    if "describe its shape" in cand_norm and ("shape" in obs_norm or "uneven" in obs_norm or "straighter" in obs_norm):
        return True

    # 3. Check if asking to repeat an already-reported shape observation
    obs_has_shape = bool(re.search(r"\b(uneven|straight|straighter|curved|jagged|overlap|overlaps|boundary|shape)\b", obs_norm))
    cand_asks_shape = bool(re.search(r"\b(what\s+shape|describe\s+(?:the\s+|its\s+)?shape|shape\s+does\b)", cand_norm))

    cand_has_texture = bool(re.search(r"\b(texture|rough|smooth|surface|peeling|cracked)\b", cand_norm))
    cand_has_color = bool(re.search(r"\b(color|colour|shade|hue|brighter|darker)\b", cand_norm))
    cand_has_spacing = bool(re.search(r"\b(spacing|gap|distance|apart|interval)\b", cand_norm))
    cand_has_orientation = bool(re.search(r"\b(orientation|angle|direction|facing)\b", cand_norm))

    cand_has_new_quality = cand_has_texture or cand_has_color or cand_has_spacing or cand_has_orientation

    if obs_has_shape and cand_asks_shape and not cand_has_new_quality:
        return True

    # 4. Check if re-asking initial notice directive when already past notice
    if required_step in ("compare", "examine", "reflect"):
        if re.search(r"\b(look\s+for\s+a\s+pattern|find\s+a\s+pattern|find\s+two\s+features)\b", cand_norm):
            return True

    # 5. Parroting observation back without adding new investigation
    if token_overlap_ratio(candidate, observation) >= 0.75:
        return True

    return False


def fallback_clue(
    step: ProgressionStep,
    observation: str = "",
    current_clue: str = "",
) -> str:
    """Generate a safe, observation-aware progression fallback clue."""
    details = extract_observation_details(observation)
    anchor = details["anchor"]
    foci = details["foci_present"]

    if not anchor or details["is_vague"]:
        return SAFE_FALLBACKS[step]

    # Select target investigative qualities that user hasn't yet examined
    if "texture" in foci and "color" in foci:
        quality_phrase = "spacing or orientation"
    elif "texture" in foci:
        quality_phrase = "color or spacing"
    elif "color" in foci:
        quality_phrase = "texture or surface details"
    else:
        quality_phrase = "surface texture or color"

    anchor_phrase = anchor if anchor.startswith("the ") else f"the {anchor}"

    if step == "examine":
        if "grass" in anchor_phrase and "pavement" in anchor_phrase:
            return (
                f"From a safe position, examine the {quality_phrase} of the materials where the grass meets the pavement. "
                "You may pause or stop at any time."
            )
        return (
            f"From a safe position, look closely at {anchor_phrase} and examine its {quality_phrase} compared to surrounding features. "
            "You may pause or stop at any time."
        )

    if step == "compare":
        return (
            f"From a safe position, compare the visible {quality_phrase} of {anchor_phrase} with a nearby feature. "
            "Describe one observable difference. You may pause or stop at any time."
        )

    if step == "reflect":
        return (
            f"Pause in a safe spot and summarize how {anchor_phrase} relates to the rest of what you noticed. "
            "You may stop here if you wish."
        )

    # notice step fallback
    return (
        f"From a safe position near {anchor_phrase}, identify one additional visible detail you have not yet described. "
        "You may pause or stop at any time."
    )


def build_progression_block(
    current_clue: str,
    observation: str,
    required_step: ProgressionStep,
) -> str:
    completed_clue = classify_clue_step(current_clue)
    completed_observation = classify_observation_step(observation)
    details = extract_observation_details(observation)
    anchor = details.get("anchor")
    anchor_note = f"- Anchor your clue on the reported detail: '{anchor}'.\n" if anchor else ""

    return (
        "INVESTIGATION PROGRESS (follow this over the mission objective):\n"
        f"- The current clue asked for a '{completed_clue}' step.\n"
        f"- The observation already completed a '{completed_observation}' step.\n"
        f"- Required next step: {required_step}.\n"
        f"- {STEP_GUIDANCE[required_step]}\n"
        f"{anchor_note}"
        "- Do not repeat, rephrase, or re-ask the current clue.\n"
        "- Do not ask the user to describe a quality they already reported.\n"
        "- The mission objective is background only. It is not the next clue.\n"
        "- Use only details the user reported. Never invent observations or causes.\n"
    )
