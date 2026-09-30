import { useLocation } from "react-router";
import { Kbd } from "@/components/ui/kbd";
import { PATHS } from "@/app/routes/paths";
import { FiSearch, FiCommand } from "react-icons/fi";
const titles: Record<string, { title: string; desc: string }> = {
  [PATHS.dashboard]: { title: "Dashboard", desc: "Talent pool health and activity" },
  [PATHS.talent]: { title: "Talent Search", desc: "Semantic search across all indexed resumes" },
  [PATHS.hire]: { title: "Agentic Hire", desc: "Rank candidates against JD with AI agents" },
  [PATHS.upload]: { title: "Resume Ingest", desc: "Upload, parse and index resumes" },
  [PATHS.chat]: { title: "Talent Chat", desc: "Ask anything about your talent pool" },
};
export function Header({ onMenu }: { onMenu?: () => void }) {
  const { pathname } = useLocation();
  const meta = titles[pathname] || { title: "Rabbit Hire", desc: "Agentic Talent OS" };
  return (
    <header className="sticky top-0 z-[var(--z-header)] flex h-[64px] items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg)]/80 px-6 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenu}
          className="lg:hidden h-9 w-9 rounded-xl border border-[var(--color-border)] flex items-center justify-center"
        >
          ☰
        </button>
        <div>
          <h1 className="text-[15px] font-semibold leading-none text-white">{meta.title}</h1>
          <p className="mt-1 text-[12px] text-slate-500">{meta.desc}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 h-9 text-[13px] text-slate-500">
          <FiSearch className="h-4 w-4" />
          <span>Search talent…</span>
          <div className="ml-2 flex items-center gap-1">
            <Kbd>
              <FiCommand className="h-3 w-3" />
            </Kbd>
            <Kbd>K</Kbd>
          </div>
        </div>
        <div className="h-9 w-9 rounded-full bg-white text-black flex items-center justify-center font-bold text-[12px]">
          A
        </div>
      </div>
    </header>
  );
}
