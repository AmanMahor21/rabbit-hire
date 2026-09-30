
import { cn } from "@/lib/cn";
export function Badge({ className, ...p }: React.HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn("inline-flex items-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-0.5 text-[11px] text-slate-300", className)} {...p} />;
}
export function ScoreBadge({ score, className }: { score?: number; className?: string }) {
  const color = score == null ? "bg-slate-700 text-slate-300" : score >= 85 ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" : score >= 70 ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/30" : "bg-amber-500/20 text-amber-300 border-amber-500/30";
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-[12px] font-semibold", color, className)}>{score != null ? `${Math.round(score)}%` : "—"}</span>;
}
