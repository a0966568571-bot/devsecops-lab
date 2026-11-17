"""A tiny notes service used for the DevSecOps lab (Assignment 9)."""
import ipaddress
import json
import os
import secrets
import shutil
import sqlite3
import subprocess  # noqa: S404 - reviewed: fixed argv list, never a shell

import yaml
from flask import Flask, request, jsonify, abort, send_file
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Read from the environment (a GitHub/host secret in real deployments).
# The fallback is random, so there is no hard-coded password in the source.
ADMIN_PASSWORD_HASH = generate_password_hash(
    os.environ.get("ADMIN_PASSWORD", secrets.token_urlsafe(16))
)
DB_PATH = "notes.db"
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner TEXT, body TEXT)"
    )
    return conn


def make_token():
    return secrets.token_urlsafe(16)


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/login", methods=["POST"])
def login():
    pw = request.form.get("password", "")
    if not check_password_hash(ADMIN_PASSWORD_HASH, pw):
        abort(401)
    return jsonify(token=make_token())


@app.route("/notes")
def list_notes():
    owner = request.args.get("owner", "")
    rows = get_db().execute(
        "SELECT id, body FROM notes WHERE owner = ?", (owner,)
    ).fetchall()
    return jsonify(notes=[{"id": r[0], "body": r[1]} for r in rows])


@app.route("/notes", methods=["POST"])
def add_note():
    owner = request.form["owner"]
    body = request.form["body"]
    conn = get_db()
    conn.execute("INSERT INTO notes (owner, body) VALUES (?, ?)", (owner, body))
    conn.commit()
    return jsonify(ok=True), 201


@app.route("/greet")
def greet():
    name = request.args.get("name", "guest")
    return f"<p>Hello {name}!</p>"


@app.route("/export")
def export_note():
    name = request.args.get("name", "welcome.txt")
    return send_file(os.path.join(EXPORT_DIR, name))


@app.route("/import", methods=["POST"])
def import_config():
    cfg = yaml.safe_load(request.data)
    if not isinstance(cfg, dict):
        abort(400)
    return jsonify(keys=list(cfg))


@app.route("/restore", methods=["POST"])
def restore():
    try:
        data = json.loads(request.data)
    except ValueError:
        abort(400)
    return jsonify(restored=len(data))


@app.route("/ping")
def ping():
    try:
        host = str(ipaddress.ip_address(request.args.get("host", "127.0.0.1")))
    except ValueError:
        abort(400)
    ping_bin = shutil.which("ping") or "/bin/ping"
    # reviewed: host is a validated IP address and no shell is used
    code = subprocess.call([ping_bin, "-c", "1", host])  # noqa: S603
    return jsonify(reachable=(code == 0))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
