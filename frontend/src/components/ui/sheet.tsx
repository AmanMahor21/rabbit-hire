
import { cn } from "@/lib/cn";
export function Sheet({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) {
  if (!open) return null;
  return <div className="fixed inset-0 z-[var(--z-overlay)] flex">
    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
    <div className="relative ml-auto h-dvh w-[380px] max-w-[85vw] bg-[var(--color-bg-soft)] border-l border-[var(--color-border)] p-6 overflow-y-auto scroll-thin">{children}</div>
  </div>;
}
