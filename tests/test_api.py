import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.api.main import app  # noqa: E402
from tests.helpers import raw  # noqa: E402

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_phish_contract():
    response = client.post("/analyze", json={"raw_email": raw("phish_credential.eml")})
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "phishing"
    for key in ("probabilities", "uncertain", "summary", "links", "sender", "language", "model_version"):
        assert key in body
    assert "http://" not in response.text and "https://" not in response.text  # links are defanged


def test_analyze_rejects_empty_and_garbage():
    assert client.post("/analyze", json={"raw_email": ""}).status_code == 422
    assert client.post("/analyze", json={"raw_email": "no headers here"}).status_code == 422
