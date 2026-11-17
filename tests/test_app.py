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


def test_login_rejects_wrong_password(client):
    assert client.post("/login", data={"password": "nope"}).status_code == 401


def test_login_accepts_password_from_env(monkeypatch):
    from werkzeug.security import generate_password_hash
    monkeypatch.setattr(app_module, "ADMIN_PASSWORD_HASH", generate_password_hash("fake-test-pw"))
    c = app_module.app.test_client()
    assert "token" in c.post("/login", data={"password": "fake-test-pw"}).get_json()


def test_restore_uses_json_not_pickle(client):
    assert client.post("/restore", data="[1, 2, 3]").get_json() == {"restored": 3}
    assert client.post("/restore", data=b"\x80\x04K\x01.").status_code == 400


def test_ping_rejects_shell_injection(client):
    assert client.get("/ping", query_string={"host": "127.0.0.1; rm -rf /"}).status_code == 400


def test_export_returns_file(client):
    r = client.get("/export", query_string={"name": "welcome.txt"})
    assert r.status_code == 200
    assert b"Welcome" in r.data


def test_greet(client):
    assert b"Hello amy" in client.get("/greet?name=amy").data
