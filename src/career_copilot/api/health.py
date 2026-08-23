from fastapi import APIRouter

from career_copilot.services.llm import OllamaClient

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    client = OllamaClient()
    ollama_ok = await client.health_check()
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "unreachable",
    }
