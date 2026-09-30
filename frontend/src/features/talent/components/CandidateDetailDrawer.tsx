import { Sheet } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { displayName, formatExp } from "@/utils/format";
import type { ResumeItem } from "@/types/api";
import { FiMail, FiPhone, FiMapPin, FiCopy, FiCheck } from "react-icons/fi";
import { useState } from "react";

export function CandidateDetailDrawer({
  candidate,
  open,
  onClose,
  reason,
}: {
  candidate: ResumeItem | null;
  open: boolean;
  onClose: () => void;
  reason?: string;
}) {
  const [copied, setCopied] = useState(false);

  if (!candidate) return null;

  const name = displayName(candidate);
  const email = candidate.email || "";
  const phone = candidate.phone || "";

  // Clean up filename for display if name is missing
  const cleanName = name
    .replace(/_/g, " ")
    .replace(/\.pdf$/i, "")
    .trim();

  const handleCopyEmail = () => {
    if (email) {
      navigator.clipboard.writeText(email);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Sheet open={open} onClose={onClose}>
      <div className="space-y-6 pb-8">
        {/* 1. Header & Contact */}
        <div className="space-y-3">
          <h2 className="text-xl font-bold text-white leading-tight">{cleanName}</h2>

          <div className="flex flex-wrap gap-3 text-sm text-slate-400">
            {email && (
              <div className="flex items-center gap-1.5 group">
                <FiMail className="h-4 w-4 text-slate-500" />
                <a href={`mailto:${email}`} className="hover:text-cyan-400 transition-colors truncate max-w-[200px]">
                  {email}
                </a>
                <button
                  onClick={handleCopyEmail}
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-white"
                  title="Copy email"
                >
                  {copied ? <FiCheck className="h-3 w-3 text-emerald-400" /> : <FiCopy className="h-3 w-3" />}
                </button>
              </div>
            )}

            {phone && (
              <div className="flex items-center gap-1.5">
                <FiPhone className="h-4 w-4 text-slate-500" />
                <a href={`tel:${phone}`} className="hover:text-cyan-400 transition-colors">
                  {phone}
                </a>
              </div>
            )}

            {candidate.location?.[0] && (
              <div className="flex items-center gap-1.5">
                <FiMapPin className="h-4 w-4 text-slate-500" />
                <span>{candidate.location[0]}</span>
              </div>
            )}

            {candidate.experience_years != null && (
              <span className="text-slate-500">• {formatExp(candidate.experience_years)} exp</span>
            )}
          </div>
        </div>

        {/* 2. AI Reasoning (Prominent) */}
        {reason && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm leading-relaxed text-amber-200 shadow-sm">
            {reason}
          </div>
        )}

        {/* 3. Skills Tags */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Key Skills</h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((skill) => (
                <Badge
                  key={skill}
                  variant="outline"
                  className="bg-[var(--color-surface)] text-slate-300 border-[var(--color-border)]"
                >
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* 4. Structured Resume Content */}
        <div className="space-y-6 text-sm leading-relaxed text-slate-300">
          {/* Summary Section */}
          {candidate.summary && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Professional Summary
              </h3>
              <p className="whitespace-pre-wrap">{candidate.summary}</p>
            </section>
          )}

          {/* Full Resume Text (Formatted) */}
          {candidate.text && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Full Resume Details
              </h3>
              <div className="max-h-[400px] overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 scroll-thin">
                <pre className="whitespace-pre-wrap font-mono text-xs text-slate-400 leading-relaxed">
                  {candidate.text}
                </pre>
              </div>
            </section>
          )}
        </div>
      </div>
    </Sheet>
  );
}
