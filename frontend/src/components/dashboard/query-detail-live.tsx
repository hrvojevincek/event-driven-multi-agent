"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CostPanel } from "@/components/dashboard/cost-panel";
import { SourcesPanel } from "@/components/dashboard/sources-panel";
import { SynthesisViewer } from "@/components/dashboard/synthesis-viewer";
import { PipelineGraph } from "@/components/workflow/pipeline-graph";
import { useQueryDetail } from "@/hooks/use-queries";
import { useJobStream } from "@/hooks/useJobStream";
import { queryKeys } from "@/lib/query-keys";

type QueryDetailLiveProps = {
  jobId: string;
};

function jobStatusLabel(status: string | null): string {
  if (!status) {
    return "connecting…";
  }
  return status.replaceAll("_", " ");
}

export function QueryDetailLive({ jobId }: QueryDetailLiveProps) {
  const stream = useJobStream(jobId);
  const queryClient = useQueryClient();
  const jobStatus = stream.jobStatus ?? null;
  const detailQuery = useQueryDetail(jobId, jobStatus);

  useEffect(() => {
    if (jobStatus === "completed" || jobStatus === "failed") {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.queries.detail(jobId),
      });
    }
  }, [jobId, jobStatus, queryClient]);

  const displayStatus = jobStatus ?? detailQuery.data?.status ?? null;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 p-6 md:p-10">
      <div className="space-y-2">
        <Badge variant="secondary" className="font-mono text-[10px] uppercase">
          Job detail
        </Badge>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">
            {detailQuery.data?.topic ?? "Query job"}
          </h1>
          <Badge variant="outline" className="font-mono text-xs">
            {jobId}
          </Badge>
          <Badge
            variant={stream.connected ? "secondary" : "outline"}
            className="font-mono text-[10px] uppercase"
          >
            {stream.connected ? "Live" : "Reconnecting"}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Pipeline graph updates in real time via SSE. Click a stage for
          details.
        </p>
        {stream.correlationId ? (
          <p className="font-mono text-xs text-muted-foreground">
            correlation_id: {stream.correlationId}
          </p>
        ) : null}
        {stream.error ? (
          <p className="text-sm text-destructive">{stream.error}</p>
        ) : null}
        {detailQuery.error ? (
          <p className="text-sm text-destructive">
            Failed to load job detail from API.
          </p>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card className="min-h-80">
          <CardHeader>
            <CardTitle>Pipeline</CardTitle>
            <CardDescription>
              Job status:{" "}
              <span className="font-mono uppercase">
                {jobStatusLabel(displayStatus)}
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PipelineGraph stages={stream.stages} />
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Synthesis</CardTitle>
              <CardDescription>
                Markdown report with citations appears when the job completes.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SynthesisViewer
                detail={detailQuery.data}
                jobStatus={displayStatus}
                isLoading={detailQuery.isLoading}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sources</CardTitle>
              <CardDescription>
                Expandable snippets from ingested documents and web results.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SourcesPanel
                detail={detailQuery.data}
                isLoading={detailQuery.isLoading}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cost</CardTitle>
              <CardDescription>
                Token usage and estimated spend from{" "}
                <code className="font-mono text-xs">llm_usage</code>.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CostPanel
                detail={detailQuery.data}
                isLoading={detailQuery.isLoading}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
