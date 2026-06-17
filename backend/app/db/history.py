"""SQLite store for collections, documents, and chat messages.

Shares the same SQLite file as the FTS5 keyword index (settings.sqlite_db_path)
so the project has a single local database file. Plain sqlite3 is used
(no ORM) — three small tables with simple queries don't justify the extra
layer, and it keeps this module consistent with db/fts.py.
"""

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings


def _connect() -> sqlite3.Connection:
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                collection_id TEXT NOT NULL REFERENCES collections(id),
                filename TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                collection_id TEXT NOT NULL REFERENCES collections(id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def create_collection(name: str) -> dict:
    collection_id = uuid.uuid4().hex
    created_at = datetime.now(UTC).isoformat()
    with _connect() as con:
        con.execute(
            "INSERT INTO collections (id, name, created_at) VALUES (?, ?, ?)",
            (collection_id, name, created_at),
        )
    return {"id": collection_id, "name": name, "created_at": created_at}


def list_collections() -> list[dict]:
    with _connect() as con:
        rows = con.execute(
            """
            SELECT c.id, c.name, c.created_at, COUNT(d.id) AS document_count
            FROM collections c
            LEFT JOIN documents d ON d.collection_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_collection(collection_id: str) -> dict | None:
    with _connect() as con:
        row = con.execute(
            "SELECT id, name, created_at FROM collections WHERE id = ?",
            (collection_id,),
        ).fetchone()
        if row is None:
            return None
        documents = con.execute(
            "SELECT id, filename, chunk_count, uploaded_at FROM documents WHERE collection_id = ? ORDER BY uploaded_at",
            (collection_id,),
        ).fetchall()

    result = dict(row)
    result["documents"] = [dict(d) for d in documents]
    return result


def delete_collection(collection_id: str) -> None:
    with _connect() as con:
        con.execute("DELETE FROM messages WHERE collection_id = ?", (collection_id,))
        con.execute("DELETE FROM documents WHERE collection_id = ?", (collection_id,))
        con.execute("DELETE FROM collections WHERE id = ?", (collection_id,))


def add_document(collection_id: str, filename: str, chunk_count: int) -> dict:
    document_id = uuid.uuid4().hex
    uploaded_at = datetime.now(UTC).isoformat()
    with _connect() as con:
        con.execute(
            "INSERT INTO documents (id, collection_id, filename, chunk_count, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (document_id, collection_id, filename, chunk_count, uploaded_at),
        )
    return {"id": document_id, "filename": filename, "chunk_count": chunk_count, "uploaded_at": uploaded_at}


def add_message(collection_id: str, role: str, content: str) -> None:
    message_id = uuid.uuid4().hex
    created_at = datetime.now(UTC).isoformat()
    with _connect() as con:
        con.execute(
            "INSERT INTO messages (id, collection_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (message_id, collection_id, role, content, created_at),
        )


def get_messages(collection_id: str, limit: int = 20) -> list[dict]:
    with _connect() as con:
        rows = con.execute(
            """
            SELECT role, content, created_at FROM messages
            WHERE collection_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (collection_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
