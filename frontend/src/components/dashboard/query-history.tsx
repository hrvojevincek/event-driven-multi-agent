"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useQueryList } from "@/hooks/use-queries";

function statusVariant(
  status: string,
): "default" | "secondary" | "outline" | "destructive" {
  if (status === "completed") {
    return "secondary";
  }
  if (status === "failed") {
    return "destructive";
  }
  if (status === "running" || status === "pending") {
    return "outline";
  }
  return "outline";
}

function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const deltaMs = Date.now() - date.getTime();
  const minutes = Math.floor(deltaMs / 60_000);
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  return date.toLocaleDateString();
}

export function QueryHistory() {
  const { data, isLoading, error } = useQueryList();

  return (
    <section className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-medium">Recent queries</h2>
          <p className="text-sm text-muted-foreground">
            Your research jobs, newest first.
          </p>
        </div>
        <Link
          href="/queries/new"
          className="text-sm text-primary hover:underline"
        >
          New query
        </Link>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Job history</CardTitle>
          <CardDescription>
            Click a job to open the live pipeline view.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading jobs…</p>
          ) : null}
          {error ? (
            <p className="text-sm text-destructive">
              Failed to load jobs. Is the API running?
            </p>
          ) : null}
          {!isLoading && !error && (data?.length ?? 0) === 0 ? (
            <p className="text-sm text-muted-foreground">
              No queries yet.{" "}
              <Link href="/queries/new" className="text-primary hover:underline">
                Submit your first topic
              </Link>
              .
            </p>
          ) : null}
          {data && data.length > 0 ? (
            <ul className="divide-y divide-border">
              {data.map((job) => (
                <li key={job.job_id}>
                  <Link
                    href={`/queries/${job.job_id}`}
                    className="group flex items-center justify-between gap-4 py-3 transition-colors hover:bg-muted/30 -mx-2 px-2 rounded-lg"
                  >
                    <div className="min-w-0 space-y-1">
                      <p className="truncate text-sm font-medium">{job.topic}</p>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge
                          variant={statusVariant(job.status)}
                          className="font-mono text-[10px] uppercase"
                        >
                          {job.status.replaceAll("_", " ")}
                        </Badge>
                        <span>{job.depth}</span>
                        <span>{formatRelativeTime(job.created_at)}</span>
                      </div>
                    </div>
                    <ArrowRight className="size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}
