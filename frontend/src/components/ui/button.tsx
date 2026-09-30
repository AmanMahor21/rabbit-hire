
import { cn } from "@/lib/cn";
import React from "react";
type Variant = "primary" | "secondary" | "ghost" | "outline" | "destructive";
type Size = "sm" | "md" | "lg" | "icon";
interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant; size?: Size; loading?: boolean;
}
export function Button({ className, variant = "primary", size = "md", loading, children, disabled, ...props }: Props) {
  const base = "inline-flex items-center justify-center rounded-xl font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)] disabled:opacity-50 disabled:pointer-events-none disabled:cursor-not-allowed active:scale-[0.98]";
  const variants: Record<Variant, string> = {
    primary: "bg-white text-black hover:bg-zinc-100 shadow",
    secondary: "bg-[var(--color-surface-raised)] text-slate-200 hover:bg-[var(--color-surface-hover)] border border-[var(--color-border-strong)]",
    ghost: "text-slate-400 hover:text-slate-100 hover:bg-white/[0.06]",
    outline: "border border-[var(--color-border-strong)] text-slate-300 hover:bg-white/[0.04] hover:text-white",
    destructive: "bg-red-500/10 text-red-300 border border-red-500/20 hover:bg-red-500/15",
  };
  const sizes: Record<Size, string> = { sm: "px-3 h-8 text-[13px]", md: "px-4 h-10 text-[14px]", lg: "px-5 h-11 text-[14px]", icon: "h-10 w-10" };
  return <button className={cn(base, variants[variant], sizes[size], className)} disabled={disabled || loading} {...props}>
    {loading && <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
    {children}
  </button>;
}
