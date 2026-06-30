# EventForge Backend

FastAPI application, SQS workers, and agent pipeline.

## Setup

```bash
cd backend
cp .env.example .env   # or use repo-root .env
uv sync
```

Install git hooks (runs `ruff check` on commit):

```bash
make hooks   # from repo root
```

## Run (Phase 1+)

```bash
uv run uvicorn eventforge.main:app --reload --port 8000
```

Via Docker Compose (from repo root, with infra + backend):

```bash
make dev
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

Logging uses pretty text in `ENVIRONMENT=local` and JSON elsewhere.

## Migrations

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

See `docs/LOCAL_DEV.md` for full stack development.

## Query API

| Method | Path | Notes |
| ------ | ---- | ----- |
| `POST` | `/api/v1/queries` | Submit topic; returns `job_id` |
| `GET` | `/api/v1/queries` | List jobs for current user |
| `GET` | `/api/v1/queries/{id}` | Stages, synthesis, sources, `llm_usage` |
| `GET` | `/api/v1/queries/{id}/stream` | SSE pipeline updates |

Local dev: set `AUTH_DISABLED=true` in `.env`. Regenerate OpenAPI after schema changes: `make openapi` from repo root.
