import pytest

from app.db import chroma_client
from app.schemas.chunks import ChunkRecord


@pytest.fixture()
def chroma(tmp_path, monkeypatch):
    monkeypatch.setattr(chroma_client.settings, "chroma_persist_dir", str(tmp_path / "chroma"))
    monkeypatch.setattr(chroma_client, "_client", None)
    yield chroma_client
    monkeypatch.setattr(chroma_client, "_client", None)


def _chunk(chunk_id, embedding, page=1, chunk_index=0, document_name="doc.pdf", text="text") -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        collection_id="col1",
        document_name=document_name,
        page=page,
        chunk_index=chunk_index,
        text=text,
        embedding=embedding,
    )


def test_add_and_query_returns_nearest_first(chroma) -> None:
    chunks = [
        _chunk("c1", [1.0, 0.0, 0.0], text="alpha", chunk_index=0),
        _chunk("c2", [0.0, 1.0, 0.0], text="beta", chunk_index=1),
        _chunk("c3", [0.9, 0.1, 0.0], text="alpha-ish", chunk_index=2),
    ]
    chroma.add_chunks("col1", chunks)

    results = chroma.query_collection("col1", [1.0, 0.0, 0.0], n_results=2)

    assert [r.chunk_id for r in results] == ["c1", "c3"]
    assert results[0].document_name == "doc.pdf"
    assert results[0].page == 1


def test_query_empty_collection_returns_empty(chroma) -> None:
    assert chroma.query_collection("missing", [1.0, 0.0, 0.0], n_results=5) == []


def test_page_none_round_trips(chroma) -> None:
    chroma.add_chunks("col1", [_chunk("c1", [1.0, 0.0, 0.0], page=None, document_name="doc.docx")])

    results = chroma.query_collection("col1", [1.0, 0.0, 0.0], n_results=1)

    assert results[0].page is None


def test_delete_collection_removes_data(chroma) -> None:
    chroma.add_chunks("col1", [_chunk("c1", [1.0, 0.0, 0.0])])

    chroma.delete_collection("col1")

    assert chroma.query_collection("col1", [1.0, 0.0, 0.0], n_results=1) == []


def test_delete_nonexistent_collection_is_noop(chroma) -> None:
    chroma.delete_collection("does-not-exist")
