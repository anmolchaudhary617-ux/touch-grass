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