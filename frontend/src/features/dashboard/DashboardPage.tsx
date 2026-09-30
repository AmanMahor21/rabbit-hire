
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { StatCard } from "./components/StatCard";
import { dashboardApi } from "./api/dashboardApi";
import { PATHS } from "@/app/routes/paths";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FiSearch, FiUploadCloud, FiCpu, FiMessageSquare, FiActivity } from "react-icons/fi";
import { Skeleton } from "@/components/ui/skeleton";
export default function DashboardPage() {
  const { data, isLoading, isError, error } = useQuery({ queryKey: ["stats"], queryFn: dashboardApi.getStats });
  return <div className="space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><h1 className="text-[22px] font-semibold tracking-tight text-white">Dashboard</h1><p className="mt-1 text-[13px] text-slate-400">Talent pipeline overview</p></div>
      <div className="flex gap-2"><Link to={PATHS.upload}><Button variant="secondary"><FiUploadCloud className="mr-2 h-4 w-4" />Ingest resumes</Button></Link><Link to={PATHS.talent}><Button><FiSearch className="mr-2 h-4 w-4" />Search talent</Button></Link></div>
    </div>
    {isError && <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-[13px] text-red-300">{(error as Error).message}</div>}
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {isLoading ? <><Skeleton className="h-[132px]" /><Skeleton className="h-[132px]" /><Skeleton className="h-[132px]" /></> : <>
        <StatCard title="Total resumes" value={data?.total_resumes ?? 0} change="+12%" />
        <StatCard title="Indexed profiles" value={data?.parsed_resumes ?? data?.total_resumes ?? 0} change="+8%" />
        <StatCard title="Unique skills" value={data?.unique_skills ?? 0} change="+23" />
      </>}
    </div>
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.2fr_0.8fr]">
      <Card className="p-6">
        <div className="flex items-center justify-between"><h3 className="text-[14px] font-semibold text-white">Quick actions</h3><FiActivity className="h-4 w-4 text-slate-500" /></div>
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Link to={PATHS.talent} className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-white/10 transition-colors"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black"><FiSearch className="h-4 w-4" /></div><p className="mt-3 text-[13px] font-medium text-white">Search talent</p><p className="mt-1 text-[11px] text-slate-500">Semantic search with filters</p></Link>
          <Link to={PATHS.hire} className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-white/10 transition-colors"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-500 text-white"><FiCpu className="h-4 w-4" /></div><p className="mt-3 text-[13px] font-medium text-white">Agentic hire</p><p className="mt-1 text-[11px] text-slate-500">JD → ranking → outreach</p></Link>
          <Link to={PATHS.chat} className="group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-white/10 transition-colors"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 text-black"><FiMessageSquare className="h-4 w-4" /></div><p className="mt-3 text-[13px] font-medium text-white">Ask talent pool</p><p className="mt-1 text-[11px] text-slate-500">RAG chat over resumes</p></Link>
        </div>
      </Card>
      <Card className="p-6"><h3 className="text-[14px] font-semibold text-white">System status</h3><div className="mt-5 space-y-4">{[{ name: "Qdrant Vector DB", status: "Operational", dot: "bg-emerald-400" }, { name: "Parser Agent", status: "Idle", dot: "bg-slate-500" }, { name: "Ranker Agent", status: "Ready", dot: "bg-cyan-400" }, { name: "Outreach Agent", status: "Ready", dot: "bg-violet-400" }].map((s) => <div key={s.name} className="flex items-center justify-between"><div className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${s.dot}`} /><p className="text-[13px] text-slate-300">{s.name}</p></div><span className="text-[11px] text-slate-500">{s.status}</span></div>)}</div></Card>
    </div>
  </div>;
}
