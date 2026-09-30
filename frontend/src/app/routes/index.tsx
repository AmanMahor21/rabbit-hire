
import { Navigate, useRoutes } from "react-router";
import { MainLayout } from "@/components/layout/MainLayout";
import { PATHS } from "./paths";
import { lazy, Suspense } from "react";
const DashboardPage = lazy(() => import("@/features/dashboard/DashboardPage"));
const TalentPage = lazy(() => import("@/features/talent/TalentPage"));
const HirePage = lazy(() => import("@/features/hire/HirePage"));
const UploadPage = lazy(() => import("@/features/upload/UploadPage"));
const ChatPage = lazy(() => import("@/features/chat/ChatPage"));
const LoginPage = lazy(() => import("@/features/auth/LoginPage"));

function Protected({ children }: { children: React.ReactNode }) {
  const token = typeof window !== "undefined" ? localStorage.getItem("rh_token") : null;
  // For now allow if no auth required - remove check if you want public
  // if (!token) return <Navigate to={PATHS.login} replace />;
  return <>{children}</>;
}

export function AppRoutes() {
  const element = useRoutes([
    { path: PATHS.login, element: <LoginPage /> },
    { path: PATHS.root, element: <Protected><MainLayout /></Protected>, children: [
      { index: true, element: <Navigate to={PATHS.dashboard} replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "talent", element: <TalentPage /> },
      { path: "hire", element: <HirePage /> },
      { path: "upload", element: <UploadPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "candidates", element: <Navigate to={PATHS.talent} replace /> },
      { path: "resume-search", element: <Navigate to={PATHS.talent} replace /> },
      { path: "resume-upload", element: <Navigate to={PATHS.upload} replace /> },
      { path: "jd-candidates", element: <Navigate to={PATHS.hire} replace /> },
      { path: "agentic-hire", element: <Navigate to={PATHS.hire} replace /> },
    ]},
    { path: "*", element: <Navigate to={PATHS.dashboard} replace /> },
  ]);
  return <Suspense fallback={<div className="flex h-dvh items-center justify-center bg-[var(--color-bg)]"><div className="flex flex-col items-center gap-3"><div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-700 border-t-cyan-400" /><p className="text-sm text-slate-500">Loading workspace…</p></div></div>}>{element}</Suspense>;
}
