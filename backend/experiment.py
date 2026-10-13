
import time
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"

# Use different domains deliberately rather than relying on random chance.
DOMAINS = [
    "Shadows and light",
    "Acoustics and sound",
    "Living things and nature",
    "Symbols and visual communication",
    "Shapes and spatial arrangement",
]

CONCEPTS = [
    "comparison",
    "hidden detail",
    "mismatch",
    "pattern break",
    "boundary",
]


def test_ideation(domain: str, concept: str) -> None:
    prompt = (
        "You are a creative designer of real-world outdoor investigations.\n"
        f"Physical domain: {domain}\n"
        f"Investigation concept: {concept}\n"
        "Invent one intriguing, practical investigation idea that combines "
        "this domain and concept.\n"
        "Describe the core mechanic in two or three sentences. Explain "
        "what the player would compare, notice, or investigate.\n"
        "Do not write a complete mission, title, safety brief, or JSON.\n"
        "Do not assume a particular location or require a rare object.\n"
        "Do not infer hidden causes or historical events from appearance alone.\n"
        "Return plain text only."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
        },
    }

    print("=" * 65)
    print(f"Domain: {domain}")
    print(f"Concept: {concept}")

    try:
        start = time.perf_counter()

        response = httpx.post(
            OLLAMA_URL,
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()

        result = response.json()
        elapsed = time.perf_counter() - start

        print(f"Time: {elapsed:.2f} seconds")
        print("Idea:")
        print(result.get("response", "").strip())

    except (httpx.HTTPError, ValueError) as exc:
        print(f"Experiment failed: {exc}")


def main() -> None:
    # Rotate concepts so we can test all five concepts across five domains.
    for index, domain in enumerate(DOMAINS):
        concept = CONCEPTS[index]
        test_ideation(domain, concept)


if __name__ == "__main__":
    main()
