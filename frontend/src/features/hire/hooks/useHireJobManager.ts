
import { useQuery } from "@tanstack/react-query";
import { agenticApi } from "../api/agenticApi";
import { useHireStore } from "@/stores/useHireStore";
import { APP_CONFIG } from "@/config/constants";
export function useHireJobManager() {
  const { activeJobId } = useHireStore();
  return useQuery({
    queryKey: ["hire-job", activeJobId],
    queryFn: () => {
      if (!activeJobId) throw new Error("No active job");
      return agenticApi.getJob(activeJobId);
    },
    enabled: !!activeJobId,
    refetchInterval: (q) => {
      const data = q.state.data;
      if (!data) return APP_CONFIG.POLL_INTERVAL_MS;
      if (data.status === "completed" || data.status === "failed") return false;
      return APP_CONFIG.POLL_INTERVAL_MS;
    },
  });
}
