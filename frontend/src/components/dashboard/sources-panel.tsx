"use client";

import { ExternalLink } from "lucide-react";

import type { QueryDetail } from "@/lib/api-client";

type SourcesPanelProps = {
  detail: QueryDetail | undefined;
  isLoading: boolean;
};

export function SourcesPanel({ detail, isLoading }: SourcesPanelProps) {
  if (isLoading && !detail) {
    return (
      <p className="rounded-lg border border-dashed border-border p-3 text-sm text-muted-foreground">
        Loading sources…
      </p>
    );
  }

  const sources = detail?.sources ?? [];

  if (sources.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-border p-3 text-sm text-muted-foreground">
        Sources appear after ingestion completes.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {sources.map((source) => (
        <li key={source.id}>
          <details className="group rounded-lg border border-border bg-muted/10">
            <summary className="cursor-pointer list-none px-3 py-2.5 text-sm font-medium marker:content-none [&::-webkit-details-marker]:hidden">
              <div className="flex items-start justify-between gap-2">
                <span className="line-clamp-2">{source.title}</span>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-muted-foreground hover:text-primary"
                  onClick={(event) => event.stopPropagation()}
                  aria-label={`Open ${source.title}`}
                >
                  <ExternalLink className="size-3.5" />
                </a>
              </div>
            </summary>
            <div className="space-y-2 border-t border-border px-3 py-2.5 text-sm text-muted-foreground">
              <p className="line-clamp-4">{source.snippet}</p>
              <p className="truncate font-mono text-xs">{source.url}</p>
            </div>
          </details>
        </li>
      ))}
    </ul>
  );
}
