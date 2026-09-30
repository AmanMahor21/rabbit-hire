
import { Card } from "@/components/ui/card";
export function StatCard({ title, value, change }: { title: string; value: number | string; change?: string; icon?: string; }) {
  return <Card className="p-5"><p className="text-[12px] text-slate-500">{title}</p><div className="mt-2 flex items-baseline justify-between"><p className="text-2xl font-semibold text-white">{value}</p>{change && <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] text-emerald-300">{change}</span>}</div></Card>;
}
