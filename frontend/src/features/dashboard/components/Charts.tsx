import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Card } from "@/components/ui/card";
import type { DashboardStats } from "@/types/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

export default function Charts({ charts }: { charts: NonNullable<DashboardStats["charts"]> }) {
  const topSkills = charts.top_skills;
  const expDist = charts.experience_dist;

  const skillData = {
    labels: topSkills?.labels ?? [],
    datasets: [
      {
        label: "Top skills",
        data: topSkills?.data ?? [],
        backgroundColor: "rgba(139, 92, 246, 0.7)",
        borderRadius: 6,
      },
    ],
  };

  const expData = {
    labels: expDist?.labels ?? [],
    datasets: [
      {
        label: "Experience (years)",
        data: expDist?.data ?? [],
        backgroundColor: ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24"],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card className="p-6">
        <h3 className="text-[14px] font-semibold text-white">Top skills</h3>
        <div className="mt-5 h-[260px]">
          <Bar
            data={skillData}
            options={{
              maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: {
                x: { grid: { color: "rgba(148,163,184,0.1)" }, ticks: { color: "#94a3b8" } },
                y: { grid: { color: "rgba(148,163,184,0.1)" }, ticks: { color: "#94a3b8" } },
              },
            }}
          />
        </div>
      </Card>
      <Card className="p-6">
        <h3 className="text-[14px] font-semibold text-white">Experience distribution</h3>
        <div className="mt-5 flex h-[260px] items-center justify-center">
          <Doughnut
            data={expData}
            options={{
              maintainAspectRatio: false,
              cutout: "65%",
              plugins: { legend: { position: "bottom", labels: { color: "#cbd5e1", boxWidth: 12 } } },
            }}
          />
        </div>
      </Card>
    </div>
  );
}
