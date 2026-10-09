// frontend/src/features/hire/hooks/useHireJobManager.ts
import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { agenticApi } from "../api/agenticApi";
import { useHireStore } from "@/stores/useHireStore";
import type { HireJob } from "@/types/api";

const hireJobKey = (id: string | null | undefined) => ["hire-job", id] as const;

export function useHireJobManager() {
  const { activeJobId } = useHireStore();
  const qc = useQueryClient();
  const handleRef = useRef<{ close: () => void } | null>(null);

  // Initial fetch on mount or when activeJobId changes
  const query = useQuery<HireJob>({
    queryKey: hireJobKey(activeJobId),
    queryFn: () => {
      if (!activeJobId) throw new Error("No active job");
      return agenticApi.getJob(activeJobId);
    },
    enabled: !!activeJobId,
    refetchInterval: false, // ❌ ZERO UI POLLING
    refetchOnWindowFocus: false, // ❌ ZERO UI POLLING
    staleTime: Infinity, // Trust SSE stream
  });

  useEffect(() => {
    if (!activeJobId) return;

    const cached = qc.getQueryData<HireJob>(hireJobKey(activeJobId));
    if (cached?.status === "completed" || cached?.status === "failed") return;

    handleRef.current?.close();
    handleRef.current = agenticApi.streamJob(activeJobId, (event) => {
      if (event.type === "status") {
        // Direct push from SSE stream into React Query cache
        qc.setQueryData<HireJob>(hireJobKey(activeJobId), event.job);
      } else if (event.type === "error" || event.type === "timeout") {
        // Fallback sync only if connection drops
        agenticApi
          .getJob(activeJobId)
          .then((latestJob) => {
            qc.setQueryData<HireJob>(hireJobKey(activeJobId), latestJob);
          })
          .catch(() => {});
      }
    });

    return () => {
      handleRef.current?.close();
      handleRef.current = null;
    };
  }, [activeJobId, qc]);

  return query;
}
