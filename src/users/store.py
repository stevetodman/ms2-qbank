"""User data persistence layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, select

from db_utils import create_hardened_sqlite_engine
from .auth import hash_password, verify_password
from .models import User, UserCreate, UserUpdate


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

        self.engine = create_hardened_sqlite_engine(database_url, echo=False)
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
