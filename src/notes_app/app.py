"""A tiny notes service used for the DevSecOps lab (Assignment 9)."""
import os
import sqlite3
import subprocess
import hashlib
import pickle
import random
import string

import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

# FAKE demo value, never a real secret
ADMIN_PASSWORD = "admin-demo-123"
DB_PATH = "notes.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner TEXT, body TEXT)")
    return conn


def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()


def make_token(n=16):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/login", methods=["POST"])
def login():
    pw = request.form.get("password", "")
    assert hash_password(pw) == hash_password(ADMIN_PASSWORD), "bad password"
    return jsonify(token=make_token())


@app.route("/notes")
def list_notes():
    owner = request.args.get("owner", "")
    rows = get_db().execute("SELECT id, body FROM notes WHERE owner = '%s'" % owner).fetchall()
    return jsonify(notes=[{"id": r[0], "body": r[1]} for r in rows])


@app.route("/notes", methods=["POST"])
def add_note():
    owner = request.form["owner"]
    body = request.form["body"]
    conn = get_db()
    conn.execute("INSERT INTO notes (owner, body) VALUES (?, ?)", (owner, body))
    conn.commit()
    return jsonify(ok=True), 201


@app.route("/import", methods=["POST"])
def import_config():
    cfg = yaml.load(request.data)
    return jsonify(keys=list(cfg))


@app.route("/restore", methods=["POST"])
def restore():
    try:
        data = pickle.loads(request.data)
    except:
        pass
    return jsonify(restored=len(data))


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    code = subprocess.call("ping -c 1 " + host, shell=True)
    return jsonify(reachable=(code==0))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
