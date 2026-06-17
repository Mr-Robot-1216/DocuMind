"""Hybrid retrieval: ChromaDB semantic search + SQLite FTS5 keyword search,
merged with Reciprocal Rank Fusion (RRF).

Why RRF: semantic search alone misses exact-match terms (acronyms, names,
part numbers) that keyword search catches, and vice versa for paraphrased
queries. RRF combines two differently-scaled ranking signals (cosine
distance vs. BM25) without needing to normalize them onto a shared scale —
it only looks at each result's *rank* within its own list.
"""

import asyncio

from app.core.embeddings import embed_query
from app.db import chroma_client, fts
from app.schemas.chunks import RetrievedChunk

RRF_K = 60


async def hybrid_search(
    collection_id: str,
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
) -> list[RetrievedChunk]:
    query_embedding = await embed_query(query)

    semantic_results, keyword_results = await asyncio.gather(
        asyncio.to_thread(chroma_client.query_collection, collection_id, query_embedding, candidate_k),
        asyncio.to_thread(fts.search_fts, collection_id, query, candidate_k),
    )

    return reciprocal_rank_fusion([semantic_results, keyword_results], top_k)


def reciprocal_rank_fusion(result_lists: list[list[RetrievedChunk]], top_k: int) -> list[RetrievedChunk]:
    scores: dict[str, float] = {}
    chunks: dict[str, RetrievedChunk] = {}

    for results in result_lists:
        for rank, chunk in enumerate(results, start=1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (RRF_K + rank)
            chunks.setdefault(chunk.chunk_id, chunk)

    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)

    merged = []
    for chunk_id in ranked_ids[:top_k]:
        chunk = chunks[chunk_id]
        chunk.score = scores[chunk_id]
        merged.append(chunk)
    return merged
