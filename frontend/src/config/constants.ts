// frontend/src/config/constants.ts

export const APP_CONFIG = {
  MAX_TOP_K: 20,
  DEFAULT_TOP_K: 8,
  SEARCH_DEBOUNCE_MS: 350,
  TOAST_DURATION: 2500,
  QUERY_STALE_MS: 1000 * 60 * 2,
  POLL_INTERVAL_MS: 1500,
} as const;

export const SIDEBAR_NAV = [
  {
    section: "Workspace",
    items: [
      {
        label: "Dashboard",
        path: "/dashboard",
        icon: "dashboard" as const,
        desc: "Overview & health",
      },
      {
        label: "Talent Search",
        path: "/talent",
        icon: "talent" as const,
        desc: "Search, filter, shortlist",
      },
      {
        label: "Agentic Hire",
        path: "/hire",
        icon: "hire" as const,
        desc: "JD → Rank → Outreach",
        badge: "AI",
      },
    ],
  },
  {
    section: "Tools",
    items: [
      {
        label: "Resume Ingest",
        path: "/upload",
        icon: "upload" as const,
        desc: "Upload & index",
      },
      {
        label: "Talent Chat",
        path: "/chat",
        icon: "chat" as const,
        desc: "RAG Q&A",
      },
    ],
  },
] as const;

export const STORAGE_KEYS = {
  hire: "hire-store-v2",
  searchQuery: "rh_search_query",
  // ✅ dropdownOptions removed — filter options now come from GET /api/filters
} as const;
