"""Document ingestion pipeline: parse -> chunk -> embed -> store (Chroma + FTS5)."""

import uuid
from typing import BinaryIO

from app.config import settings
from app.core.chunking import chunk_text
from app.core.embeddings import embed_texts
from app.core.parsing import parse_document
from app.db import chroma_client, fts
from app.schemas.chunks import ChunkRecord


async def ingest_document(collection_id: str, file: BinaryIO, filename: str) -> int:
    pages = parse_document(file, filename)

    records: list[ChunkRecord] = []
    chunk_index = 0
    for page in pages:
        for chunk in chunk_text(page.text, settings.chunk_size, settings.chunk_overlap):
            records.append(
                ChunkRecord(
                    chunk_id=uuid.uuid4().hex,
                    collection_id=collection_id,
                    document_name=filename,
                    page=page.page,
                    chunk_index=chunk_index,
                    text=chunk,
                )
            )
            chunk_index += 1

    if not records:
        return 0

    embeddings = await embed_texts([record.text for record in records])
    for record, embedding in zip(records, embeddings):
        record.embedding = embedding

    chroma_client.add_chunks(collection_id, records)
    fts.index_chunks(records)

    return len(records)
