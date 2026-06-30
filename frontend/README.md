# EventForge Frontend

Next.js 16 App Router dashboard for the EventForge research pipeline.

## Stack

- Next.js 16, TypeScript, Tailwind CSS, shadcn/ui
- TanStack Query — query list, detail, submit
- React Flow — live pipeline graph on `/queries/[id]`
- SSE (`useJobStream`) — real-time stage updates
- OpenAPI codegen — `npm run codegen` → `src/types/api.ts`

## Pages

| Route | Purpose |
| ----- | ------- |
| `/` | Landing + recent job history |
| `/queries/new` | Submit research query |
| `/queries/[id]` | Live pipeline, synthesis, sources, cost |

## Local dev

```bash
cp .env.example .env   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev            # http://localhost:3000
```

Backend must run with `AUTH_DISABLED=true` for local UI (no Cognito sign-in yet — Phase 4.4).

```bash
# repo root
make dev               # full stack via Docker Compose
# or hybrid: infra + backend + frontend natively (see docs/LOCAL_DEV.md)
make workers           # required for pipeline to complete
```

## Scripts

```bash
npm run dev       # dev server
npm run build     # production build
npm run lint      # ESLint
npm run codegen   # regenerate types from backend OpenAPI
```

From repo root: `make openapi` exports OpenAPI + runs codegen.

## Structure

```
src/
├── app/                    # App Router pages
├── components/
│   ├── dashboard/          # submit form, history, synthesis, sources, cost
│   ├── workflow/           # React Flow pipeline graph
│   ├── layout/             # shell, sidebar, header
│   └── ui/                 # shadcn/ui
├── hooks/
│   ├── useJobStream.ts     # SSE subscription
│   └── use-queries.ts      # TanStack Query hooks
└── lib/api-client.ts       # typed fetch wrapper
```

Docs: [`docs/LOCAL_DEV.md`](../docs/LOCAL_DEV.md) · Linear: [KRE-153](https://linear.app/kreativbiro/issue/KRE-153) (Phase 4.3)
