# EventForge Frontend

Next.js 16 App Router dashboard for the event-driven research pipeline.

## Features

- Query submit + job list/detail
- React Flow pipeline visualization
- SSE (`useJobStream`) — real-time stage updates via fetch
- shadcn/ui + Tailwind v4

## Routes

| Path            | Purpose                    |
| --------------- | -------------------------- |
| `/`             | Landing + recent queries   |
| `/queries/new`  | Submit a research query    |
| `/queries/[id]` | Pipeline graph + synthesis |

## Local dev

```bash
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open http://localhost:3000 — API calls use the backend mock user (no login). See [`docs/LOCAL_DEV.md`](../docs/LOCAL_DEV.md).

## Structure

```
frontend/src/
├── app/                    # App Router pages
├── components/
│   ├── ui/                 # shadcn/ui
│   ├── workflow/           # React Flow nodes/edges
│   └── dashboard/          # Synthesis, sources, cost
├── hooks/useJobStream.ts   # SSE subscription
├── lib/api-client.ts       # Typed fetch (openapi-typescript)
└── types/                  # Generated from OpenAPI
```

Regenerate API types after backend OpenAPI changes:

```bash
npm run codegen
```
