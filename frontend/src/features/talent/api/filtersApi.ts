// frontend/src/features/talent/api/filtersApi.ts
import { apiClient } from "@/lib/api-client";
import type { FilterOptions } from "@/types/api";

export type { FilterOptions };

export const filtersApi = {
  get: () => apiClient.get<FilterOptions>("/filters").then((r) => r.data),
};
