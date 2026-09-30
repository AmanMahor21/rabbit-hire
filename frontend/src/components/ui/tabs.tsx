
import { cn } from "@/lib/cn";
import { createContext, useContext } from "react";
const Ctx = createContext<{ value: string; onValueChange: (v: string) => void } | null>(null);
export function Tabs({ value, onValueChange, children, className }: { value: string; onValueChange: (v: string) => void; children: React.ReactNode; className?: string }) {
  return <Ctx.Provider value={{ value, onValueChange }}><div className={cn("space-y-4", className)}>{children}</div></Ctx.Provider>;
}
export function TabsList({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("inline-flex rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1 gap-1", className)} {...p} />;
}
export function TabsTrigger({ id, children }: { id: string; children: React.ReactNode }) {
  const ctx = useContext(Ctx)!;
  const active = ctx.value === id;
  return <button onClick={() => ctx.onValueChange(id)} className={cn("px-4 h-8 rounded-lg text-[13px] font-medium transition-colors", active ? "bg-white text-black shadow" : "text-slate-400 hover:text-white")}>{children}</button>;
}
export function TabsContent({ id, children }: { id: string; children: React.ReactNode }) {
  const ctx = useContext(Ctx)!;
  if (ctx.value !== id) return null;
  return <div>{children}</div>;
}
