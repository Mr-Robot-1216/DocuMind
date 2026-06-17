"""Embedding client for nomic-embed-text via Ollama's /api/embed endpoint."""

import httpx

from app.config import settings


async def embed_texts(texts: list[str], client: httpx.AsyncClient | None = None) -> list[list[float]]:
    if not texts:
        return []

    owns_client = client is None
    client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0)
    try:
        response = await client.post(
            "/api/embed",
            json={"model": settings.embed_model, "input": texts},
        )
        response.raise_for_status()
        return response.json()["embeddings"]
    finally:
        if owns_client:
            await client.aclose()


async def embed_query(text: str, client: httpx.AsyncClient | None = None) -> list[float]:
    embeddings = await embed_texts([text], client=client)
    return embeddings[0]
