# Event Schemas

> **Cursor agents:** Pipeline rules in `.cursor/rules/event-pipeline.mdc`. Define schemas here before backend Pydantic models.

Canonical event contracts shared between backend publishers, workers, and Step Functions.

## Conventions

- EventBridge `detail-type`: `eventforge.<domain>.<action>` (e.g. `eventforge.query.submitted`)
- Envelope fields: `event_id`, `correlation_id`, `job_id`, `timestamp`, `schema_version`, `detail_type`, `payload`
- JSON Schema in this directory; mirrored as Pydantic in `backend/src/eventforge/events/schemas/`

## Incremental schema policy (mini-122)

Define schemas **when the producer is implemented**, not all upfront:

| When              | Schema                                                |
| ----------------- | ----------------------------------------------------- |
| KRE-122           | Shared envelope + `query.submitted`                   |
| KRE-130           | `ingestion.completed`                                 |
| Phase 2.2         | `embedding.completed`                                 |
| Phase 2.2         | `knowledge.mined`                                     |
| Phase 2.2         | `research.task.dispatched`, `research.task.completed` |
| Phase 2.2         | `synthesis.completed`                                 |
| Each later worker | That stage's output event                             |
| Phase 2.3 (DLQ)   | `pipeline.failed` when terminal failure is recorded   |

## Schema index

| File                                   | Status           | Producer   | Consumer              |
| -------------------------------------- | ---------------- | ---------- | --------------------- |
| `envelope.schema.json`                 | Done (KRE-122)   | All        | All                   |
| `query.submitted.schema.json`          | Done (KRE-122)   | API        | Ingestion worker      |
| `ingestion.completed.schema.json`      | Done (KRE-130)   | Ingestion  | Embedding worker      |
| `embedding.completed.schema.json`      | Done (Phase 2.2) | Embedding  | Knowledge worker      |
| `knowledge.mined.schema.json`          | Done (Phase 2.2) | Knowledge  | Research orchestrator |
| `research.task.dispatched.schema.json` | Done (Phase 2.2) | Research   | Research workers      |
| `research.task.completed.schema.json`  | Done (Phase 2.2) | Research   | Synthesis             |
| `synthesis.completed.schema.json`      | Done (Phase 2.2) | Synthesis  | API / SSE             |
| `pipeline.failed.schema.json`          | Done (Phase 2.3) | DLQ worker | Alerting / SSE        |

## Planned pipeline (reference)

```
query.submitted → ingestion.completed → embedding.completed → knowledge.mined
  → research.task.dispatched (×N) → research.task.completed (×N)
  → synthesis.completed
```

See `docs/ARCHITECTURE.md` §3 for sequence diagram.
