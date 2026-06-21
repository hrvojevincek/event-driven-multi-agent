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

## Migrations

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

See `docs/LOCAL_DEV.md` for full stack development.
