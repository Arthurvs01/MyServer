import pytest
from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"CasaPy" in response.data


def test_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"CasaPy" in response.data


def test_home_redirect_to_login(client):
    # O Flask redireciona para login quando não autenticado
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 302
    assert b"Login" in response.data


def test_api_status_requires_auth(client):
    response = client.get("/api/status")
    assert response.status_code == 401
