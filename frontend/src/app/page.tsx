import { Badge } from "@/components/ui/badge";
import { QueryHistory } from "@/components/dashboard/query-history";
import Link from "next/link";
import { ArrowRight, GitBranch, Layers, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const stages = [
  "Ingestion",
  "Embedding",
  "Knowledge",
  "Research",
  "Synthesis",
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-10 p-6 md:p-10">
      <section className="space-y-4">
        <Badge variant="secondary" className="font-mono text-[10px] uppercase">
          Event-driven research
        </Badge>
        <div className="max-w-2xl space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            Multi-agent research, orchestrated by events
          </h1>
          <p className="text-base leading-relaxed text-muted-foreground">
            Submit a topic and watch an async pipeline ingest sources, embed
            knowledge, run parallel research agents, and deliver a cited
            synthesis — with live pipeline visibility in React Flow.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button nativeButton={false} render={<Link href="/queries/new" />}>
            Start a query
            <ArrowRight data-icon="inline-end" />
          </Button>
          <Button
            variant="outline"
            nativeButton={false}
            render={<Link href="/queries/demo" />}
          >
            View sample job
          </Button>
        </div>
      </section>

      <QueryHistory />

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <Zap className="mb-1 size-4 text-primary" />
            <CardTitle>Async pipeline</CardTitle>
            <CardDescription>
              EventBridge stages with idempotency, DLQ, and correlation tracing.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <Layers className="mb-1 size-4 text-secondary" />
            <CardTitle>Real AI agents</CardTitle>
            <CardDescription>
              Tavily ingestion, RAG knowledge mining, parallel LLM research,
              cited synthesis.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <GitBranch className="mb-1 size-4 text-primary" />
            <CardTitle>Live dashboard</CardTitle>
            <CardDescription>
              SSE-driven React Flow updates as each stage completes.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">Pipeline stages</h2>
            <p className="text-sm text-muted-foreground">
              Five stages from query submission to cited report.
            </p>
          </div>
        </div>
        <Card>
          <CardContent className="flex flex-wrap gap-2 pt-4">
            {stages.map((stage, index) => (
              <div key={stage} className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-xs">
                  {String(index + 1).padStart(2, "0")}
                </Badge>
                <span className="text-sm">{stage}</span>
                {index < stages.length - 1 ? (
                  <ArrowRight className="size-3.5 text-muted-foreground" />
                ) : null}
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
