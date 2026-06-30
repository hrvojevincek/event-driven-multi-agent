# EventForge — Cursor Agent Guide

> **You are working in Cursor IDE.** Project context is loaded automatically from `.cursor/rules/`. This file is the entry point for agent sessions.

## What to read

| Priority | Source | When |
|----------|--------|------|
| 1 | `.cursor/rules/eventforge-core.mdc` | Always (auto-applied) |
| 2 | `.cursor/rules/*.mdc` matching open files | File-specific context |
| 3 | **Linear MCP** (`list_issues`, `get_issue`) | **Current work — prefer over TASKS.md** |
| 4 | `docs/LINEAR.md` | Issue index, blockers, parallel tracks |
| 5 | `docs/TASKS.md` | Phase progress mirror |
| 6 | `docs/ARCHITECTURE.md` | Pipeline, events, data flow |
| 7 | `docs/TECH_DECISIONS.md` | Before changing stack or patterns |
| 8 | `docs/PRD.md` | Product scope and user stories |
| 9 | `docs/LOCAL_DEV.md` | Local setup and troubleshooting |

## Project summary

**EventForge** — event-driven multi-agent research platform.

- User submits query → EventBridge triggers agent pipeline → results in dashboard with React Flow
- Hybrid: Next.js frontend + FastAPI backend + AWS events (EventBridge/SQS/Step Functions)
- Data: Postgres + pgvector | Auth: AWS Cognito | Observability: OpenTelemetry

## Current status

**Phases 0–4 complete.** **Phase 5 in progress** — Terraform modules + deploy hardening done ([KRE-156](https://linear.app/kreativbiro/issue/KRE-156)–[KRE-162](https://linear.app/kreativbiro/issue/KRE-162)). **Next:** first AWS apply + ECR. Index: `docs/LINEAR.md`

## Commands

```bash
./scripts/setup-local.sh && make dev   # start local infra
make down                              # stop
```

## Agent rules

1. Surgical diffs — don't over-engineer
2. Event schemas in `shared/events/` before backend code
3. Production patterns: idempotency, DLQ, OTEL spans, cost tracking
4. Update `docs/TASKS.md` checkboxes when done
5. Commit only when user explicitly requests
6. **Docstrings on classes** — new or touched Python classes get a one-line docstring (see `backend-python.mdc`)

## User shortcuts

| Say this | Agent does |
|----------|------------|
| "What's next in EventForge?" | Linear MCP → suggest unblocked `KRE-xxx` |
| "Implement KRE-118" | `get_issue` → implement acceptance criteria |
| "Implement Phase 3" | Follow Phase 3 — real AI agents in `docs/TASKS.md` |
| "Implement Phase 4" | Follow Phase 4 — frontend + SSE in `docs/LINEAR.md` |
| "Mark KRE-117 done" | Close in Linear + update `docs/TASKS.md` |

## Cursor rules map

```
.cursor/rules/
├── eventforge-core.mdc      alwaysApply — stack, architecture, behavior
├── backend-python.mdc       backend/**
├── frontend-nextjs.mdc      frontend/**
├── event-pipeline.mdc       agents, workers, events
├── infra-aws.mdc            infra, docker-compose
└── docs-workflow.mdc        docs, TASKS, workflow
```
