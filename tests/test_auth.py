import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from backend.models.user import User
from backend.main import app

def test_get_current_user_bypass(session: Session):
    from backend.api.routers.auth import get_current_user
    user = get_current_user(session)
    assert user is not None
    assert user.email == "local_admin@local.host"

def test_register_success(client: TestClient, session: Session):
    payload = {"email": "newuser@test.com", "password": "securepassword"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert "id" in data

def test_register_duplicate(client: TestClient, session: Session):
    payload = {"email": "dup@test.com", "password": "pass"}
    client.post("/api/v1/auth/register", json=payload)
    # Riprova
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success(client: TestClient, session: Session):
    # Registra
    client.post("/api/v1/auth/register", json={"email": "login@test.com", "password": "pass"})
    # Login
    response = client.post("/api/v1/auth/login", data={"username": "login@test.com", "password": "pass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(client: TestClient, session: Session):
    client.post("/api/v1/auth/register", json={"email": "fail@test.com", "password": "pass"})
    response = client.post("/api/v1/auth/login", data={"username": "fail@test.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
