
import type { ResumeItem } from "@/types/api";
import { CandidateCard } from "@/features/talent/components/CandidateCard";
import { Card } from "@/components/ui/card";
import { FiAward, FiClock } from "react-icons/fi";
export function RankedList({ candidates, onSelect, selectedId }: { candidates: ResumeItem[]; onSelect: (c: ResumeItem) => void; selectedId?: string; }) {
  if (!candidates.length) return null;
  return <div className="space-y-4">
    <Card className="p-4 flex items-center justify-between"><div className="flex items-center gap-2"><div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500 text-black"><FiAward className="h-4 w-4" /></div><div><p className="text-[13px] font-semibold text-white">Ranked shortlist</p><p className="text-[11px] text-slate-500">{candidates.length} candidates</p></div></div><div className="flex items-center gap-1 text-[11px] text-slate-500"><FiClock className="h-3 w-3" />Just now</div></Card>
    <div className="grid grid-cols-1 gap-3">{candidates.map((c, i) => <div key={c.id || c.filename} className={i===0 ? "rounded-2xl border border-amber-500/20 p-0.5 bg-gradient-to-b from-amber-500/20 to-transparent" : ""}><CandidateCard candidate={c} rankScore={c.rank_score} reason={c.ranking_reason} selected={selectedId === c.id} onClick={() => onSelect(c)} /></div>)}</div>
  </div>;
}
