import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { ErrorBoundary } from "@/components/errors/ErrorBoundary";
import { APP_CONFIG } from "@/config/constants";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: APP_CONFIG.QUERY_STALE_MS, gcTime: 1000 * 60 * 30 },
  },
});

export function AppProvider({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ErrorBoundary>
          {children}
          <ToastContainer
            position="top-right"
            autoClose={APP_CONFIG.TOAST_DURATION}
            hideProgressBar
            theme="dark"
            toastClassName="!bg-[var(--color-surface-raised)] !border !border-[var(--color-border)] !text-slate-100 !rounded-xl !shadow-2xl"
          />
        </ErrorBoundary>
      </QueryClientProvider>
    </BrowserRouter>
  );
}
