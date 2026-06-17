import json

import httpx

from app.core.llm import build_messages, stream_chat
from app.schemas.chunks import RetrievedChunk


def test_build_messages_includes_context_and_citations() -> None:
    chunks = [
        RetrievedChunk(chunk_id="c1", document_name="report.pdf", page=3, chunk_index=0, text="Revenue grew 20%.", score=0.1),
        RetrievedChunk(chunk_id="c2", document_name="notes.docx", page=None, chunk_index=1, text="No page info here.", score=0.2),
    ]

    messages = build_messages(history=[], question="How did revenue change?", chunks=chunks)

    assert messages[0]["role"] == "system"
    assert "[report.pdf, p. 3]" in messages[0]["content"]
    assert "[notes.docx, source]" in messages[0]["content"]
    assert "Revenue grew 20%." in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "How did revenue change?"}


def test_build_messages_handles_no_chunks() -> None:
    messages = build_messages(history=[], question="hi", chunks=[])
    assert "(no relevant context found)" in messages[0]["content"]


def test_build_messages_preserves_history() -> None:
    history = [{"role": "user", "content": "prev question"}, {"role": "assistant", "content": "prev answer"}]
    messages = build_messages(history=history, question="follow up", chunks=[])

    assert messages[1:3] == history
    assert messages[-1] == {"role": "user", "content": "follow up"}


async def test_stream_chat_yields_content_tokens() -> None:
    lines = [
        {"message": {"content": "Hel"}, "done": False},
        {"message": {"content": "lo"}, "done": False},
        {"message": {"content": ""}, "done": True},
    ]
    body = "\n".join(json.dumps(line) for line in lines)

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["think"] is False
        assert payload["stream"] is True
        return httpx.Response(200, content=body)

    from app.config import settings

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url=settings.ollama_base_url, transport=transport, timeout=None)

    tokens = [token async for token in stream_chat([{"role": "user", "content": "hi"}], client=client)]

    assert tokens == ["Hel", "lo"]
