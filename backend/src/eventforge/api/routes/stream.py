from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from eventforge.api.deps import (
    Settings,
    get_cognito_validator,
    get_settings,
    resolve_current_user,
)
from eventforge.db.models import User
from eventforge.db.repositories import JobRepository
from eventforge.db.session import get_session_factory
from eventforge.services.auth.cognito import CognitoTokenValidator
from eventforge.services.stage_stream import (
    format_sse,
    format_sse_keepalive,
    iter_job_stream_events,
)

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


async def _assert_job_access(
    db: AsyncSession,
    job_id: UUID,
    user: User,
) -> None:
    job = await JobRepository(db).get_by_id(job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("/queries/{job_id}/stream")
async def stream_query_events(
    job_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
    validator: CognitoTokenValidator = Depends(get_cognito_validator),
) -> StreamingResponse:
    """Stream pipeline stage updates for a job via Server-Sent Events."""
    session_factory = get_session_factory()
    async with session_factory() as db:
        current_user = await resolve_current_user(db, credentials, settings, validator)
        await _assert_job_access(db, job_id, current_user)
        user_id = current_user.id

    async def event_generator():
        async for event in iter_job_stream_events(job_id, user_id):
            if event is None:
                yield format_sse_keepalive()
            else:
                yield format_sse(event, sse_event=event.event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
