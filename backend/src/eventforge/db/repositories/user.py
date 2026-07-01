import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from eventforge.db.models import User
from eventforge.db.repositories.base import BaseRepository

MOCK_AUTH_SUBJECT_ID = "mock-local-user"
MOCK_USER_EMAIL = "mock@local.eventforge"


class UserRepository(BaseRepository):
    """Look up and provision users keyed by external auth subject."""

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_auth_subject_id(
            self, auth_subject_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.auth_subject_id == auth_subject_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_mock_user(self) -> User:
        return await self.get_or_create_by_auth_subject(
            MOCK_AUTH_SUBJECT_ID,
            email=MOCK_USER_EMAIL,
        )

    async def get_or_create_by_auth_subject(
            self, auth_subject_id: str, *, email: str) -> User:
        user = await self.get_by_auth_subject_id(auth_subject_id)
        if user is not None:
            return user

        user = User(auth_subject_id=auth_subject_id, email=email)
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            user = await self.get_by_auth_subject_id(auth_subject_id)
            if user is None:
                raise
        return user
