from fastapi.testclient import TestClient

from app.main import app


def test_login_page():
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    assert "CasaPy" in response.text


def test_register_page():
    client = TestClient(app)
    response = client.get("/register")
    assert response.status_code == 200
    assert "CasaPy" in response.text


def test_home_redirect_to_login():
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers.get("location", "")


def test_api_status_requires_auth():
    client = TestClient(app)
    response = client.get("/api/status")
    assert response.status_code == 401
