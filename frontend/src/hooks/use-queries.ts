"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteQuery,
  getQueryDetail,
  listQueries,
  submitQuery,
  type SubmitQueryRequest,
} from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";

export function useQueryList() {
  return useQuery({
    queryKey: queryKeys.queries.all,
    queryFn: listQueries,
  });
}

export function useQueryDetail(jobId: string, jobStatus: string | null) {
  return useQuery({
    queryKey: queryKeys.queries.detail(jobId),
    queryFn: () => getQueryDetail(jobId),
    refetchInterval: () => {
      if (jobStatus === "completed" || jobStatus === "failed") {
        return false;
      }
      return 5_000;
    },
  });
}

export function useSubmitQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: SubmitQueryRequest) => submitQuery(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.queries.all });
    },
  });
}

export function useDeleteQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => deleteQuery(jobId),
    onSuccess: (_data, jobId) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.queries.all });
      void queryClient.removeQueries({ queryKey: queryKeys.queries.detail(jobId) });
    },
  });
}
