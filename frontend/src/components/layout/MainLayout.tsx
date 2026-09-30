import { Outlet, Link } from "react-router";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useHireJobManager } from "@/features/hire/hooks/useHireJobManager";
import { useState } from "react";

export function MainLayout() {
  const { data: job } = useHireJobManager();
  const isRunning = job?.status === "queued" || job?.status === "running";
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-dvh w-full bg-[var(--color-bg)]">
      <Sidebar open={mobileOpen} setOpen={setMobileOpen} />
      <main className="flex min-h-dvh flex-1 flex-col lg:ml-[268px] transition-all duration-300">
        <Header onMenu={() => setMobileOpen(true)} />
        <div className="flex-1 p-4 md:p-6 lg:p-8">
          <div className="mx-auto">
            <Outlet />
          </div>
        </div>
        {isRunning && (
          <div className="fixed bottom-4 right-4 z-[var(--z-toast)] flex items-center gap-3 rounded-2xl border border-cyan-500/20 bg-[var(--color-surface)] px-4 py-3 shadow-2xl">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
            <div>
              <p className="text-sm font-medium text-white">
                Ranking {job?.stage} — {job?.progress}%
              </p>
              <p className="text-xs text-slate-500">Job {job?.job_id} running</p>
            </div>
            <Link to="/hire" className="ml-2 rounded-lg bg-white px-3 py-1 text-xs font-bold text-black">
              View
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}
