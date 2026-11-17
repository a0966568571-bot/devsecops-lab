import pytest

from notes_app import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DB_PATH", str(tmp_path / "test.db"))
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_add_and_list_notes(client):
    assert client.post("/notes", data={"owner": "amy", "body": "hi"}).status_code == 201
    client.post("/notes", data={"owner": "bob", "body": "secret"})
    notes = client.get("/notes?owner=amy").get_json()["notes"]
    assert [n["body"] for n in notes] == ["hi"]


def test_sql_injection_does_not_leak_other_owners(client):
    client.post("/notes", data={"owner": "bob", "body": "secret"})
    notes = client.get("/notes", query_string={"owner": "x' OR '1'='1"}).get_json()["notes"]
    assert notes == []


def test_import_yaml(client):
    r = client.post("/import", data="a: 1\nb: 2\n")
    assert r.get_json() == {"keys": ["a", "b"]}
