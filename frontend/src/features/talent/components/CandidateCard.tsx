
import type { ResumeItem } from "@/types/api";
import { Badge, ScoreBadge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { FiMail, FiMapPin, FiBriefcase } from "react-icons/fi";
import { formatExp, displayName } from "@/utils/format";

export function CandidateCard({ candidate, rankScore, reason, selected, onClick }: { candidate: ResumeItem; rankScore?: number; reason?: string; selected?: boolean; onClick?: () => void; }) {
  const name = displayName(candidate);
  const skills = candidate.skills || [];
  return <article role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && onClick?.()} onClick={onClick} className={cn("group relative cursor-pointer rounded-2xl border p-4 text-left transition-colors focus-ring", selected ? "border-white bg-white text-black" : "surface surface-hover")}>
    <div className="flex items-start justify-between gap-3">
      <div className="flex gap-3 min-w-0">
        <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold", selected ? "bg-black text-white" : "bg-white text-black")}>{String(name).charAt(0).toUpperCase()}</div>
        <div className="min-w-0">
          <h3 className={cn("truncate text-[14px] font-semibold", selected ? "text-black" : "text-white")}>{name}</h3>
          <div className={cn("mt-1 flex flex-wrap items-center gap-2 text-[11px]", selected ? "text-black/60" : "text-slate-400")}>
            {(candidate.experience_years ?? candidate.experience) != null && <span className="inline-flex items-center gap-1"><FiBriefcase className="h-3 w-3" />{formatExp(candidate.experience_years ?? candidate.experience)}</span>}
            {candidate.location?.[0] && <span className="inline-flex items-center gap-1"><FiMapPin className="h-3 w-3" />{candidate.location[0].slice(0,28)}</span>}
            {candidate.email && <span className="inline-flex items-center gap-1 truncate"><FiMail className="h-3 w-3" />{candidate.email}</span>}
          </div>
        </div>
      </div>
      {typeof rankScore === "number" && <ScoreBadge score={rankScore} className={selected ? "!bg-black !text-white !border-black" : ""} />}
    </div>
    {skills.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5">{skills.slice(0,6).map((s) => <Badge key={s} className={cn("text-[11px]", selected ? "bg-black/10 text-black border-black/10" : "")}>{s}</Badge>)}{skills.length > 6 && <Badge>+{skills.length-6}</Badge>}</div>}
    {reason && <p className={cn("mt-3 line-clamp-2 text-[12px] leading-5", selected ? "text-black/70" : "text-slate-400")}>{reason}</p>}
  </article>;
}
