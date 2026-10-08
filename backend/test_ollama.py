import asyncio

from app.services.ollama import generate


async def main():
    response = await generate(
        "Give me one short outdoor observation challenge for a person."
    )

    print("\nAI RESPONSE:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())