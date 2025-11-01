"""FastAPI application for user authentication and account management."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

# Import monitoring utilities
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.logging import add_monitoring

from .auth import (
    create_access_token,
    create_token_pair,
    decode_refresh_token,
    get_user_id_from_token,
    JWT_EXPIRATION_HOURS,
)
from .models import (
    RefreshTokenRequest,
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserProfile,
    UserUpdate,
)
from .store import UserStore

security = HTTPBearer()


def create_app(*, store: Optional[UserStore] = None) -> FastAPI:
    """Create and configure the user authentication FastAPI application.

    Args:
        store: Optional UserStore instance for dependency injection (testing)

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="MS2 QBank User API",
        version="1.0.0",
        description="User authentication and account management service",
    )

    # Add monitoring (logging, Sentry, health checks)
    add_monitoring(app, service_name="users")

    # Initialize user store
    user_store = store or UserStore()
    app.state.user_store = user_store

    logger.info("User store initialized")

    def get_store() -> UserStore:
        """Dependency to get the user store instance."""
        return app.state.user_store

    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        store: UserStore = Depends(get_store),
    ) -> User:
        """Dependency to get the current authenticated user from JWT token.

        Args:
            credentials: HTTP Bearer token credentials
            store: User store instance

        Returns:
            Authenticated user object

        Raises:
            HTTPException: If token is invalid or user not found
        """
        token = credentials.credentials
        user_id = get_user_id_from_token(token)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = store.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    # --- PUBLIC ENDPOINTS ---

    @app.post("/auth/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
    def register(user_data: UserCreate, store: UserStore = Depends(get_store)) -> UserProfile:
        """Register a new user account.

        Args:
            user_data: User registration data
            store: User store instance

        Returns:
            Created user profile

        Raises:
            HTTPException: If email already exists or validation fails
        """
        try:
            user = store.create_user(user_data)
            logger.info(
                "New user registered",
                user_id=user.id,
                email=user.email,
                subscription_tier=user.subscription_tier,
            )
        except ValueError as exc:
            logger.warning(
                "User registration failed",
                email=user_data.email,
                reason=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            exam_date=user.exam_date,
            subscription_tier=user.subscription_tier,
            subscription_start=user.subscription_start,
            subscription_end=user.subscription_end,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
        )

    @app.post("/auth/login", response_model=TokenResponse)
    def login(credentials: UserLogin, store: UserStore = Depends(get_store)) -> TokenResponse:
        """Authenticate a user and return access and refresh tokens.

        Args:
            credentials: User login credentials
            store: User store instance

        Returns:
            JWT token pair (access + refresh tokens)

        Raises:
            HTTPException: If authentication fails
        """
        user = store.authenticate(credentials.email, credentials.password)

        if user is None:
            logger.warning(
                "Login attempt failed",
                email=credentials.email,
                reason="Invalid credentials",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate JWT token pair (access + refresh)
        token_data = create_token_pair(user.id, user.email)

        logger.info(
            "User logged in successfully",
            user_id=user.id,
            email=user.email,
        )

        # Store refresh token in database
        store.store_refresh_token(
            user_id=user.id,
            token=token_data["refresh_token"],
            expires_at=token_data["refresh_expires_at"],
        )

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
        )

    @app.post("/auth/refresh", response_model=TokenResponse)
    def refresh_token(
        refresh_request: RefreshTokenRequest,
        store: UserStore = Depends(get_store),
    ) -> TokenResponse:
        """Refresh an access token using a refresh token.

        Args:
            refresh_request: Refresh token request payload
            store: User store instance

        Returns:
            New JWT token pair (access + refresh tokens)

        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        import jwt

        try:
            # Decode and validate refresh token
            payload = decode_refresh_token(refresh_request.refresh_token)
            user_id = int(payload.get("sub"))
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        # Check if token exists in database and is not revoked
        db_token = store.get_refresh_token(refresh_request.refresh_token)
        if db_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = store.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Revoke old refresh token
        store.revoke_refresh_token(refresh_request.refresh_token)

        # Generate new token pair
        token_data = create_token_pair(user.id, user.email)

        # Store new refresh token in database
        store.store_refresh_token(
            user_id=user.id,
            token=token_data["refresh_token"],
            expires_at=token_data["refresh_expires_at"],
        )

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
        )

    # --- PROTECTED ENDPOINTS ---

    @app.get("/auth/me", response_model=UserProfile)
    def get_current_user_profile(current_user: User = Depends(get_current_user)) -> UserProfile:
        """Get the current authenticated user's profile.

        Args:
            current_user: Authenticated user from JWT token

        Returns:
            User profile information
        """
        return UserProfile(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            exam_date=current_user.exam_date,
            subscription_tier=current_user.subscription_tier,
            subscription_start=current_user.subscription_start,
            subscription_end=current_user.subscription_end,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            is_active=current_user.is_active,
        )

    @app.patch("/auth/me", response_model=UserProfile)
    def update_current_user_profile(
        user_data: UserUpdate,
        current_user: User = Depends(get_current_user),
        store: UserStore = Depends(get_store),
    ) -> UserProfile:
        """Update the current authenticated user's profile.

        Args:
            user_data: Updated user data
            current_user: Authenticated user from JWT token
            store: User store instance

        Returns:
            Updated user profile

        Raises:
            HTTPException: If update fails
        """
        try:
            updated_user = store.update_user(current_user.id, user_data)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            ) from exc

        return UserProfile(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            exam_date=updated_user.exam_date,
            subscription_tier=updated_user.subscription_tier,
            subscription_start=updated_user.subscription_start,
            subscription_end=updated_user.subscription_end,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login,
            is_active=updated_user.is_active,
        )

    @app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(
        current_user: User = Depends(get_current_user),
        store: UserStore = Depends(get_store),
    ) -> None:
        """Logout the current user and revoke all refresh tokens.

        Args:
            current_user: Authenticated user from JWT token
            store: User store instance

        Note:
            This revokes all refresh tokens for the user. Access tokens
            remain valid until expiration (15 minutes) due to stateless JWT design.
        """
        # Revoke all refresh tokens for this user
        store.revoke_all_user_tokens(current_user.id)
        # Access tokens cannot be invalidated server-side (stateless JWT)
        # They will expire in 15 minutes

    return app


# Create default app instance
app = create_app()

__all__ = ["app", "create_app"]
