import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { StatCard } from "./components/StatCard";
import { dashboardApi } from "./api/dashboardApi";
import { PATHS } from "@/app/routes/paths";
import { Button } from "@/components/ui/button";
import { FiSearch, FiUploadCloud } from "react-icons/fi";
import { Skeleton } from "@/components/ui/skeleton";
import Charts from "./components/Charts";
export default function DashboardPage() {
  const { data, isLoading, isError, error } = useQuery({ queryKey: ["stats"], queryFn: dashboardApi.getStats });
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-white">Dashboard</h1>
          <p className="mt-1 text-[13px] text-slate-400">Talent pipeline overview</p>
        </div>
        <div className="flex gap-2">
          <Link to={PATHS.upload}>
            <Button variant="secondary">
              <FiUploadCloud className="mr-2 h-4 w-4" />
              Ingest resumes
            </Button>
          </Link>
          <Link to={PATHS.talent}>
            <Button>
              <FiSearch className="mr-2 h-4 w-4" />
              Search talent
            </Button>
          </Link>
        </div>
      </div>
      {isError && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-[13px] text-red-300">
          {(error as Error).message}
        </div>
      )}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {isLoading ? (
          <>
            <Skeleton className="h-[132px]" />
            <Skeleton className="h-[132px]" />
            <Skeleton className="h-[132px]" />
          </>
        ) : (
          <>
            <StatCard title="Total resumes" value={data?.total_resumes ?? 0} change="+12%" />
            <StatCard title="Indexed profiles" value={data?.parsed_resumes ?? data?.total_resumes ?? 0} change="+8%" />
            <StatCard title="Unique skills" value={data?.unique_skills ?? 0} change="+23" />
          </>
        )}
      </div>
      {data?.charts && (data.charts.top_skills || data.charts.experience_dist) ? <Charts charts={data.charts} /> : null}
    </div>
  );
}
