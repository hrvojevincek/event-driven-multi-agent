# EventForge — Linear Integration

> **Source of truth for active work:** [Linear EventForge project](https://linear.app/kreativbiro/project/eventforge-f35070f0931e)  
> **Mirror:** `docs/TASKS.md` checkboxes + `KRE-xxx` links (update when issues close)

## Workspace

| Item | Value |
|------|-------|
| Team | `Kreativbiro` (key: `KRE`) |
| Project | [EventForge](https://linear.app/kreativbiro/project/eventforge-f35070f0931e) |
| Target | Phase 1 by 2026-07-15 |

## Agent workflow (Cursor + Linear MCP)

1. **Start session:** `list_issues` with `project: EventForge` (or `get_issue` for a specific `KRE-xxx`)
2. **Pick work:** Prefer unblocked issues in current milestone; respect `blockedBy`
3. **Implement:** Use acceptance criteria from issue description + `.cursor/rules/`
4. **On complete:** Mark issue Done in Linear + check box in `docs/TASKS.md`

### MCP commands

```
list_issues(project: "EventForge")
get_issue(id: "KRE-122")
save_issue(id: "KRE-122", state: "Done")
```

## Milestones

| Milestone | Status |
|-----------|--------|
| Phase 0 — Foundation | Complete |
| Phase 1 — Scaffolding | In progress (backend done; frontend deferred) |
| Phase 2 — Core Pipeline | Active (backend-first vertical slices) |

## Issue index (Phase 0 + 1)

| ID | Linear | Title | Estimate | Blocked by |
|----|--------|-------|----------|------------|
| EF-001 | [KRE-117](https://linear.app/kreativbiro/issue/KRE-117) | Close Phase 0 — git init + docker verify | 2 | — |
| EF-002 | [KRE-118](https://linear.app/kreativbiro/issue/KRE-118) | Backend project init — uv + package layout | 2 | KRE-117 |
| EF-003 | [KRE-120](https://linear.app/kreativbiro/issue/KRE-120) | FastAPI app + health endpoints | 2 | KRE-118 |
| EF-004 | [KRE-123](https://linear.app/kreativbiro/issue/KRE-123) | DB layer — SQLAlchemy, Alembic, core models | 3 | KRE-120 |
| EF-005 | [KRE-125](https://linear.app/kreativbiro/issue/KRE-125) | Config, logging, Dockerfile, compose wiring | 3 | KRE-123 |
| EF-006 | [KRE-119](https://linear.app/kreativbiro/issue/KRE-119) | Frontend init — Next.js 15, Tailwind, shadcn | 3 | KRE-117 |
| EF-007 | [KRE-121](https://linear.app/kreativbiro/issue/KRE-121) | Frontend layout + placeholder pages | 3 | KRE-119 |
| EF-008 | [KRE-124](https://linear.app/kreativbiro/issue/KRE-124) | Frontend API client + Dockerfile + compose | 2 | KRE-121 |
| EF-009 | [KRE-126](https://linear.app/kreativbiro/issue/KRE-126) | OpenAPI generation + TypeScript codegen | 2 | KRE-120, KRE-124 |
| EF-010 | [KRE-122](https://linear.app/kreativbiro/issue/KRE-122) | Event envelope + query.submitted schemas (mini-122) | 1 | KRE-118 |
| EF-011 | [KRE-127](https://linear.app/kreativbiro/issue/KRE-127) | CI stub — lint workflow | 1 | KRE-125 (backend); KRE-124 (eslint) |
| EF-012 | [KRE-128](https://linear.app/kreativbiro/issue/KRE-128) | Phase 1 integration smoke test | 2 | KRE-125, KRE-124, KRE-126, KRE-122, KRE-127 |

## Issue index (Phase 2 — vertical slices)

| ID | Linear | Title | Estimate | Blocked by |
|----|--------|-------|----------|------------|
| EF-013 | [KRE-129](https://linear.app/kreativbiro/issue/KRE-129) | Query API + EventBridge publisher + idempotency | 3 | KRE-122 |
| EF-014 | [KRE-130](https://linear.app/kreativbiro/issue/KRE-130) | SQS consumer base + ingestion stub worker | 3 | KRE-129 |
| EF-015 | [KRE-131](https://linear.app/kreativbiro/issue/KRE-131) | Harden pipeline idempotency (atomic claim + API keys) | 2 | KRE-130 |

> Remaining Phase 2 work (embedding → synthesis workers, orchestration, DLQ) stays in `docs/TASKS.md` until split into Linear issues. **Stage event schemas are added incrementally with each worker** — not upfront in KRE-122.

## Backend-first track (recommended)

```
Done:   KRE-118 → KRE-120 → KRE-123 → KRE-125

Done:   KRE-118 → KRE-120 → KRE-123 → KRE-125 → KRE-122 → KRE-129 → KRE-130

Next:   KRE-131 (idempotency hardening — atomic claim + API keys)

Parallel (optional): KRE-127 backend ruff job only

Defer:  KRE-119 → KRE-121 → KRE-124 → KRE-126 → KRE-128 (Phase 1 full-stack exit)
```

## Parallel tracks (original Phase 1)

```
Track A (backend): KRE-118 → KRE-120 → KRE-123 → KRE-125 → KRE-127
Track B (frontend): KRE-119 → KRE-121 → KRE-124 → KRE-127
Parallel: KRE-122 (after KRE-118), KRE-126 (after KRE-120 + KRE-124)
Finish: KRE-128
```

## Labels

`phase-0`, `phase-1`, `phase-2`, `backend`, `frontend`, `infra`, `docs`, `workflows`, `agents`, `observability`, `Feature`

## User shortcuts

| Say this | Agent does |
|----------|------------|
| "What's next in EventForge?" | `list_issues` → suggest unblocked work |
| "Implement KRE-122" | Mini-122 schemas + Pydantic mirror |
| "Implement KRE-129" | Query API + EventBridge publisher |
| "Mark KRE-117 done" | Close in Linear + update TASKS.md |

## Grill-me decisions (2025-06-20)

- Scope: Phase 0 + Phase 1 only (~12 grouped issues)
- Linear = active source; TASKS.md = mirror
- New EventForge project on Kreativbiro
- Backend: `uv`
- Phase 1 includes lint-only CI stub

## Plan revision (2026-06-21)

- **Mini-122:** KRE-122 scoped to envelope + `query.submitted` only (1 pt)
- **Backend-first:** Phase 2 vertical slices (KRE-129, KRE-130) may start before Phase 1 frontend exit
- **Incremental schemas:** remaining pipeline events defined when each worker is built
- Phase 1 exit (KRE-128) still requires frontend — do not block pipeline work on it
