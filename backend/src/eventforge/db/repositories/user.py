import uuid

from sqlalchemy import select

from eventforge.db.models import User
from eventforge.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.clerk_id == clerk_id))
        return result.scalar_one_or_none()
