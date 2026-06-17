from fastapi.testclient import TestClient

from app.db import history
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_collections_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(history.settings, "sqlite_db_path", str(tmp_path / "test.db"))
    history.init_db()

    response = client.get("/collections")
    assert response.status_code == 200
    assert response.json() == []
