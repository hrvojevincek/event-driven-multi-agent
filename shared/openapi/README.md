# OpenAPI Contracts

> **Cursor agents:** Frontend types generated from here. See `.cursor/rules/frontend-nextjs.mdc`.

Generated OpenAPI specs and shared types.

- `eventforge-api.yaml` — exported from FastAPI (`make export-openapi`)
- `frontend/src/types/api.ts` — generated via `openapi-typescript` (`make codegen` or `make openapi`)

## Regenerate

From repo root:

```bash
make openapi          # export spec + codegen (both steps)
make export-openapi   # FastAPI → eventforge-api.yaml only
make codegen          # yaml → frontend/src/types/api.ts only
```

Or from `frontend/`:

```bash
npm run codegen       # requires eventforge-api.yaml to exist first
```
