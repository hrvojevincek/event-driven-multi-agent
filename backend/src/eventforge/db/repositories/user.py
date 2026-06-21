import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from eventforge.db.models import User
from eventforge.db.repositories.base import BaseRepository

MOCK_CLERK_ID = "mock-local-user"
MOCK_USER_EMAIL = "mock@local.eventforge"


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.clerk_id == clerk_id))
        return result.scalar_one_or_none()

    async def get_or_create_mock_user(self) -> User:
        user = await self.get_by_clerk_id(MOCK_CLERK_ID)
        if user is not None:
            return user

        user = User(clerk_id=MOCK_CLERK_ID, email=MOCK_USER_EMAIL)
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            user = await self.get_by_clerk_id(MOCK_CLERK_ID)
            if user is None:
                raise
        return user
