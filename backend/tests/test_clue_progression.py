from app.services.clue_progression import (
    fallback_clue,
    is_repetitive,
    select_next_step,
)


FIRST_CLUE = (
    "Look for two adjacent features that meet or transition. "
    "Observe their visible relationship from a safe position."
)

COMPARISON_OBSERVATION = (
    "The grass edge is uneven. In one section, the grass overlaps the "
    "pavement, while a nearby section has a much straighter boundary."
)


def test_select_next_step_advances_past_completed_comparison():
    step = select_next_step(FIRST_CLUE, COMPARISON_OBSERVATION)
    assert step == "examine"


def test_select_next_step_asks_to_compare_after_a_simple_notice():
    step = select_next_step(
        FIRST_CLUE,
        "I noticed a grass edge next to the pavement.",
    )
    assert step == "compare"


def test_repeated_shape_question_is_repetitive():
    required = select_next_step(FIRST_CLUE, COMPARISON_OBSERVATION)
    assert is_repetitive(
        "What shape does the grass edge take?",
        FIRST_CLUE,
        COMPARISON_OBSERVATION,
        required,
    )
    assert is_repetitive(
        "Look at the transition point and describe its shape.",
        FIRST_CLUE,
        COMPARISON_OBSERVATION,
        required,
    )


def test_advancing_examine_clue_is_not_flagged_without_step_keywords():
    required = select_next_step(FIRST_CLUE, COMPARISON_OBSERVATION)
    assert required == "examine"

    clue = "Inspect whether a nearby surface looks smooth or rough."
    forbidden = (
        "examine",
        "texture",
        "color",
        "spacing",
        "orientation",
        "different",
        "relationship",
        "characteristic",
    )
    lowered = clue.lower()
    assert all(word not in lowered for word in forbidden)
    assert not is_repetitive(clue, FIRST_CLUE, COMPARISON_OBSERVATION, required)


def test_fallback_for_examine_is_safe_and_not_a_shape_paraphrase():
    clue = fallback_clue("examine")
    assert "shape" not in clue.lower()
    assert "pause or stop" in clue.lower()
    assert not is_repetitive(clue, FIRST_CLUE, COMPARISON_OBSERVATION, "examine")


FLOWER_CLUE = (
    "Look for a pattern already present in your surroundings. "
    "Do not arrange or move anything. If no clear pattern is visible, "
    "compare two features instead."
)

FLOWER_OBSERVATION = (
    "A row of evenly spaced terracotta flower pots lining the edge of a public plaza walkway. "
    "Out of the seven visible pots, the fifth pot has a distinct structural chip along its upper rim, "
    "and the plant inside it is slightly shorter than the rest."
)


def test_flower_pot_observation_advances_to_examine():
    step = select_next_step(FLOWER_CLUE, FLOWER_OBSERVATION)
    assert step == "examine"


def test_flower_pot_fallback_uses_observation_detail_and_advances():
    clue = fallback_clue("examine", observation=FLOWER_OBSERVATION, current_clue=FLOWER_CLUE)
    # 1. Must use a detail actually reported
    assert "fifth pot" in clue.lower()
    # 2. Must not use generic detached phrasing
    assert "look at a different visible quality in the same scene" not in clue.lower()
    # 3. Must not ask about shape
    assert "shape" not in clue.lower()
    # 4. Must ask for an unexamined quality
    assert "texture" in clue.lower() or "color" in clue.lower()
    # 5. Must include safety reminder
    assert "pause or stop" in clue.lower()
    assert "safe" in clue.lower()
    # 6. Must not be flagged as repetitive
    assert not is_repetitive(clue, FLOWER_CLUE, FLOWER_OBSERVATION, "examine")


def test_valid_model_clue_for_flower_pot_is_preserved():
    valid_clue = (
        "Look closely at the fifth pot with the chipped rim and check if the "
        "texture of the chip differs from the smooth parts of the terracotta."
    )
    assert not is_repetitive(valid_clue, FLOWER_CLUE, FLOWER_OBSERVATION, "examine")


def test_repetitive_first_clue_rephrasing_for_flower_pot_is_rejected():
    repetitive_clue = "Look for a pattern already present in the terracotta flower pots."
    assert is_repetitive(repetitive_clue, FLOWER_CLUE, FLOWER_OBSERVATION, "examine")


def test_empty_and_vague_observation_fallback_is_safe():
    empty_clue = fallback_clue("examine", observation="")
    assert "pause or stop" in empty_clue.lower()
    assert "safe" in empty_clue.lower()

    vague_clue = fallback_clue("examine", observation="Just walked around.")
    assert "pause or stop" in vague_clue.lower()
    assert "safe" in vague_clue.lower()


def test_initial_clues_for_all_five_concepts_classify_as_notice():
    """Verify that initial clues for all concepts are treated as notice phase, not completed examine/compare steps."""
    from app.services.clue_progression import classify_clue_step, is_initial_clue
    from app.services.mission_service import MISSION_BLUEPRINTS

    concepts = ["comparison", "hidden_detail", "mismatch", "pattern_break", "boundary"]
    for concept in concepts:
        bp = MISSION_BLUEPRINTS[concept]
        for duration, clue in bp["first_clues"].items():
            assert is_initial_clue(clue), f"{concept} {duration} should be recognized as an initial clue"
            classified = classify_clue_step(clue)
            assert classified == "notice", (
                f"{concept} {duration} contains descriptive wording but must classify as 'notice' "
                f"at the start of a mission, not '{classified}'"
            )


def test_initial_clue_progression_advances_properly_without_skipping_steps():
    """Verify that responding to an initial clue with a simple notice advances to compare, and a comparison advances to examine."""
    from app.services.clue_progression import select_next_step
    from app.services.mission_service import MISSION_BLUEPRINTS

    simple_obs = "I noticed an ordinary wooden bench near the pathway."
    comparison_obs = (
        "I compared two trees. The left tree is tall and straight, "
        "while the right tree has a curved trunk and rougher bark."
    )

    concepts = ["comparison", "hidden_detail", "mismatch", "pattern_break", "boundary"]
    for concept in concepts:
        bp = MISSION_BLUEPRINTS[concept]
        for duration, clue in bp["first_clues"].items():
            # A simple observation must advance to compare, never jump directly to reflect
            next_after_simple = select_next_step(clue, simple_obs)
            assert next_after_simple == "compare", (
                f"{concept} {duration}: expected 'compare' after simple notice, got '{next_after_simple}'"
            )

            # A comparison observation must advance to examine, never jump directly to reflect
            next_after_comp = select_next_step(clue, comparison_obs)
            assert next_after_comp == "examine", (
                f"{concept} {duration}: expected 'examine' after comparison observation, got '{next_after_comp}'"
            )


def test_later_examine_clue_still_advances_to_reflect():
    """Verify that an actual subsequent examine clue in later turns advances to reflect."""
    from app.services.clue_progression import classify_clue_step, select_next_step

    later_examine_clue = (
        "From a safe position, look closely at the fifth pot and examine its texture "
        "compared to surrounding features. You may pause or stop at any time."
    )
    obs = "The texture of the chipped area feels rougher than the glaze."

    classified = classify_clue_step(later_examine_clue)
    assert classified == "examine"
    next_step = select_next_step(later_examine_clue, obs)
    assert next_step == "reflect"
