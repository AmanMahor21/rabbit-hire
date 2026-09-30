
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
export function JDInputPanel({ jd, setJd, topK, setTopK, autoOutreach, setAutoOutreach, onRun, loading }: { jd: string; setJd: (v: string) => void; topK: number; setTopK: (v: number) => void; autoOutreach: boolean; setAutoOutreach: (v: boolean) => void; onRun: () => void; loading: boolean; }) {
  return <Card className="p-5 space-y-4 h-fit lg:sticky lg:top-[88px]">
    <h3 className="text-[14px] font-semibold text-white">Job Description</h3>
    <Textarea value={jd} onChange={e => setJd(e.target.value)} placeholder="Paste JD here..." className="min-h-[260px]" />
    <div className="flex items-center justify-between"><span className="text-[12px] text-slate-500">Top K</span><select value={topK} onChange={e => setTopK(Number(e.target.value))} className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-[13px] text-white">{[8,12,16,20].map(k => <option key={k} value={k}>{k}</option>)}</select></div>
    <label className="flex items-center gap-2 text-[12px] text-slate-400"><input type="checkbox" checked={autoOutreach} onChange={e => setAutoOutreach(e.target.checked)} /> Auto outreach</label>
    <Button onClick={onRun} loading={loading} className="w-full">Run Agentic Rank</Button>
  </Card>;
}
