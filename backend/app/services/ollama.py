import httpx


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"


async def generate(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": "low",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["response"]