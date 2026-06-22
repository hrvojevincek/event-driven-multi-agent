from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.api.deps import get_db, get_settings
from eventforge.api.schemas.queries import (
    QueryDetailResponse,
    SubmitQueryRequest,
    SubmitQueryResponse,
)
from eventforge.core.config import Settings
from eventforge.events.publisher import EventPublisher, EventPublishError
from eventforge.services.query import get_query_detail, submit_query

router = APIRouter()


def get_publisher(settings: Settings = Depends(get_settings)) -> EventPublisher:
    return EventPublisher(settings)


@router.post(
    "/queries",
    status_code=status.HTTP_201_CREATED,
    response_model=SubmitQueryResponse,
)
async def create_query(
    body: SubmitQueryRequest,
    db: AsyncSession = Depends(get_db),
    publisher: EventPublisher = Depends(get_publisher),
) -> SubmitQueryResponse:
    try:
        result = await submit_query(
            db,
            publisher,
            topic=body.topic,
            depth=body.depth,
            max_sources=body.max_sources,
        )
    except EventPublishError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Failed to publish query.submitted event", "error": str(exc)},
        ) from exc

    return SubmitQueryResponse(job_id=result.job_id, correlation_id=result.correlation_id)


@router.get(
    "/queries/{job_id}",
    response_model=QueryDetailResponse,
)
async def get_query(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> QueryDetailResponse:
    detail = await get_query_detail(db, job_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return detail
