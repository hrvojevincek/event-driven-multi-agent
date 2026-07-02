import type { paths } from "@/types/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${getApiBaseUrl()}${normalizedPath}`;
  const headers = new Headers(init?.headers);

  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let body: unknown;
    try {
      body = await parseJson(response);
    } catch {
      body = undefined;
    }
    throw new ApiError(
      `API ${response.status}: ${response.statusText}`,
      response.status,
      body,
    );
  }

  return parseJson<T>(response);
}

export type HealthResponse =
  paths["/health"]["get"]["responses"][200]["content"]["application/json"];

export type QuerySummary =
  paths["/api/v1/queries"]["get"]["responses"][200]["content"]["application/json"][number];

export type QueryDetail =
  paths["/api/v1/queries/{job_id}"]["get"]["responses"][200]["content"]["application/json"];

export type SubmitQueryRequest =
  paths["/api/v1/queries"]["post"]["requestBody"]["content"]["application/json"];

export type SubmitQueryResponse =
  paths["/api/v1/queries"]["post"]["responses"][201]["content"]["application/json"];

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function listQueries(): Promise<QuerySummary[]> {
  return apiFetch<QuerySummary[]>("/api/v1/queries");
}

export async function getQueryDetail(jobId: string): Promise<QueryDetail> {
  return apiFetch<QueryDetail>(`/api/v1/queries/${jobId}`);
}

export async function submitQuery(
  body: SubmitQueryRequest,
): Promise<SubmitQueryResponse> {
  return apiFetch<SubmitQueryResponse>("/api/v1/queries", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function deleteQuery(jobId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/queries/${jobId}`, {
    method: "DELETE",
  });
}
