import { apiClient } from "@/lib/api-client";
import { env } from "@/config/env";
import type { HireJob } from "@/types/api";

export type HireStreamEvent =
  | { type: "status"; job: HireJob }
  | { type: "error"; message: string }
  | { type: "timeout"; jobId: string };

export type HireStreamHandle = {
  close: () => void;
};

export const agenticApi = {
  // ✅ Fixed: Changed "/hire/jobs" to "/agentic-hire"
  createJob: (payload: { job_description: string; top_k: number; auto_generate_outreach: boolean }) =>
    apiClient.post<{ job_id: string }>("/agentic-hire", payload).then((r) => r.data),

  // ✅ Fixed: Changed "/hire/jobs/${id}" to "/agentic-hire/${id}"
  getJob: (id: string) => apiClient.get<HireJob>(`/agentic-hire/${id}`).then((r) => r.data),

  /**
   * Open an SSE stream for a job. Emits terminal state, then closes.
   * The browser's EventSource auto-reconnects on transient errors.
   */
  // frontend/src/features/hire/api/agenticApi.ts (streamJob method)

  streamJob(jobId: string, onEvent: (event: HireStreamEvent) => void, onOpen?: () => void): HireStreamHandle {
    const base = env.API_URL.endsWith("/") ? env.API_URL.slice(0, -1) : env.API_URL;
    const url = `${base}/agentic-hire/${encodeURIComponent(jobId)}/stream`;

    const es = new EventSource(url);

    es.addEventListener("open", () => onOpen?.());

    es.addEventListener("status", (evt) => {
      try {
        const job = JSON.parse((evt as MessageEvent).data) as HireJob;
        onEvent({ type: "status", job });
        if (job.status === "completed" || job.status === "failed") {
          es.close();
        }
      } catch (err) {
        console.error("[SSE] Failed to parse status frame:", err);
      }
    });

    es.addEventListener("error", (evt) => {
      const me = evt as MessageEvent;
      if (me.data) {
        try {
          const parsed = JSON.parse(me.data);
          onEvent({ type: "error", message: parsed.error ?? "stream error" });
        } catch {
          onEvent({ type: "error", message: "stream error" });
        }
      }
    });

    es.addEventListener("timeout", (evt) => {
      const me = evt as MessageEvent;
      let jobIdOut = jobId;
      try {
        jobIdOut = JSON.parse(me.data).job_id ?? jobId;
      } catch {}
      onEvent({ type: "timeout", jobId: jobIdOut });
      es.close();
    });

    return {
      close: () => es.close(),
    };
  },
};
