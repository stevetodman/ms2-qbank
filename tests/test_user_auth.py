"""Tests for user authentication service."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from users.app import create_app
from users.models import UserCreate, UserLogin, UserUpdate
from users.store import UserStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield f"sqlite:///{db_path}"
    db_path.unlink(missing_ok=True)


@pytest.fixture
def store(temp_db):
    """Create a UserStore instance with temporary database."""
    return UserStore(database_url=temp_db)


@pytest.fixture
def client(store):
    """Create a test client with the user authentication app."""
    app = create_app(store=store)
    return TestClient(app)


def test_user_registration(client):
    """Test user registration endpoint."""
    response = client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["full_name"] == "Jane Doe"
    assert data["subscription_tier"] == "trial"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_duplicate_email_registration(client):
    """Test that duplicate email registration is rejected."""
    user_data = {
        "email": "student@example.com",
        "password": "SecurePass123!",
        "full_name": "Jane Doe",
    }

    # First registration should succeed
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Second registration with same email should fail
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_user_login(client):
    """Test user login endpoint."""
    # Register a user first
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    # Login with correct credentials
    response = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_with_wrong_password(client):
    """Test that login fails with incorrect password."""
    # Register a user
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    # Try to login with wrong password
    response = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_with_nonexistent_user(client):
    """Test that login fails for non-existent user."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword",
        },
    )

    assert response.status_code == 401


def test_get_current_user_profile(client):
    """Test getting current user profile with valid token."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )
    token = login_response.json()["access_token"]

    # Get profile with token
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["full_name"] == "Jane Doe"


def test_get_profile_without_token(client):
    """Test that getting profile without token fails."""
    response = client.get("/auth/me")
    assert response.status_code == 403  # Forbidden (no token)


def test_get_profile_with_invalid_token(client):
    """Test that getting profile with invalid token fails."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_update_user_profile(client):
    """Test updating user profile."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )
    token = login_response.json()["access_token"]

    # Update profile
    response = client.patch(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Jane Smith",
            "notification_preferences": {"email_reminders": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Jane Smith"


def test_logout(client):
    """Test logout endpoint."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )
    token = login_response.json()["access_token"]

    # Logout
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204


def test_password_hashing(store):
    """Test that passwords are properly hashed."""
    user_data = UserCreate(
        email="student@example.com",
        password="SecurePass123!",
        full_name="Jane Doe",
    )

    user = store.create_user(user_data)

    # Password should be hashed, not stored as plain text
    assert user.hashed_password != "SecurePass123!"
    assert user.hashed_password.startswith("$2b$")  # bcrypt hash prefix


def test_authentication_flow(store):
    """Test complete authentication flow."""
    # Create user
    user_data = UserCreate(
        email="student@example.com",
        password="SecurePass123!",
        full_name="Jane Doe",
    )
    user = store.create_user(user_data)
    assert user.last_login is None

    # Authenticate with correct credentials
    authenticated_user = store.authenticate("student@example.com", "SecurePass123!")
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    assert authenticated_user.last_login is not None

    # Authenticate with wrong credentials
    failed_auth = store.authenticate("student@example.com", "WrongPassword")
    assert failed_auth is None
