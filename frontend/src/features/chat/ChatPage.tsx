// frontend/src/features/chat/ChatPage.tsx

import { useState, useRef, useEffect, useCallback } from "react";
import { chatApi, type ChatResponse } from "./api/chatApi";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FiSend, FiCpu, FiUser } from "react-icons/fi";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CandidateDetailDrawer } from "@/features/talent/components/CandidateDetailDrawer";
import type { ResumeItem } from "@/types/api";
import { cn } from "@/lib/cn";

type ChatMsg = {
  role: "user" | "assistant";
  content: string;
  candidates?: ResumeItem[];
  ts: string;
  id: string;
};

const SUGGESTED = [
  "Find Python developers in Bangalore",
  "Who has experience with React and AWS?",
  "Show me senior backend engineers",
  "Summarize the top 3 candidates",
];

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<ResumeItem | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = useCallback(
    async (text?: string) => {
      const msg = (text || input).trim();
      if (!msg) return;

      setInput("");
      const id = crypto.randomUUID();

      setMessages((m) => [...m, { role: "user", content: msg, ts: new Date().toISOString(), id }]);

      setLoading(true);
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      try {
        const data: ChatResponse = await chatApi.chat(
          msg,
          messages.slice(-10).map(({ role, content }) => ({ role, content }))
        );

        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: data.answer,
            candidates: data.candidates || [],
            ts: new Date().toISOString(),
            id: crypto.randomUUID(),
          },
        ]);
      } catch {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: "I encountered an error. Please try again.",
            ts: new Date().toISOString(),
            id: crypto.randomUUID(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [input, messages]
  );

  const showEmptyState = messages.length === 0 && !loading;

  return (
    <div className="flex h-[calc(100dvh-140px)] flex-col gap-4">
      <Card className="relative flex min-h-0 flex-1 flex-col overflow-hidden p-0">
        {/* ─── Messages / Empty State (fills middle) ─── */}
        <div className="relative min-h-0 flex-1 overflow-y-auto scroll-thin">
          {showEmptyState ? (
            // ✅ Empty state now lives INSIDE the scroll area, not over the whole card
            <div className="flex h-full flex-col items-center justify-center p-6 text-center">
              <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-500/20 to-violet-500/20">
                <FiCpu className="h-8 w-8 text-cyan-400" />
              </div>
              <h2 className="mb-2 text-2xl font-semibold text-white">Talent Intelligence Chat</h2>
              <p className="mb-8 max-w-md text-slate-400">Ask questions about your talent pool.</p>
              <div className="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                {SUGGESTED.map((p) => (
                  <button
                    key={p}
                    onClick={() => send(p)}
                    className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-4 py-3 text-left text-sm text-slate-300 transition-colors hover:border-cyan-500/30 hover:bg-[var(--color-surface-raised)] hover:text-white"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // ✅ Normal message list
            <div className="space-y-6 p-4 md:p-6">
              {messages.map((m) => (
                <div key={m.id} className={cn("flex gap-4", m.role === "user" ? "justify-end" : "justify-start")}>
                  {m.role === "assistant" && (
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-600 text-white">
                      <FiCpu className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={cn("flex max-w-[85%] flex-col gap-2", m.role === "user" ? "items-end" : "items-start")}
                  >
                    <div
                      className={cn(
                        "rounded-2xl px-5 py-3.5 text-[14px] leading-relaxed shadow-sm",
                        m.role === "user"
                          ? "rounded-tr-none bg-white text-black"
                          : "rounded-tl-none border border-[var(--color-border)] bg-[var(--color-surface)] text-slate-200"
                      )}
                    >
                      <div className="prose prose-invert prose-sm max-w-none [&_p]:last:mb-0">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                      </div>
                    </div>

                    {m.candidates && m.candidates.length > 0 && (
                      <div className="mt-1 grid w-full grid-cols-1 gap-2">
                        {m.candidates.slice(0, 3).map((c) => (
                          <button
                            key={c.id}
                            onClick={() => setSelectedCandidate(c)}
                            className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-left text-[12px] text-slate-300 transition-all hover:border-cyan-500/50 hover:bg-[var(--color-surface-hover)] hover:text-white active:scale-[0.99]"
                          >
                            <div className="truncate font-medium text-white group-hover:text-cyan-400">
                              {c.full_name || c.name || c.filename?.replace(/_/g, " ").replace(".pdf", "")}
                            </div>
                            <div className="mt-1 line-clamp-1 text-[11px] text-slate-500">
                              {c.skills?.slice(0, 3).join(", ")}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {m.role === "user" && (
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-black">
                      <FiUser className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-4">
                  <div className="flex h-8 w-8 animate-pulse items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-600">
                    <FiCpu className="h-4 w-4 text-white/50" />
                  </div>
                  <div className="flex items-center gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 text-[13px] text-slate-500">
                    <span
                      className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* ─── Input (always pinned to bottom) ─── */}
        <div className="flex shrink-0 gap-2 border-t border-[var(--color-border)] bg-[var(--color-bg)] p-4">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Ask about talent..."
            className="scroll-thin max-h-32 min-h-[48px] flex-1 resize-none rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-[14px] text-white placeholder:text-slate-500 outline-none focus:border-[var(--color-border-focus)] focus:ring-2 focus:ring-white/10"
            rows={1}
          />
          <Button onClick={() => send()} disabled={loading || !input.trim()} className="h-12 w-12 shrink-0 px-0">
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            ) : (
              <FiSend className="h-4 w-4" />
            )}
          </Button>
        </div>
      </Card>

      <CandidateDetailDrawer
        candidate={selectedCandidate}
        open={!!selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
      />
    </div>
  );
}
