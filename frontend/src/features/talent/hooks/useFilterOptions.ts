// frontend/src/features/talent/hooks/useFilterOptions.ts
import { useQuery } from "@tanstack/react-query";
import { filtersApi, type FilterOptions } from "../api/filtersApi";

export const FILTER_OPTIONS_QUERY_KEY = ["filter-options"] as const;

export function useFilterOptions() {
  return useQuery<FilterOptions>({
    queryKey: FILTER_OPTIONS_QUERY_KEY,
    queryFn: filtersApi.get,
    staleTime: 1000 * 60 * 5, // matches backend Redis TTL
    gcTime: 1000 * 60 * 30,
    refetchOnMount: true,
  });
}
