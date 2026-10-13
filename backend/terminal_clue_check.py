from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

mission = {
    "title": "The Curious Tree",
    "type": "observe",
    "premise": "Explore a safe outdoor area and investigate an interesting tree.",
    "objective": "Notice details about the tree and how it differs from its surroundings.",
    "current_clue": "Look closely at the tree and notice its visible features.",
}

observations = [
    "The bark looks rough and the lower branches are uneven.",
    "The bark on one side looks darker than the other side.",
    "The lower branches are farther apart on the left side.",
    "The leaves near the top appear smaller than the leaves below.",
    "The tree has several unusual patterns in its bark.",
]

print("\n=== TOUCH GRASS: NEXT-CLUE API TEST ===\n")

previous_clue = mission["current_clue"]
successful = 0
returned_clues = []

for count, observation in enumerate(observations, start=1):
    payload = {
        **mission,
        "current_clue": previous_clue,
        "observation": observation,
        "observation_count": count,
    }

    print(f"\n--- Observation {count} ---")
    print("Input:", observation)

    try:
        response = client.post("/api/missions/next-clue", json=payload)
        print("HTTP status:", response.status_code)

        if response.status_code != 200:
            print("ERROR:", response.text)
            continue

        clue = response.json().get("next_clue", "").strip()

        if not clue:
            print("FAIL: next_clue is empty or missing.")
            continue

        print("Next clue:", clue)

        if clue.casefold() in {item.casefold() for item in returned_clues}:
            print("WARNING: Exact repeat, ignoring capitalization.")
        else:
            print("PASS: Non-empty clue; no exact repeat.")

        returned_clues.append(clue)
        previous_clue = clue
        successful += 1

    except Exception as exc:
        print("ERROR:", repr(exc))

print("\n=== SUMMARY ===")
print(f"Successful API responses: {successful}/{len(observations)}")

print("\n=== REQUEST VALIDATION TEST ===")
invalid_payload = {
    **mission,
    "current_clue": "Look at the tree.",
    "observation": "The bark is rough.",
    "observation_count": 0,
}

response = client.post("/api/missions/next-clue", json=invalid_payload)
print("HTTP status for observation_count=0:", response.status_code)

if response.status_code == 422:
    print("PASS: Invalid observation count rejected.")
else:
    print("CHECK: Expected HTTP 422.")
    print(response.text)
