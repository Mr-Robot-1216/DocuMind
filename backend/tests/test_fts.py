from app.db import fts
from app.schemas.chunks import ChunkRecord


def _chunk(chunk_id, collection_id, text, page=1, chunk_index=0, document_name="doc.pdf") -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        collection_id=collection_id,
        document_name=document_name,
        page=page,
        chunk_index=chunk_index,
        text=text,
    )


def test_index_and_search(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fts.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    fts.init_db()

    fts.index_chunks(
        [
            _chunk("c1", "col1", "The quick brown fox jumps over the lazy dog"),
            _chunk("c2", "col1", "Completely unrelated content about pandas and numpy"),
            _chunk("c3", "col2", "The quick brown fox in another collection"),
        ]
    )

    results = fts.search_fts("col1", "quick fox", k=5)

    assert [r.chunk_id for r in results] == ["c1"]
    assert results[0].page == 1
    assert results[0].document_name == "doc.pdf"


def test_search_no_matches_returns_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fts.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    fts.init_db()
    fts.index_chunks([_chunk("c1", "col1", "hello world")])

    assert fts.search_fts("col1", "nonexistentword", k=5) == []


def test_search_empty_query_returns_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fts.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    fts.init_db()

    assert fts.search_fts("col1", "   ", k=5) == []


def test_page_none_round_trips(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fts.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    fts.init_db()
    fts.index_chunks([_chunk("c1", "col1", "docx content here", page=None, document_name="doc.docx")])

    results = fts.search_fts("col1", "docx content", k=5)

    assert results[0].page is None


def test_page_sheet_name_round_trips(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fts.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    fts.init_db()
    fts.index_chunks([_chunk("c1", "col1", "spreadsheet content", page="Sheet1", document_name="doc.xlsx")])

    results = fts.search_fts("col1", "spreadsheet", k=5)

    assert results[0].page == "Sheet1"


def test_delete_collection_chunks_removes_only_that_collection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fts.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    fts.init_db()
    fts.index_chunks(
        [
            _chunk("c1", "col1", "the quick brown fox"),
            _chunk("c2", "col2", "the quick brown fox"),
        ]
    )

    fts.delete_collection_chunks("col1")

    assert fts.search_fts("col1", "quick fox", k=5) == []
    assert [r.chunk_id for r in fts.search_fts("col2", "quick fox", k=5)] == ["c2"]
