
import { cn } from "@/lib/cn";
import React from "react";
interface Props extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string; error?: string; leftIcon?: React.ReactNode; rightIcon?: React.ReactNode;
}
export function Input({ label, error, leftIcon, rightIcon, className, id, ...props }: Props) {
  const autoId = React.useId();
  const inputId = id || autoId;
  return <div className="w-full">
    {label && <label htmlFor={inputId} className="mb-1.5 block text-[12px] font-medium text-slate-300">{label}</label>}
    <div className="relative">
      {leftIcon && <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">{leftIcon}</div>}
      <input id={inputId} className={cn("h-10 w-full rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 text-[14px] text-slate-100 outline-none placeholder:text-slate-500 focus:border-[var(--color-border-focus)] focus:ring-2 focus:ring-white/10 transition", leftIcon && "pl-9", rightIcon && "pr-9", error && "border-red-500/40 focus:border-red-500/40 focus:ring-red-500/10", className)} {...props} />
      {rightIcon && <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">{rightIcon}</div>}
    </div>
    {error && <p className="mt-1.5 text-[12px] text-red-300">{error}</p>}
  </div>;
}
