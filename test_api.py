import os
import shutil

DB_PATH = "./test_test.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_create_and_redirect():
    # create
    resp = client.post("/shorten", json={"target_url": "https://example.com"})
    assert resp.status_code == 201
    body = resp.json()
    assert "alias" in body
    alias = body["alias"]

    # redirect
    r = client.get(f"/{alias}", follow_redirects=False)
    assert r.status_code == 307
    # Accept either with or without trailing slash
    assert r.headers["location"].rstrip('/') == "https://example.com"

    # meta shows access_count incremented (>=1)
    m = client.get(f"/{alias}/meta")
    assert m.status_code == 200
    meta = m.json()
    assert meta["access_count"] >= 1


