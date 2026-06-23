import uuid

from sqlalchemy import select

from eventforge.db.models import SynthesisReport
from eventforge.db.repositories.base import BaseRepository


class SynthesisReportRepository(BaseRepository):
    async def get_by_job_id(self, job_id: uuid.UUID) -> SynthesisReport | None:
        result = await self.session.execute(
            select(SynthesisReport).where(SynthesisReport.job_id == job_id)
        )
        return result.scalar_one_or_none()
