"""SQLite FTS5 keyword index — the keyword half of hybrid retrieval.

Reuses the same SQLite database as chat history (settings.sqlite_db_path)
so the project doesn't need a separate keyword search service.
"""

import re
import sqlite3
from pathlib import Path

from app.config import settings
from app.schemas.chunks import ChunkRecord, RetrievedChunk, page_from_str, page_to_str


def _connect() -> sqlite3.Connection:
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db() -> None:
    with _connect() as con:
        con.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                collection_id UNINDEXED,
                document_name UNINDEXED,
                page UNINDEXED,
                chunk_index UNINDEXED,
                text
            )
            """
        )


def index_chunks(chunks: list[ChunkRecord]) -> None:
    if not chunks:
        return
    with _connect() as con:
        con.executemany(
            """
            INSERT INTO chunks_fts (chunk_id, collection_id, document_name, page, chunk_index, text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (c.chunk_id, c.collection_id, c.document_name, page_to_str(c.page), c.chunk_index, c.text)
                for c in chunks
            ],
        )


def delete_collection_chunks(collection_id: str) -> None:
    with _connect() as con:
        con.execute("DELETE FROM chunks_fts WHERE collection_id = ?", (collection_id,))


def search_fts(collection_id: str, query: str, k: int) -> list[RetrievedChunk]:
    match_query = _build_match_query(query)
    if not match_query:
        return []

    with _connect() as con:
        rows = con.execute(
            """
            SELECT chunk_id, document_name, page, chunk_index, text, bm25(chunks_fts) AS score
            FROM chunks_fts
            WHERE chunks_fts MATCH ? AND collection_id = ?
            ORDER BY score
            LIMIT ?
            """,
            (match_query, collection_id, k),
        ).fetchall()

    return [
        RetrievedChunk(
            chunk_id=row[0],
            document_name=row[1],
            page=page_from_str(row[2]),
            chunk_index=row[3],
            text=row[4],
            score=row[5],
        )
        for row in rows
    ]


def _build_match_query(query: str) -> str:
    tokens = re.findall(r"\w+", query)
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens)
