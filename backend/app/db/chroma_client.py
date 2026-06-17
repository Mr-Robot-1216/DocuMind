"""ChromaDB persistent client — one collection per DocuMind document collection.

Collections are created with cosine distance ("hnsw:space": "cosine")
rather than the Chroma default (squared L2). Cosine is scale-invariant,
which matters because nomic-embed-text does not guarantee unit-normalized
output vectors.
"""

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.errors import NotFoundError

from app.config import settings
from app.schemas.chunks import ChunkRecord, RetrievedChunk, page_from_str, page_to_str

_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection(collection_id: str) -> Collection:
    return get_client().get_or_create_collection(
        name=collection_id,
        metadata={"hnsw:space": "cosine"},
    )


def list_collections() -> list[str]:
    return [c.name for c in get_client().list_collections()]


def delete_collection(collection_id: str) -> None:
    try:
        get_client().delete_collection(name=collection_id)
    except (ValueError, NotFoundError):
        pass


def add_chunks(collection_id: str, chunks: list[ChunkRecord]) -> None:
    if not chunks:
        return
    collection = get_collection(collection_id)
    collection.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=[c.embedding for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "document_name": c.document_name,
                "page": page_to_str(c.page),
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ],
    )


def query_collection(collection_id: str, query_embedding: list[float], n_results: int) -> list[RetrievedChunk]:
    collection = get_collection(collection_id)
    count = collection.count()
    if count == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, count),
    )

    chunks = []
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                document_name=metadata["document_name"],
                page=page_from_str(metadata["page"]),
                chunk_index=metadata["chunk_index"],
                text=text,
                score=distance,
            )
        )
    return chunks
