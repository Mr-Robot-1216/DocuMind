import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.citations import extract_cited_sources
from app.core.llm import build_messages, stream_chat
from app.core.retrieval import hybrid_search
from app.db import history

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    collection_id: str
    message: str


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    if history.get_collection(request.collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    chunks = await hybrid_search(request.collection_id, request.message)

    history_messages = [
        {"role": m["role"], "content": m["content"]} for m in history.get_messages(request.collection_id)
    ]
    messages = build_messages(history_messages, request.message, chunks)

    history.add_message(request.collection_id, "user", request.message)

    async def event_stream():
        full_response = ""
        async for token in stream_chat(messages):
            full_response += token
            yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        sources = extract_cited_sources(chunks, full_response)
        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

        history.add_message(request.collection_id, "assistant", full_response)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
