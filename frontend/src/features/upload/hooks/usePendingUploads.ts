// frontend/src/features/upload/hooks/usePendingUploads.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

type PendingResponse = {
  pending: number;
  total: number;
};

export const PENDING_UPLOADS_QUERY_KEY = ["pending-uploads"] as const;

export function usePendingUploads() {
  return useQuery<PendingResponse>({
    queryKey: PENDING_UPLOADS_QUERY_KEY,
    queryFn: async () => {
      const { data } = await apiClient.get<PendingResponse>("/process/pending");
      return data;
    },
    staleTime: 1000 * 60, // 1 min
    gcTime: 1000 * 60 * 5,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });
}
