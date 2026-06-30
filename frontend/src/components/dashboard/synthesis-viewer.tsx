"use client";

import Markdown from "react-markdown";

import type { QueryDetail } from "@/lib/api-client";

type SynthesisViewerProps = {
  detail: QueryDetail | undefined;
  jobStatus: string | null;
  isLoading: boolean;
};

export function SynthesisViewer({
  detail,
  jobStatus,
  isLoading,
}: SynthesisViewerProps) {
  if (isLoading && !detail) {
    return (
      <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
        Loading report…
      </p>
    );
  }

  const report = detail?.synthesis_report;

  if (report) {
    return (
      <article className="markdown-body rounded-lg border border-border bg-muted/20 p-4 text-sm">
        <Markdown>{report.content}</Markdown>
      </article>
    );
  }

  if (jobStatus === "failed") {
    return (
      <p className="rounded-lg border border-dashed border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
        Pipeline failed before synthesis completed.
      </p>
    );
  }

  if (jobStatus === "completed") {
    return (
      <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
        Job finished but no synthesis report was returned.
      </p>
    );
  }

  return (
    <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
      Report will appear when synthesis completes.
    </p>
  );
}
