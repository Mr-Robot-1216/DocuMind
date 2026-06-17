from app.schemas.chunks import RetrievedChunk


def extract_cited_sources(chunks: list[RetrievedChunk], response_text: str) -> list[dict]:
    """Filter retrieved chunks down to the ones the model actually cited.

    The system prompt instructs the model to cite sources inline as
    "[document_name, p. page]"; chunks whose document name never appears
    in the response weren't used to answer the question (e.g. a generic
    "you're welcome!" reply shouldn't carry citation badges).
    """
    seen: set[tuple[str, int | str | None]] = set()
    sources = []
    for chunk in chunks:
        key = (chunk.document_name, chunk.page)
        if key in seen or f"[{chunk.document_name}" not in response_text:
            continue
        seen.add(key)
        sources.append({"document_name": chunk.document_name, "page": chunk.page})
    return sources
