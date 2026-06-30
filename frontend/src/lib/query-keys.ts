export const queryKeys = {
  queries: {
    all: ["queries"] as const,
    detail: (jobId: string) => ["queries", jobId] as const,
  },
} as const;
