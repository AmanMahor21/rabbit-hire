
export function ScoreRing({ score }: { score?: number }) {
  const s = score ?? 0;
  const r = 36; const c = 2 * Math.PI * r; const offset = c - (s / 100) * c;
  return <div className="relative h-20 w-20"><svg className="h-20 w-20 -rotate-90"><circle cx="40" cy="40" r={r} stroke="var(--color-border)" strokeWidth="6" fill="none" /><circle cx="40" cy="40" r={r} stroke="white" strokeWidth="6" fill="none" strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" /></svg><span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white">{Math.round(s)}%</span></div>;
}
