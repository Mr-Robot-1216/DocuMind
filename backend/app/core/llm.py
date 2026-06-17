"""Streaming chat client for qwen3:8b via Ollama's /api/chat endpoint.

think=False is set explicitly: qwen3 is a hybrid-reasoning model that, by
default, emits a long internal "thinking" trace before any visible output
(20-30s of silence on this hardware even for trivial prompts) — exactly the
streaming-UX problem CLAUDE.md flagged for DeepSeek-R1. Disabling it trades
away chain-of-thought reasoning for responsiveness, the right call for a
chat-over-documents UI where answers should start streaming immediately.
"""

import json
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.schemas.chunks import RetrievedChunk

SYSTEM_PROMPT_TEMPLATE = """You are DocuMind, a helpful assistant that answers questions using ONLY the \
provided context from the user's documents.

- If the answer is not contained in the context, say you don't know — do not make things up.
- Cite sources inline using the format [document_name, p. page] after the relevant sentence.

Context:
{context}
"""


def build_messages(history: list[dict], question: str, chunks: list[RetrievedChunk]) -> list[dict]:
    context = "\n\n".join(_format_chunk(c) for c in chunks)
    system = SYSTEM_PROMPT_TEMPLATE.format(context=context or "(no relevant context found)")
    return [{"role": "system", "content": system}, *history, {"role": "user", "content": question}]


def _format_chunk(chunk: RetrievedChunk) -> str:
    location = f"p. {chunk.page}" if chunk.page is not None else "source"
    return f"[{chunk.document_name}, {location}]\n{chunk.text}"


async def stream_chat(messages: list[dict], client: httpx.AsyncClient | None = None) -> AsyncIterator[str]:
    owns_client = client is None
    client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=None)
    try:
        async with client.stream(
            "POST",
            "/api/chat",
            json={"model": settings.chat_model, "messages": messages, "stream": True, "think": False},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
                if data.get("done"):
                    break
    finally:
        if owns_client:
            await client.aclose()
