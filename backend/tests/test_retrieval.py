from app.core import retrieval
from app.core.retrieval import reciprocal_rank_fusion
from app.schemas.chunks import RetrievedChunk


def _chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(chunk_id=chunk_id, document_name="doc.pdf", page=1, chunk_index=0, text=chunk_id, score=0.0)


def test_rrf_ranks_items_in_both_lists_higher() -> None:
    semantic = [_chunk("a"), _chunk("b"), _chunk("c")]
    keyword = [_chunk("c"), _chunk("a"), _chunk("d")]

    merged = reciprocal_rank_fusion([semantic, keyword], top_k=10)

    # "a" appears at rank 1 in semantic and rank 2 in keyword -> highest combined score
    assert merged[0].chunk_id == "a"
    ids = [c.chunk_id for c in merged]
    assert set(ids) == {"a", "b", "c", "d"}


def test_rrf_respects_top_k() -> None:
    semantic = [_chunk("a"), _chunk("b"), _chunk("c")]
    keyword: list[RetrievedChunk] = []

    merged = reciprocal_rank_fusion([semantic, keyword], top_k=2)

    assert len(merged) == 2
    assert [c.chunk_id for c in merged] == ["a", "b"]


def test_rrf_handles_empty_lists() -> None:
    assert reciprocal_rank_fusion([[], []], top_k=5) == []


async def test_hybrid_search_merges_semantic_and_keyword(monkeypatch) -> None:
    async def fake_embed_query(query, client=None):
        return [0.1, 0.2, 0.3]

    def fake_query_collection(collection_id, embedding, n_results):
        return [_chunk("a"), _chunk("b")]

    def fake_search_fts(collection_id, query, k):
        return [_chunk("b"), _chunk("c")]

    monkeypatch.setattr(retrieval, "embed_query", fake_embed_query)
    monkeypatch.setattr(retrieval.chroma_client, "query_collection", fake_query_collection)
    monkeypatch.setattr(retrieval.fts, "search_fts", fake_search_fts)

    results = await retrieval.hybrid_search("col1", "test query", top_k=3)

    ids = [c.chunk_id for c in results]
    assert ids[0] == "b"  # appears in both lists -> ranked first
    assert set(ids) == {"a", "b", "c"}
