// frontend/src/features/talent/api/candidateApi.ts
import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse, ResumeItem, SearchFiltersDto } from "@/types/api";

export const candidateApi = {
  search: (payload: { query: string; filters?: SearchFiltersDto; top_k?: number }) =>
    apiClient.post<PaginatedResponse<ResumeItem>>("/search", payload).then((r) => r.data),
};
