import uuid
from decimal import Decimal

from sqlalchemy import func, select

from eventforge.db.models import LLMUsage
from eventforge.db.repositories.base import BaseRepository


class LLMUsageRepository(BaseRepository):
    """Persist and aggregate LLM token usage per job."""

    async def log(
        self,
        *,
        job_id: uuid.UUID,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
    ) -> LLMUsage:
        record = LLMUsage(
            job_id=job_id,
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_by_job_id(self, job_id: uuid.UUID) -> list[LLMUsage]:
        result = await self.session.execute(
            select(LLMUsage)
            .where(LLMUsage.job_id == job_id)
            .order_by(LLMUsage.created_at)
        )
        return list(result.scalars().all())

    async def total_cost_by_job_id(self, job_id: uuid.UUID) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(LLMUsage.cost_usd), 0)).where(
                LLMUsage.job_id == job_id
            )
        )
        total = result.scalar_one()
        return Decimal(str(total))
