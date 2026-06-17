from app.core.citations import extract_cited_sources
from app.schemas.chunks import RetrievedChunk


def _chunk(document_name, page, chunk_index=0, score=1.0) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{document_name}-{chunk_index}",
        document_name=document_name,
        page=page,
        chunk_index=chunk_index,
        text="text",
        score=score,
    )


def test_only_cited_documents_are_returned() -> None:
    chunks = [_chunk("resume.pdf", 1), _chunk("notes.docx", None)]
    response = "Your skills are listed [resume.pdf, p. 1]."

    assert extract_cited_sources(chunks, response) == [{"document_name": "resume.pdf", "page": 1}]


def test_no_citations_returns_empty() -> None:
    chunks = [_chunk("resume.pdf", 1)]
    response = "You're welcome! Let me know if you need anything else."

    assert extract_cited_sources(chunks, response) == []


def test_duplicate_citations_are_deduped() -> None:
    chunks = [_chunk("resume.pdf", 2, chunk_index=0), _chunk("resume.pdf", 2, chunk_index=1)]
    response = "Skills [resume.pdf, p. 2] and experience [resume.pdf, p. 2]."

    assert extract_cited_sources(chunks, response) == [{"document_name": "resume.pdf", "page": 2}]
