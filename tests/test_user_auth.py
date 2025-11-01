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


# --- Refresh Token Tests ---


def test_login_returns_refresh_token(client):
    """Test that login returns both access and refresh tokens."""
    # Register a user
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    # Login
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
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900  # 15 minutes in seconds


def test_refresh_token_flow(client):
    """Test complete refresh token flow."""
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

    assert login_response.status_code == 200
    login_data = login_response.json()
    old_access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # Use refresh token to get new access token
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    # New tokens should be different from old ones
    assert refresh_data["access_token"] != old_access_token
    assert refresh_data["refresh_token"] != refresh_token

    # New access token should work
    profile_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {refresh_data['access_token']}"},
    )
    assert profile_response.status_code == 200


def test_refresh_token_invalidates_old_token(client):
    """Test that old refresh token cannot be reused after refresh."""
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

    refresh_token = login_response.json()["refresh_token"]

    # Use refresh token once
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200

    # Try to use old refresh token again - should fail
    second_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert second_refresh.status_code == 401
    assert "not found or has been revoked" in second_refresh.json()["detail"]


def test_refresh_with_invalid_token(client):
    """Test that refresh fails with invalid token."""
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid-token-string"},
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_refresh_with_access_token(client):
    """Test that refresh fails when using an access token instead of refresh token."""
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

    # Try to refresh using access token (wrong token type)
    access_token = login_response.json()["access_token"]
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_logout_revokes_refresh_tokens(client, store):
    """Test that logout revokes all refresh tokens for a user."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    # Login to get tokens
    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Logout
    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 204

    # Try to use refresh token after logout - should fail
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


def test_refresh_token_stored_in_database(client, store):
    """Test that refresh tokens are properly stored in the database."""
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

    refresh_token = login_response.json()["refresh_token"]

    # Verify token is in database
    db_token = store.get_refresh_token(refresh_token)
    assert db_token is not None
    assert db_token.token == refresh_token
    assert db_token.revoked is False


def test_multiple_refresh_tokens_per_user(client):
    """Test that a user can have multiple active refresh tokens (multi-device support)."""
    # Register
    client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
            "full_name": "Jane Doe",
        },
    )

    # Login from "device 1"
    login1 = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )
    refresh_token1 = login1.json()["refresh_token"]

    # Login from "device 2"
    login2 = client.post(
        "/auth/login",
        json={
            "email": "student@example.com",
            "password": "SecurePass123!",
        },
    )
    refresh_token2 = login2.json()["refresh_token"]

    # Both tokens should be different
    assert refresh_token1 != refresh_token2

    # Both tokens should work
    refresh1_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token1},
    )
    assert refresh1_response.status_code == 200

    refresh2_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token2},
    )
    assert refresh2_response.status_code == 200
