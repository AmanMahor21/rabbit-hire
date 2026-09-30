
export const formatExp = (y?: number | null) => {
  if (y == null) return "—";
  return y === 1 ? "1 yr" : `${y} yrs`;
};
export const truncate = (s: string, n = 200) => (s.length > n ? `${s.slice(0, n)}…` : s);
export const scoreColor = (score?: number) => {
  if (score == null) return "text-slate-400";
  if (score >= 85) return "text-emerald-300";
  if (score >= 70) return "text-cyan-300";
  if (score >= 50) return "text-amber-300";
  return "text-slate-400";
};
export const displayName = (c: { name?: string; full_name?: string; filename?: string }) =>
  c.name || c.full_name || c.filename?.replace(/\.[^.]+$/, "").replace(/_/g, " ") || "Unknown";
