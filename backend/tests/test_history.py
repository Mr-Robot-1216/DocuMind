from app.db import history


def test_delete_collection_removes_collection_documents_and_messages(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(history.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    history.init_db()

    collection = history.create_collection("To delete")
    collection_id = collection["id"]
    history.add_document(collection_id, "doc.pdf", chunk_count=3)
    history.add_message(collection_id, "user", "hello")

    history.delete_collection(collection_id)

    assert history.get_collection(collection_id) is None
    assert all(c["id"] != collection_id for c in history.list_collections())


def test_delete_collection_does_not_affect_others(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(history.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    history.init_db()

    keep = history.create_collection("Keep")
    remove = history.create_collection("Remove")

    history.delete_collection(remove["id"])

    assert history.get_collection(keep["id"]) is not None
