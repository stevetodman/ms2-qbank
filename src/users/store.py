"""User data persistence layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine, select

from .auth import hash_password, verify_password
from .models import RefreshToken, User, UserCreate, UserUpdate


class UserStore:
    """Handle user data persistence with SQLite database."""

    def __init__(self, database_url: str = "sqlite:///data/users.db") -> None:
        """Initialize the user store with a database connection.

        Args:
            database_url: SQLAlchemy database URL
        """
        # Ensure data directory exists
        if database_url.startswith("sqlite:///"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(database_url, echo=False)
        SQLModel.metadata.create_all(self.engine)

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user account.

        Args:
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            ValueError: If email already exists
        """
        with Session(self.engine) as session:
            # Check if email already exists
            existing = session.exec(
                select(User).where(User.email == user_data.email)
            ).first()
            if existing:
                raise ValueError(f"User with email {user_data.email} already exists")

            # Create new user with hashed password
            user = User(
                email=user_data.email,
                hashed_password=hash_password(user_data.password),
                full_name=user_data.full_name,
                exam_date=user_data.exam_date,
            )

            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.email == email)).first()

            if not user or not user.is_active:
                return None

            if not verify_password(password, user.hashed_password):
                return None

            # Update last login timestamp
            user.last_login = datetime.now(timezone.utc)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID.

        Args:
            user_id: User's database ID

        Returns:
            User object if found, None otherwise
        """
        with Session(self.engine) as session:
            return session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        with Session(self.engine) as session:
            return session.exec(select(User).where(User.email == email)).first()

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user profile information.

        Args:
            user_id: User's database ID
            user_data: Updated user data

        Returns:
            Updated user object

        Raises:
            KeyError: If user not found
        """
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            if not user:
                raise KeyError(f"User {user_id} not found")

            # Update fields if provided
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            if user_data.exam_date is not None:
                user.exam_date = user_data.exam_date
            if user_data.notification_preferences is not None:
                user.notification_preferences = json.dumps(user_data.notification_preferences)
            if user_data.display_settings is not None:
                user.display_settings = json.dumps(user_data.display_settings)

            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account (soft delete).

        Args:
            user_id: User's database ID

        Returns:
            Deactivated user object

        Raises:
            KeyError: If user not found
        """
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            if not user:
                raise KeyError(f"User {user_id} not found")

            user.is_active = False
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def store_refresh_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime,
        device_info: Optional[str] = None,
    ) -> RefreshToken:
        """Store a refresh token in the database.

        Args:
            user_id: User's database ID
            token: JWT refresh token string
            expires_at: Token expiration timestamp
            device_info: Optional device/browser information

        Returns:
            Created RefreshToken object
        """
        with Session(self.engine) as session:
            refresh_token = RefreshToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                device_info=device_info,
            )
            session.add(refresh_token)
            session.commit()
            session.refresh(refresh_token)
            return refresh_token

    def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Retrieve a refresh token by its value.

        Args:
            token: JWT refresh token string

        Returns:
            RefreshToken object if found and valid, None otherwise
        """
        with Session(self.engine) as session:
            refresh_token = session.exec(
                select(RefreshToken).where(
                    RefreshToken.token == token,
                    RefreshToken.revoked == False,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
            ).first()
            return refresh_token

    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a specific refresh token.

        Args:
            token: JWT refresh token string

        Returns:
            True if token was revoked, False if not found
        """
        with Session(self.engine) as session:
            refresh_token = session.exec(
                select(RefreshToken).where(RefreshToken.token == token)
            ).first()

            if not refresh_token:
                return False

            refresh_token.revoked = True
            session.add(refresh_token)
            session.commit()
            return True

    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: User's database ID

        Returns:
            Number of tokens revoked
        """
        with Session(self.engine) as session:
            tokens = session.exec(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked == False,
                )
            ).all()

            count = 0
            for token in tokens:
                token.revoked = True
                session.add(token)
                count += 1

            session.commit()
            return count

    def cleanup_expired_tokens(self) -> int:
        """Remove expired refresh tokens from the database.

        Returns:
            Number of tokens deleted
        """
        with Session(self.engine) as session:
            expired_tokens = session.exec(
                select(RefreshToken).where(
                    RefreshToken.expires_at < datetime.now(timezone.utc)
                )
            ).all()

            count = 0
            for token in expired_tokens:
                session.delete(token)
                count += 1

            session.commit()
            return count
