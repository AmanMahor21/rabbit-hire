import { apiClient } from "@/lib/api-client";
import type { HireJob } from "@/types/api";

export const agenticApi = {
  // ✅ Fixed: Changed "/hire/jobs" to "/agentic-hire"
  createJob: (payload: { job_description: string; top_k: number; auto_generate_outreach: boolean }) =>
    apiClient.post<{ job_id: string }>("/agentic-hire", payload).then((r) => r.data),

  // ✅ Fixed: Changed "/hire/jobs/${id}" to "/agentic-hire/${id}"
  getJob: (id: string) => apiClient.get<HireJob>(`/agentic-hire/${id}`).then((r) => r.data),
};
