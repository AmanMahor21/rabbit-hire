// frontend/src/features/hire/components/OutreachPanel.tsx
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ResumeItem } from "@/types/api";

interface OutreachItem {
  candidate: string;
  email?: string;
  message: string;
  candidate_details?: ResumeItem;
}

export function OutreachPanel({
  outreach,
  onViewCandidate,
}: {
  outreach: OutreachItem[];
  onViewCandidate?: (c: ResumeItem) => void;
}) {
  if (!outreach.length) {
    return <Card className="p-6 text-center text-sm text-slate-500">No outreach generated</Card>;
  }

  return (
    <div className="space-y-3">
      {outreach.map((o, i) => (
        <Card key={i} className="p-4">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <p className="text-[13px] font-medium text-white">{o.candidate}</p>
              {o.email && <p className="text-[11px] text-slate-500">{o.email}</p>}
            </div>
            {/* ✅ View Profile button only shows if we have candidate details */}
            {o.candidate_details && onViewCandidate && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewCandidate(o.candidate_details!)}
                className="shrink-0"
              >
                View Profile
              </Button>
            )}
          </div>
          <hr className="mt-2 w-full border-slate-700" />
          <p className="text-[13px] leading-6 text-slate-200 whitespace-pre-wrap">{o.message}</p>
        </Card>
      ))}
    </div>
  );
}
