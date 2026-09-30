
import { useCallback } from "react";
export function Dropzone({ onFiles, disabled }: { onFiles: (f: File[]) => void; disabled?: boolean; }) {
  const onDrop = useCallback((e: React.DragEvent) => { e.preventDefault(); if (disabled) return; const files = Array.from(e.dataTransfer.files); onFiles(files); }, [onFiles, disabled]);
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => { if (e.target.files) onFiles(Array.from(e.target.files)); };
  return <div onDragOver={e => e.preventDefault()} onDrop={onDrop} className="rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/50 p-8 text-center hover:border-[var(--color-border-strong)] transition-colors">
    <p className="text-[14px] text-white font-medium">Drag & drop resumes</p><p className="text-[12px] text-slate-500 mt-1">PDF, DOCX up to 50 files</p>
    <label className="mt-4 inline-flex rounded-xl bg-white text-black px-4 py-2 text-[13px] font-medium cursor-pointer">Browse files<input type="file" multiple hidden onChange={onChange} accept=".pdf,.docx,.doc" disabled={disabled} /></label>
  </div>;
}
