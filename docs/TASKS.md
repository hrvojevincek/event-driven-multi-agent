# EventForge — Task Roadmap

> **Cursor agents:** Check current phase here before implementing. Update checkboxes when done. Workflow rule: `.cursor/rules/docs-workflow.mdc`.

Living roadmap for EventForge development. Structured for **Linear integration** — each phase maps to a Milestone; checkbox items map to Issues.

**Linear (active):** [EventForge project](https://linear.app/kreativbiro/project/eventforge-f35070f0931e) — see `docs/LINEAR.md` for issue index.

**How to use:**

> "What's next in EventForge?" · "Implement KRE-118" · "Mark KRE-117 done"

When an issue closes → check the matching box below and ensure `KRE-xxx` link is present.

---

## Phase 0: Foundation & Documentation

**Goal:** Project structure, documentation, and local infrastructure skeleton.  
**Status:** Complete

- [x] Define folder structure and repo scaffold
- [x] Create `CLAUDE.md` (AI context)
- [x] Create `.cursor/rules/` (Cursor IDE agent rules)
- [x] Create `AGENTS.md` (Cursor agent entry point)
- [x] Create `docs/PRD.md`
- [x] Create `docs/ARCHITECTURE.md`
- [x] Create `docs/TECH_DECISIONS.md`
- [x] Create `docs/TASKS.md`
- [x] Create `docs/LOCAL_DEV.md`
- [x] Add `docker-compose.yml` (Postgres + pgvector, LocalStack)
- [x] Add `.env.example`, `.gitignore`, `Makefile`, `README.md`
- [x] Add LocalStack init script for EventBridge + SQS
- [x] Create Linear EventForge project + Phase 0/1 issues (`docs/LINEAR.md`)
- [x] Initialize git repository and first commit → [KRE-117](https://linear.app/kreativbiro/issue/KRE-117)
- [x] Verify `make dev` starts infrastructure cleanly → [KRE-117](https://linear.app/kreativbiro/issue/KRE-117)

---

## Phase 1: Application Scaffolding

**Goal:** Runnable FastAPI backend with health checks and DB connection. Frontend deferred to Phase 4 (backend-first).

### 1.1 Backend Scaffold

→ [KRE-118](https://linear.app/kreativbiro/issue/KRE-118) · [KRE-120](https://linear.app/kreativbiro/issue/KRE-120) · [KRE-123](https://linear.app/kreativbiro/issue/KRE-123) · [KRE-125](https://linear.app/kreativbiro/issue/KRE-125)

- [x] Initialize `backend/` with `pyproject.toml` (uv) — KRE-118
- [x] Create `src/eventforge/` package structure — KRE-118
- [x] FastAPI app with `/health` and `/health/ready` endpoints — KRE-120
- [x] SQLAlchemy 2.0 + Alembic setup — KRE-123
- [x] Core models: `User`, `Job`, `JobStage`, `ProcessedEvent` — KRE-123
- [x] Config via `pydantic-settings` from `.env` — KRE-125
- [x] Structured logging (JSON in prod, pretty in local) — KRE-125
- [x] Dockerfile for backend — KRE-125
- [x] Uncomment backend service in `docker-compose.yml` — KRE-125

### 1.2 Shared Contracts

→ [KRE-126](https://linear.app/kreativbiro/issue/KRE-126) · [KRE-122](https://linear.app/kreativbiro/issue/KRE-122) · [KRE-127](https://linear.app/kreativbiro/issue/KRE-127) · [KRE-128](https://linear.app/kreativbiro/issue/KRE-128)

- [ ] OpenAPI spec generation from FastAPI — KRE-126 (frontend codegen deferred to Phase 4)
- [x] Event envelope + `query.submitted` JSON schemas (mini-122) — KRE-122
- [x] CI lint workflow (ruff; eslint when frontend exists) — KRE-127

**Phase 1 exit criteria (backend):** `make dev` runs infra + backend; `/health` and `/health/ready` return 200; migrations apply cleanly.

> **Backend-first:** Phase 2+ does not wait for frontend. Full-stack smoke test → [KRE-128](https://linear.app/kreativbiro/issue/KRE-128) moves to Phase 4.

---

## Phase 2: Core Pipeline (Local)

**Goal:** End-to-end query submission → event publishing → worker processing (mocked LLM) → DB persistence.

**Strategy:** Vertical slices + incremental event schemas (see `docs/LINEAR.md` backend-first track).

### 2.0 Vertical slices (Linear)

→ [KRE-129](https://linear.app/kreativbiro/issue/KRE-129) · [KRE-130](https://linear.app/kreativbiro/issue/KRE-130) · [KRE-131](https://linear.app/kreativbiro/issue/KRE-131)

- [x] `POST /api/v1/queries` + EventBridge publisher + idempotency — KRE-129
- [x] SQS consumer base + ingestion stub worker (+ `ingestion.completed` schema) — KRE-130
- [x] Harden idempotency: atomic `try_claim` + composite PK `(event_id, worker_name)` — KRE-131 (optional `Idempotency-Key` deferred → KRE-132)

### 2.1 API & Data Layer

- [x] `GET /api/v1/queries/{id}` — job detail with stages
- [x] `GET /api/v1/queries` — list user queries (mock user for now)
- [x] Include synthesis report on `GET /api/v1/queries/{id}` when available

### 2.2 Workers (Stub Agents)

- [x] Embedding worker (mock: store fake chunks in Postgres via pgvector) + `embedding.completed` schema
- [x] Knowledge mining worker (mock: extract fake entities) + `knowledge.mined` schema
- [x] Research worker (mock: generate fake research notes) + `research.task.*` schemas
- [x] Synthesis worker (mock: combine into markdown report) + `synthesis.completed` schema
- [x] Wire EventBridge rules → SQS queues (LocalStack)

### 2.3 Orchestration

- [x] Sequential event chaining (ingestion → embedding → knowledge → research → synthesis)
- [x] Research fan-out: dispatch N tasks (simplified local — skip Step Functions initially)
- [x] SQS redrive policies → `eventforge-dlq` (LocalStack, maxReceiveCount: 3) — [KRE-134](https://linear.app/kreativbiro/issue/KRE-134)
- [x] `pipeline.failed` event + schema + terminal failure handling — [KRE-135](https://linear.app/kreativbiro/issue/KRE-135)
- [x] Update `JobStage` status in Postgres at each step

**Phase 2 exit criteria:** Submit query via API → all stages complete → result in DB (mocked LLM). Verified via `./scripts/verify-pipeline-e2e.sh`.

---

## Phase 3: Real AI Agents & Auth

**Goal:** Replace stub agents with real LLM calls, web search, embeddings, and backend authentication. Test via Postman/curl before any UI.

### 3.1 LLM Integration

- [x] LLM client abstraction (OpenAI + Anthropic)
- [ ] Ingestion: Tavily web search
- [ ] Embedding: chunk real content + OpenAI `text-embedding-3-small`
- [ ] Knowledge mining: RAG retrieval + entity extraction
- [ ] Research: parallel focused sub-queries with LLM
- [ ] Synthesis: structured report generation with citations
- [ ] Cost tracking (`llm_usage` table + API endpoint) — table + repository done; API endpoint pending

### 3.2 Authentication (backend)

- [ ] JWT validation middleware in FastAPI (Clerk JWKS)
- [ ] User-scoped job queries
- [ ] Replace mock user with authenticated `user_id` on all job records

### 3.3 Resilience Hardening

- [ ] LLM retry with exponential backoff
- [ ] Circuit breaker per provider
- [ ] Per-query cost cap enforcement

**Phase 3 exit criteria:** Real research query via API produces cited synthesis; backend auth enforced; LLM costs tracked. Verified via Postman + `./scripts/verify-pipeline-e2e.sh`.

---

## Phase 4: Frontend Experience & Real-Time

**Goal:** Interactive dashboard with live React Flow pipeline visualization (after backend + real agents are solid).

### 4.0 Frontend Scaffold

→ [KRE-119](https://linear.app/kreativbiro/issue/KRE-119) · [KRE-121](https://linear.app/kreativbiro/issue/KRE-121) · [KRE-124](https://linear.app/kreativbiro/issue/KRE-124) · [KRE-126](https://linear.app/kreativbiro/issue/KRE-126) · [KRE-128](https://linear.app/kreativbiro/issue/KRE-128)

- [ ] Initialize Next.js 15 with TypeScript, Tailwind, App Router — KRE-119
- [ ] Install and configure shadcn/ui — KRE-119
- [ ] Basic layout: header, sidebar, main content area — KRE-121
- [ ] Placeholder pages: `/` (home), `/queries/new`, `/queries/[id]` — KRE-121
- [ ] API client setup with env-based `NEXT_PUBLIC_API_URL` — KRE-124
- [ ] `openapi-typescript` codegen from backend OpenAPI — KRE-126
- [ ] Dockerfile for frontend — KRE-124
- [ ] Uncomment frontend service in `docker-compose.yml` — KRE-124
- [ ] Phase 4 full-stack integration smoke test — KRE-128

### 4.1 Real-Time Streaming

- [ ] SSE endpoint: `GET /api/v1/queries/{id}/stream`
- [ ] Publish stage events to SSE subscribers
- [ ] Frontend `useJobStream` hook

### 4.2 React Flow Visualization

- [ ] Pipeline node components (pending, running, completed, failed)
- [ ] Animated edges on active stage
- [ ] Auto-layout pipeline graph
- [ ] Stage detail panel on node click (duration, agent name)

### 4.3 Dashboard UI

- [ ] Query submission form (topic, depth, max_sources)
- [ ] Results viewer (markdown rendering)
- [ ] Source list with expandable snippets
- [ ] Job history page

### 4.4 Authentication (Clerk UI)

- [ ] Clerk integration in Next.js
- [ ] Pass JWT to API client; protected routes via Clerk middleware

### 4.5 Observability (Local)

- [ ] OTEL SDK in FastAPI + workers
- [ ] OTEL collector in docker-compose
- [ ] Verify traces in local Jaeger or Grafana

**Phase 4 exit criteria:** Submit query in UI → watch React Flow update live → view real synthesis result. → [KRE-128](https://linear.app/kreativbiro/issue/KRE-128)

---

## Phase 5: AWS Deployment

**Goal:** Production-grade deployment to AWS dev environment.

### 5.1 Infrastructure (Terraform)

- [ ] `modules/networking` — VPC, subnets, security groups
- [ ] `modules/rds` — Postgres with backups
- [ ] `modules/eventbridge` — event bus + rules
- [ ] `modules/sqs` — queues + DLQ + redrive
- [ ] `modules/step-functions` — research fan-out workflow
- [ ] `modules/ecs` — API + worker services (Fargate)
- [ ] `modules/observability` — CloudWatch, ADOT
- [ ] `environments/dev` — compose modules
- [ ] Secrets Manager for API keys

### 5.2 CI/CD

- [ ] GitHub Actions: lint + test on PR
- [ ] Docker build + push to ECR
- [ ] Terraform plan on PR, apply on merge to main
- [ ] Frontend deploy to Vercel (or S3 + CloudFront)

### 5.3 Step Functions

- [ ] Research fan-out Map state
- [ ] Wait for all research completions
- [ ] Trigger synthesis on completion

**Phase 5 exit criteria:** Deployed to AWS dev; end-to-end query works in cloud.

---

## Phase 6: Polish & Portfolio

**Goal:** Demo-ready portfolio piece.

- [ ] README with architecture diagram and demo GIF
- [ ] Admin DLQ replay endpoint + simple UI
- [ ] Playwright E2E test for happy path
- [ ] Performance: P95 latency benchmarks
- [ ] Cost dashboard panel in UI
- [ ] Export synthesis as Markdown download
- [ ] Demo seed script with impressive sample query
- [ ] Automated RAG eval (faithfulness, citation accuracy, RAGAS-style metrics) → [KRE-133](https://linear.app/kreativbiro/issue/KRE-133)

---

## Backlog (Post-MVP)

- [ ] PDF / document upload ingestion (S3 + Textract)
- [ ] PGVector migration option
- [ ] Temporal orchestration migration (ADR-008)
- [ ] Team workspaces / org model
- [ ] Scheduled recurring research
- [ ] Knowledge graph visualization (beyond pipeline flow)
- [ ] Human-in-the-loop pipeline pauses
- [ ] Bi-directional Linear sync (issue status → TASKS.md)
- [ ] WebSocket upgrade if SSE insufficient
- [ ] Multi-region considerations

---

## Linear Integration Template

When creating Linear issues, use this format:

```
Title:       [Phase X.Y] <task description>
Description: <acceptance criteria from checkbox>
Labels:      phase-N, backend|frontend|infra|agents
Priority:    P0–P3 (map from PRD)
Estimate:    1–5 points
Blocked by:  <dependency issue if any>
```

### Suggested Linear Project Structure

```
Project: EventForge
├── Milestone: Phase 0 — Foundation
├── Milestone: Phase 1 — Scaffolding
├── Milestone: Phase 2 — Core Pipeline
├── Milestone: Phase 3 — Real AI & Auth
├── Milestone: Phase 4 — Frontend & Real-Time
├── Milestone: Phase 5 — AWS Deployment
└── Milestone: Phase 6 — Polish
```

---

## Current Priority

**Backend-first track:** Phase 2 core pipeline complete (E2E + DLQ + `pipeline.failed`). **Next: Phase 3** — real AI agents (Tavily, embeddings, LLM). Frontend + SSE/React Flow deferred to **Phase 4** ([KRE-119](https://linear.app/kreativbiro/issue/KRE-119) onward).

Verify: `./scripts/verify-pipeline-e2e.sh` · `./scripts/verify-dlq-redrive.sh` · run DLQ worker: `uv run --project backend python -m eventforge.workers.dlq`
