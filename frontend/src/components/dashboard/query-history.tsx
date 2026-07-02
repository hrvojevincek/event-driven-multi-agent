"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Trash2 } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useDeleteQuery, useQueryList } from "@/hooks/use-queries";

type PendingDelete = {
  jobId: string;
  topic: string;
};

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
  const deleteQuery = useDeleteQuery();
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(
    null,
  );

  async function confirmDelete() {
    if (!pendingDelete) {
      return;
    }
    await deleteQuery.mutateAsync(pendingDelete.jobId);
    setPendingDelete(null);
  }

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
              <Link
                href="/queries/new"
                className="text-primary hover:underline"
              >
                Submit your first topic
              </Link>
              .
            </p>
          ) : null}
          {data && data.length > 0 ? (
            <ul className="divide-y divide-border">
              {data.map((job) => (
                <li key={job.job_id}>
                  <div className="group flex items-center justify-between gap-2 py-3 -mx-2 px-2 rounded-lg hover:bg-muted/30">
                    <Link
                      href={`/queries/${job.job_id}`}
                      className="flex min-w-0 flex-1 items-center justify-between gap-4"
                    >
                      <div className="min-w-0 space-y-1">
                        <p className="truncate text-sm font-medium">
                          {job.topic}
                        </p>
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
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Delete ${job.topic}`}
                      disabled={
                        deleteQuery.isPending &&
                        deleteQuery.variables === job.job_id
                      }
                      onClick={() => {
                        setPendingDelete({
                          jobId: job.job_id,
                          topic: job.topic,
                        });
                      }}
                      className="shrink-0 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open && !deleteQuery.isPending) {
            setPendingDelete(null);
          }
        }}
      >
        <AlertDialogContent size="default">
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-destructive/10 text-destructive">
              <Trash2 />
            </AlertDialogMedia>
            <AlertDialogTitle>Delete this job?</AlertDialogTitle>
            <AlertDialogDescription>
              {pendingDelete ? (
                <>
                  <span className="font-medium text-foreground">
                    {pendingDelete.topic}
                  </span>{" "}
                  will be permanently removed, including pipeline history and
                  results. This cannot be undone.
                </>
              ) : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteQuery.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={deleteQuery.isPending}
              onClick={() => {
                void confirmDelete();
              }}
            >
              {deleteQuery.isPending ? "Deleting…" : "Delete job"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
