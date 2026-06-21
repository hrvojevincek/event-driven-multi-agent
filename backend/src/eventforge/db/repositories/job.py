import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from eventforge.db.models import Job, JobStage, StageStatus
from eventforge.db.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id).options(selectinload(Job.stages))
        )
        return result.scalar_one_or_none()

    async def get_by_correlation_id(self, correlation_id: str) -> Job | None:
        result = await self.session.execute(
            select(Job)
            .where(Job.correlation_id == correlation_id)
            .options(selectinload(Job.stages))
        )
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: uuid.UUID) -> list[Job]:
        result = await self.session.execute(
            select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
        )
        return list(result.scalars().all())


class JobStageRepository(BaseRepository):
    async def get_by_job_and_stage(self, job_id: uuid.UUID, stage: str) -> JobStage | None:
        result = await self.session.execute(
            select(JobStage).where(JobStage.job_id == job_id, JobStage.stage == stage)
        )
        return result.scalar_one_or_none()

    async def mark_running(self, job_stage: JobStage) -> JobStage:
        now = datetime.now(tz=UTC)
        job_stage.status = StageStatus.RUNNING.value
        job_stage.started_at = now
        await self.session.flush()
        return job_stage

    async def mark_completed(self, job_stage: JobStage) -> JobStage:
        now = datetime.now(tz=UTC)
        job_stage.status = StageStatus.COMPLETED.value
        job_stage.completed_at = now
        if job_stage.started_at is not None:
            job_stage.duration_ms = int((now - job_stage.started_at).total_seconds() * 1000)
        await self.session.flush()
        return job_stage
