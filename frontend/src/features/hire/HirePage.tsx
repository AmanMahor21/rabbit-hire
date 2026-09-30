// frontend/src/features/hire/HirePage.tsx
import { useState, useMemo } from "react";
import { agenticApi } from "./api/agenticApi";
import { JDInputPanel } from "./components/JDInputPanel";
import { RankedList } from "./components/RankedList";
import { OutreachPanel } from "./components/OutreachPanel";
import { CandidateDetailDrawer } from "@/features/talent/components/CandidateDetailDrawer";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useHireStore } from "@/stores/useHireStore";
import { useHireJobManager } from "./hooks/useHireJobManager";
import { showToast } from "@/utils/toast";
import type { ResumeItem } from "@/types/api";

// ✅ Helper: Transform nested LangGraph result into flat ResumeItem
const mapApiToResumeItem = (apiResult: any): ResumeItem => {
  const payload = apiResult.payload || {};
  return {
    id: apiResult.id || payload.filename || crypto.randomUUID(),
    filename: payload.filename || "",
    name: payload.name || "",
    full_name: payload.full_name || payload.name || "",
    skills: payload.skills || [],
    location: payload.location || [],
    domains: payload.domains || [],
    experience_years: payload.experience_years || payload.experience || 0,
    experience: payload.experience || 0,
    email: payload.email || null,
    phone: payload.phone || null,
    text: payload.text || "",
    summary: payload.summary || "",
    // Convert 0-1 score to 0-100 if needed
    rank_score: apiResult.rank_score || (apiResult.score ? Math.round(apiResult.score * 100) : 0),
    ranking_reason: apiResult.ranking_reason || apiResult.reason || "",
  };
};

export default function HirePage() {
  const { jd, setJd, topK, setTopK, autoOutreach, setAutoOutreach, activeJobId, setActiveJobId } = useHireStore();
  const [localStarting, setLocalStarting] = useState(false);
  const [activeTab, setActiveTab] = useState("ranked");
  const [selected, setSelected] = useState<ResumeItem | null>(null);

  const { data: job, isFetching } = useHireJobManager();
  const isRunning = job?.status === "queued" || job?.status === "running";

  // ✅ Transform ranked candidates
  const ranked = useMemo(() => {
    if (!job?.result?.results) return [];
    return job.result.results.map(mapApiToResumeItem);
  }, [job?.result?.results]);

  // ✅ Enrich outreach with candidate details for the drawer
  const enrichedOutreach = useMemo(() => {
    if (!job?.result?.outreach) return [];
    return job.result.outreach.map((o: any) => ({
      ...o,
      // Try to match outreach candidate back to ranked list by name or filename
      candidate_details: ranked.find(
        (r) => r.name === o.candidate || r.filename === o.candidate || r.id === o.candidate_id
      ),
    }));
  }, [job?.result?.outreach, ranked]);

  const run = async () => {
    if (!jd.trim()) return showToast({ message: "Paste a job description first", type: "warning" });
    setLocalStarting(true);
    try {
      const res = await agenticApi.createJob({
        job_description: jd,
        top_k: topK,
        auto_generate_outreach: autoOutreach,
      });
      setActiveJobId(res.job_id);
      showToast({ message: `Job ${res.job_id} started`, type: "success" });
    } catch (e: any) {
      showToast({ message: e.message, type: "error" });
    } finally {
      setLocalStarting(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_1fr]">
      <JDInputPanel
        jd={jd}
        setJd={setJd}
        topK={topK}
        setTopK={setTopK}
        autoOutreach={autoOutreach}
        setAutoOutreach={setAutoOutreach}
        onRun={run}
        loading={localStarting || isRunning}
      />

      <div className="min-w-0 space-y-4">
        {/* Status Bar */}
        {activeJobId && job && (
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isRunning && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-white" />
              )}
              <span className="text-[13px] text-slate-300">
                Job {activeJobId} • {job.status} • {job.stage} • {job.progress}%
              </span>
            </div>
            <span className="text-[11px] text-slate-500">{isFetching ? "syncing..." : "live"}</span>
          </div>
        )}

        {/* Empty State */}
        {ranked.length === 0 ? (
          <div className="flex min-h-[40vh] flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/40 p-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-black font-bold">
              AI
            </div>
            <h3 className="mt-4 text-[15px] font-semibold text-white">
              {isRunning ? `Running ${job?.stage}... ${job?.progress}%` : "Ready to rank"}
            </h3>
            <p className="mt-2 max-w-sm text-[13px] leading-5 text-slate-500">
              {isRunning
                ? "Graph is running in background. You can go to other pages."
                : "Paste a JD on the left. Supervisor graph will parse, search, rank."}
            </p>
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger id="ranked">Ranked ({ranked.length})</TabsTrigger>
              <TabsTrigger id="outreach">Outreach ({enrichedOutreach.length})</TabsTrigger>
            </TabsList>

            <TabsContent id="ranked">
              {/* ✅ Passes correctly shaped data */}
              <RankedList candidates={ranked} onSelect={setSelected} selectedId={selected?.id} />
            </TabsContent>

            <TabsContent id="outreach">
              {/* ✅ Passes enriched data + click handler */}
              <OutreachPanel outreach={enrichedOutreach} onViewCandidate={(c: ResumeItem) => setSelected(c)} />
            </TabsContent>
          </Tabs>
        )}
      </div>

      {/* ✅ Detail drawer receives properly shaped ResumeItem */}
      <CandidateDetailDrawer
        candidate={selected}
        open={!!selected}
        onClose={() => setSelected(null)}
        reason={selected?.ranking_reason}
      />
    </div>
  );
}
