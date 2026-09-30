
import { cn } from "@/lib/cn";
import React from "react";
export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => (
  <textarea ref={ref} className={cn("min-h-[100px] w-full rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] px-3 py-2.5 text-[14px] text-slate-100 placeholder:text-slate-500 focus:border-[var(--color-border-focus)] focus:ring-2 focus:ring-white/10 outline-none transition", className)} {...props} />
));
Textarea.displayName = "Textarea";
