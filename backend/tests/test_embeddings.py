import json

import httpx

from app.config import settings
from app.core.embeddings import embed_query, embed_texts


def _mock_client(captured: dict) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(base_url=settings.ollama_base_url, transport=transport)


async def test_embed_texts_calls_ollama_embed_endpoint() -> None:
    captured: dict = {}
    client = _mock_client(captured)

    result = await embed_texts(["a", "b"], client=client)

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"].endswith("/api/embed")
    assert captured["body"] == {"model": settings.embed_model, "input": ["a", "b"]}


async def test_embed_texts_empty_list_skips_request() -> None:
    assert await embed_texts([]) == []


async def test_embed_query_returns_single_vector() -> None:
    captured: dict = {}
    client = _mock_client(captured)

    result = await embed_query("hello", client=client)

    assert result == [0.1, 0.2]
    assert captured["body"]["input"] == ["hello"]
