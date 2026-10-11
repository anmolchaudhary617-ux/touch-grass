import json

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_create_mission(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return json.dumps({
            "title": "The Hidden History",
            "type": "investigate",
            "estimated_time": "20-30",
            "premise": "Something around you has changed over time.",
            "objective": "Find something old and compare it with something newer nearby.",
            "safety_brief": "Stay in public areas and stop if anything feels unsafe.",
            "first_clue": "Find something that looks older than its surroundings."
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post(
        "/api/missions",
        json={
            "adventure_type": "investigate",
            "duration": "20-30",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "The Hidden History"
    assert data["type"] == "investigate"
    assert data["estimated_time"] == "20-30"
    assert "objective" in data
    assert "first_clue" in data


def test_mission_generation_matches_adventure_type_mechanics(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return json.dumps({"title": "Custom Test Adventure"})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    # 1. Investigate must select comparison or mismatch
    resp_inv = client.post(
        "/api/missions",
        json={"adventure_type": "investigate", "duration": "20-30"},
    )
    assert resp_inv.status_code == 200
    inv_data = resp_inv.json()
    assert inv_data["type"] == "investigate"
    assert (
        "similarity and one difference" in inv_data["objective"].lower()
        or "visible difference between comparable features" in inv_data["objective"].lower()
    )

    # 2. Observe must select hidden_detail or pattern_break
    resp_obs = client.post(
        "/api/missions",
        json={"adventure_type": "observe", "duration": "10-15"},
    )
    assert resp_obs.status_code == 200
    obs_data = resp_obs.json()
    assert obs_data["type"] == "observe"
    assert (
        "notice one visible detail" in obs_data["objective"].lower()
        or "visual pattern and one observable variation" in obs_data["objective"].lower()
    )

    # 3. Discover must select boundary or pattern_break
    resp_disc = client.post(
        "/api/missions",
        json={"adventure_type": "discover", "duration": "30-45"},
    )
    assert resp_disc.status_code == 200
    disc_data = resp_disc.json()
    assert disc_data["type"] == "discover"
    assert (
        "visible transition between adjacent features" in disc_data["objective"].lower()
        or "visual pattern and one observable variation" in disc_data["objective"].lower()
    )


def test_mission_generation_duration_shapes_first_clue_pacing(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return json.dumps({"title": "Custom Test Adventure"})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    # Short duration (10-15)
    r1 = client.post("/api/missions", json={"adventure_type": "observe", "duration": "10-15"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["estimated_time"] == "10-15"
    assert "10-15 minute scan" in d1["first_clue"]

    # Extended duration (30-45)
    r2 = client.post("/api/missions", json={"adventure_type": "observe", "duration": "30-45"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["estimated_time"] == "30-45"
    assert "30-45 minute walk" in d2["first_clue"]


def test_mission_generation_alternates_concepts(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return json.dumps({"title": "Custom Test Adventure"})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    # Consecutive calls of same type alternate
    r1 = client.post("/api/missions", json={"adventure_type": "investigate", "duration": "20-30"})
    r2 = client.post("/api/missions", json={"adventure_type": "investigate", "duration": "20-30"})
    assert r1.json()["objective"] != r2.json()["objective"]

    # Interleaved switching preserves per-type alternation
    obs1 = client.post("/api/missions", json={"adventure_type": "observe", "duration": "20-30"})
    disc1 = client.post("/api/missions", json={"adventure_type": "discover", "duration": "20-30"})
    obs2 = client.post("/api/missions", json={"adventure_type": "observe", "duration": "20-30"})
    disc2 = client.post("/api/missions", json={"adventure_type": "discover", "duration": "20-30"})
    assert obs1.json()["objective"] != obs2.json()["objective"]
    assert disc1.json()["objective"] != disc2.json()["objective"]




def test_create_next_clue(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return json.dumps({
            "next_clue": (
                "Look more closely at the old railing and compare one "
                "visible sign of age with something newer nearby."
            )
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post(
        "/api/missions/next-clue",
        json={
            "title": "The Hidden History",
            "type": "investigate",
            "premise": "Something around you has changed over time.",
            "objective": (
                "Find something old and compare it with something newer nearby."
            ),
            "current_clue": (
                "Find something that looks older than its surroundings."
            ),
            "observation": (
                "I noticed an old metal railing with chipped paint "
                "next to a newer painted wall."
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "next_clue" in data
    assert data["next_clue"]


BOUNDARY_FIRST_CLUE = (
    "Look for two adjacent features that meet or transition. "
    "Observe their visible relationship from a safe position. "
    "If no clear transition is available, compare two nearby features."
)

SHAPE_OBSERVATION = (
    "The grass edge is uneven. In one section, the grass overlaps the "
    "pavement, while a nearby section has a much straighter boundary."
)

REPEATED_SHAPE_CLUE = "What shape does the grass edge take?"


def _next_clue_payload(**overrides):
    payload = {
        "title": "Where Things Meet",
        "type": "investigate",
        "premise": (
            "The transition between two adjacent features can reveal "
            "interesting differences in shape or appearance."
        ),
        "objective": (
            "Examine a visible transition between adjacent features. "
            "Describe its shape or appearance without guessing its cause."
        ),
        "current_clue": BOUNDARY_FIRST_CLUE,
        "observation": SHAPE_OBSERVATION,
    }
    payload.update(overrides)
    return payload


def test_next_clue_replaces_repeated_observation_task(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        assert "Required next step: examine" in prompt
        assert "follow this over the mission objective" in prompt
        return json.dumps({"next_clue": REPEATED_SHAPE_CLUE})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post("/api/missions/next-clue", json=_next_clue_payload())

    assert response.status_code == 200
    data = response.json()
    assert list(data.keys()) == ["next_clue"]
    assert isinstance(data["next_clue"], str)
    assert data["next_clue"]
    assert "shape" not in data["next_clue"].lower()
    assert data["next_clue"] != REPEATED_SHAPE_CLUE
    assert "pause or stop" in data["next_clue"].lower()


def test_next_clue_rejects_paraphrase_of_current_clue(monkeypatch):
    paraphrased = (
        "Observe the transition edge between the grass and pavement "
        "and describe its shape."
    )

    async def fake_generate(prompt: str) -> str:
        return json.dumps({"next_clue": paraphrased})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post("/api/missions/next-clue", json=_next_clue_payload())

    assert response.status_code == 200
    clue = response.json()["next_clue"]
    assert clue != paraphrased
    assert "describe its shape" not in clue.lower()


def test_next_clue_keeps_valid_progressing_json(monkeypatch):
    progressing = (
        "From where you stand, compare the color of the grass with the "
        "pavement beside it. You may pause or stop at any time."
    )

    async def fake_generate(prompt: str) -> str:
        return json.dumps({"next_clue": progressing})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    # A notice-level observation should advance to compare, matching this clue.
    response = client.post(
        "/api/missions/next-clue",
        json=_next_clue_payload(
            observation="I noticed a grass edge next to the pavement.",
        ),
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"next_clue": progressing}


def test_next_clue_invalid_json_returns_502(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return "not json at all"

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post("/api/missions/next-clue", json=_next_clue_payload())

    assert response.status_code == 502
    assert "Invalid JSON" in response.json()["detail"]


FLOWER_PAYLOAD = {
    "title": "The Pattern Detective",
    "type": "investigate",
    "premise": "Repeated shapes, spacing, or arrangements can make small variations easier to notice.",
    "objective": "Identify a naturally occurring visual pattern and one observable variation. If no clear pattern exists, compare two visible features instead.",
    "current_clue": (
        "Look for a pattern already present in your surroundings. Do not arrange or move anything. "
        "If no clear pattern is visible, compare two features instead."
    ),
    "observation": (
        "A row of evenly spaced terracotta flower pots lining the edge of a public plaza walkway. "
        "Out of the seven visible pots, the fifth pot has a distinct structural chip along its upper rim, "
        "and the plant inside it is slightly shorter than the rest."
    ),
}


def test_flower_pot_observation_fallback_is_contextual_not_generic(monkeypatch):
    # Simulate model returning repetitive text
    async def fake_generate(prompt: str) -> str:
        assert "Required next step: examine" in prompt
        assert "fifth pot" in prompt
        return json.dumps({
            "next_clue": "Look for a pattern already present in the terracotta flower pots."
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post("/api/missions/next-clue", json=FLOWER_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    clue = data["next_clue"]
    # Must use a reported detail from observation
    assert "fifth pot" in clue.lower()
    # Must NOT use the old disconnected generic fallback string
    assert "look at a different visible quality in the same scene" not in clue.lower()
    # Must NOT ask about shape again
    assert "shape" not in clue.lower()
    # Must include safe exploration reminder
    assert "pause or stop" in clue.lower()


def test_flower_pot_observation_keeps_valid_model_clue(monkeypatch):
    valid_clue = (
        "Look closely at the fifth pot with the chipped rim and check if the "
        "texture of the chip differs from the smooth terracotta of the other pots."
    )

    async def fake_generate(prompt: str) -> str:
        return json.dumps({"next_clue": valid_clue})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post("/api/missions/next-clue", json=FLOWER_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["next_clue"] == valid_clue


def test_later_turn_advances_from_previous_clue(monkeypatch):
    captured_prompts = []

    async def fake_generate(prompt: str) -> str:
        captured_prompts.append(prompt)
        return json.dumps({
            "next_clue": "Pause and summarize the details you noticed."
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    # Turn 2: current clue is already an examine clue from Turn 1
    turn_2_payload = {
        "title": "The Pattern Detective",
        "type": "investigate",
        "premise": "Repeated shapes, spacing, or arrangements can make small variations easier to notice.",
        "objective": "Identify a naturally occurring visual pattern and one observable variation.",
        "current_clue": (
            "From a safe position, look closely at the fifth pot and examine its texture "
            "compared to surrounding features. You may pause or stop at any time."
        ),
        "observation": "The texture of the chipped area feels rougher than the glaze.",
    }

    response = client.post("/api/missions/next-clue", json=turn_2_payload)

    assert response.status_code == 200
    assert len(captured_prompts) == 1
    # Because current_clue was examine, next step should advance to reflect
    assert "Required next step: reflect" in captured_prompts[0]


def test_flexible_llm_json_key_handling(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        # LLM uses 'clue' instead of 'next_clue'
        return json.dumps({
            "clue": "Notice whether any other plant in the row has different foliage."
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post("/api/missions/next-clue", json=FLOWER_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["next_clue"] == "Notice whether any other plant in the row has different foliage."


def test_llm_answer_key_and_sentence_key_handling(monkeypatch):
    # Test 'answer' key
    async def fake_generate_answer(prompt: str) -> str:
        return json.dumps({
            "answer": "Compare the spacing between the two lower branches."
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate_answer,
    )

    response = client.post("/api/missions/next-clue", json=FLOWER_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["next_clue"] == "Compare the spacing between the two lower branches."

    # Test sentence as dictionary key
    async def fake_generate_sentence_key(prompt: str) -> str:
        return json.dumps({
            "Inspect the bark closely and notice any color patterns.": ""
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate_sentence_key,
    )

    response = client.post("/api/missions/next-clue", json=FLOWER_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["next_clue"] == "Inspect the bark closely and notice any color patterns."


def test_observation_count_prevents_premature_reflection(monkeypatch):
    captured_prompts = []

    async def fake_generate(prompt: str) -> str:
        captured_prompts.append(prompt)
        return json.dumps({
            "next_clue": "Look closely at the bark texture and notice variations."
        })

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    # Observation count 3 with an examine current_clue
    examine_payload = {
        "title": "The Curious Tree",
        "type": "observe",
        "premise": "Explore a safe outdoor area.",
        "objective": "Notice details about the tree.",
        "current_clue": "From a safe position, look closely and examine the texture.",
        "observation": "The bark looks rough and darker on one side.",
        "observation_count": 3,
    }

    response = client.post("/api/missions/next-clue", json=examine_payload)
    assert response.status_code == 200
    # Must be capped at examine, NOT reflect
    assert "Required next step: examine" in captured_prompts[0]
    assert "Required next step: reflect" not in captured_prompts[0]

    # When observation_count is 4+, reflection is permitted
    examine_payload["observation_count"] = 4
    response = client.post("/api/missions/next-clue", json=examine_payload)
    assert response.status_code == 200
    assert "Required next step: reflect" in captured_prompts[1]


def test_empty_or_vague_observation_handled_safely(monkeypatch):
    async def fake_generate(prompt: str) -> str:
        return json.dumps({"next_clue": ""})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    response = client.post(
        "/api/missions/next-clue",
        json=_next_clue_payload(observation="I just walked around."),
    )

    assert response.status_code == 200
    clue = response.json()["next_clue"]
    assert clue
    assert "pause or stop" in clue.lower()
    assert "safe" in clue.lower()


def test_first_clue_contains_actionable_targets_and_fallbacks_for_all_concepts():
    """Verify that every concept blueprint has concrete targets, observation tasks, and fallbacks."""
    from app.services.mission_service import MISSION_BLUEPRINTS

    expected_concepts = ["comparison", "hidden_detail", "mismatch", "pattern_break", "boundary"]
    assert set(MISSION_BLUEPRINTS.keys()) == set(expected_concepts)

    for concept_name in expected_concepts:
        bp = MISSION_BLUEPRINTS[concept_name]
        assert "first_clues" in bp
        for duration in ["10-15", "20-30", "30-45"]:
            clue = bp["first_clues"][duration]
            # 1. Concrete target guidance (conditional, e.g. "such as")
            assert "such as" in clue.lower()
            # 2. Clear fallback condition ("if no" or "if the" or "if suitable" or "if paired")
            assert "if " in clue.lower() and any(
                term in clue.lower() for term in ["instead", "choose", "compare", "inspect", "identify", "observe"]
            )
            # 3. Safety reminder preserved
            assert "safe" in clue.lower()
            # 4. Actionable task phrasing (not just "choose two features")
            assert "choose two features visible" not in clue.lower()


def test_first_clue_location_independence():
    """Verify that clues do not claim specific objects definitively exist nearby."""
    from app.services.mission_service import MISSION_BLUEPRINTS

    for concept, bp in MISSION_BLUEPRINTS.items():
        for duration, clue in bp["first_clues"].items():
            # Targets must be conditional examples, preceded by "such as"
            assert "such as" in clue
            # Must provide fallback alternative
            assert "instead" in clue.lower() or "if " in clue.lower()
            # Clues must never require touching unknown objects
            assert "touch" in clue.lower() and ("not touch" in clue.lower() or "do not" in clue.lower() or "without touching" in clue.lower())


def test_first_clue_duration_differentiation(monkeypatch):
    """Verify that first clues scale tasks appropriately across duration brackets."""
    async def fake_generate(prompt: str) -> str:
        return json.dumps({"title": "Pacing Test Title"})

    monkeypatch.setattr(
        "app.services.mission_service.generate",
        fake_generate,
    )

    from app.services.mission_service import MISSION_BLUEPRINTS

    for adv_type, concepts in [
        ("investigate", ["comparison", "mismatch"]),
        ("observe", ["hidden_detail", "pattern_break"]),
        ("discover", ["boundary", "pattern_break"]),
    ]:
        resp_10 = client.post("/api/missions", json={"adventure_type": adv_type, "duration": "10-15"}).json()
        resp_20 = client.post("/api/missions", json={"adventure_type": adv_type, "duration": "20-30"}).json()
        resp_30 = client.post("/api/missions", json={"adventure_type": adv_type, "duration": "30-45"}).json()

        # Each duration has distinctive pacing language
        assert "10-15 minute scan" in resp_10["first_clue"]
        assert "20-30 minute exploration" in resp_20["first_clue"]
        assert "30-45 minute walk" in resp_30["first_clue"]

        # Ensure clue text differs substantially across durations
        assert resp_10["first_clue"] != resp_20["first_clue"]
        assert resp_20["first_clue"] != resp_30["first_clue"]
