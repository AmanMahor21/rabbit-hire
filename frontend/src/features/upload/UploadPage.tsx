// frontend/src/features/upload/UploadPage.tsx
import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Dropzone } from "./components/Dropzone";
import { uploadApi } from "./api/uploadApi";
import { showToast } from "@/utils/toast";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FiFileText, FiTrash2, FiZap, FiCheckCircle, FiLoader } from "react-icons/fi";
import { Link } from "react-router";
import { PATHS } from "@/app/routes/paths";
import { apiClient } from "@/lib/api-client";
import { FILTER_OPTIONS_QUERY_KEY } from "@/features/talent/hooks/useFilterOptions";

type ProcessStatusResponse = {
  status: "processing" | "completed" | "failed";
  state?: string;
  result?: { message?: string; count?: number };
  error?: string;
};

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"idle" | "uploaded" | "indexing" | "indexed">("idle");

  const [taskId, setTaskId] = useState<string | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const qc = useQueryClient();
  const [, setLastUpload] = useLocalStorage("lastUploadCount", 0);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (!taskId || step !== "indexing") return;

    pollIntervalRef.current = setInterval(async () => {
      try {
        const { data } = await apiClient.get<ProcessStatusResponse>(`/process/status/${taskId}`);

        if (data.status === "completed") {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStep("indexed");
          setTaskId(null);

          // ✅ Invalidate filter options so TalentPage refetches them
          qc.invalidateQueries({ queryKey: FILTER_OPTIONS_QUERY_KEY });
          // ✅ Also invalidate stats so dashboard updates
          qc.invalidateQueries({ queryKey: ["stats"] });

          showToast({
            message: data.result?.message || "Indexing complete!",
            type: "success",
          });
        } else if (data.status === "failed") {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStep("uploaded");
          setTaskId(null);
          showToast({
            message: data.error || "Processing failed",
            type: "error",
          });
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [taskId, step, qc]);

  const handleUpload = async () => {
    if (!files.length) return showToast({ message: "Select files first", type: "warning" });

    setLoading(true);
    try {
      const res = await uploadApi.upload(files);
      setStep("uploaded");
      setLastUpload(files.length);
      showToast({
        message: res.message || `Uploaded ${files.length} files`,
        type: "success",
      });
    } catch (e: any) {
      showToast({ message: e.message, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    setLoading(true);
    try {
      const res = await apiClient.post<{ task_id: string; message: string }>("/process");
      setTaskId(res.data.task_id);
      setStep("indexing");
      showToast({
        message: "Processing started in background…",
        type: "info",
      });
    } catch (e: any) {
      showToast({ message: e.message, type: "error" });
      setStep("uploaded");
    } finally {
      setLoading(false);
    }
  };

  const isIndexing = step === "indexing";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-white">Resume ingest</h1>
        <p className="mt-1 text-[13px] text-slate-400">Upload resumes → LLM parsing → Qdrant embedding.</p>
      </div>

      <div className="flex items-center gap-2">
        {[
          { id: "idle", label: "Select", done: files.length > 0 },
          {
            id: "uploaded",
            label: "Uploaded",
            done: step === "uploaded" || step === "indexing" || step === "indexed",
          },
          { id: "indexed", label: "Indexed", done: step === "indexed" },
        ].map((s, idx) => (
          <div key={s.id} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-[12px] font-medium ${
                s.done ? "bg-white text-black" : "bg-[var(--color-surface-raised)] text-slate-500"
              }`}
            >
              {s.done ? <FiCheckCircle className="h-4 w-4" /> : idx + 1}
            </div>
            <span className={`text-[12px] ${s.done ? "text-white" : "text-slate-500"}`}>{s.label}</span>
            {idx < 2 && <div className={`h-px w-8 ${s.done ? "bg-white/20" : "bg-[var(--color-border)]"}`} />}
          </div>
        ))}
      </div>

      <Card className="p-6">
        <Dropzone
          onFiles={(f) => {
            setFiles((prev) => [...prev, ...f]);
            setStep("idle");
          }}
          disabled={loading || isIndexing}
        />

        {files.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-[13px] font-medium text-white">{files.length} files selected</h3>
              <button
                onClick={() => setFiles([])}
                className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-white"
                disabled={isIndexing}
              >
                <FiTrash2 /> Clear
              </button>
            </div>

            <div className="mt-3 max-h-56 space-y-2 overflow-y-auto pr-1 scroll-thin">
              {files.map((f) => (
                <div
                  key={`${f.name}-${f.size}-${f.lastModified}`}
                  className="flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5"
                >
                  <FiFileText className="h-4 w-4 text-slate-500" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[12px] text-white">{f.name}</p>
                    <p className="text-[11px] text-slate-500">{(f.size / 1024).toFixed(0)} KB</p>
                  </div>
                  <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-slate-300">
                    {f.name.split(".").pop()?.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-6 flex gap-2">
              <Button
                variant="secondary"
                onClick={handleUpload}
                disabled={loading || isIndexing}
                className="h-11 flex-1"
              >
                {loading && !isIndexing ? "Uploading…" : "1. Upload files"}
              </Button>
              <Button
                onClick={handleProcess}
                disabled={loading || isIndexing || step === "idle"}
                className="h-11 flex-1"
              >
                {isIndexing ? (
                  <>
                    <FiLoader className="mr-2 h-4 w-4 animate-spin" />
                    Indexing…
                  </>
                ) : (
                  <>
                    <FiZap className="mr-2 h-4 w-4" />
                    2. Process & index
                  </>
                )}
              </Button>
            </div>

            {step === "indexed" && (
              <div className="mt-4 flex items-center justify-between rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-[12px] text-emerald-200">
                <span>✅ Indexed! Your talent pool is updated.</span>
                <Link to={PATHS.talent} className="rounded-lg bg-white px-3 py-1 text-[11px] font-medium text-black">
                  Search now
                </Link>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
