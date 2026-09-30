// frontend/src/components/layout/Sidebar.tsx

import { NavLink, useLocation } from "react-router";
import { SIDEBAR_NAV } from "@/config/constants";
import { cn } from "@/lib/cn";
import { FiGrid, FiSearch, FiCpu, FiUploadCloud, FiMessageSquare, FiZap } from "react-icons/fi";
import { useState } from "react";

const iconMap = {
  dashboard: FiGrid,
  talent: FiSearch,
  hire: FiCpu,
  upload: FiUploadCloud,
  chat: FiMessageSquare,
} as const;

export function Sidebar({ open, setOpen }: { open?: boolean; setOpen?: (v: boolean) => void }) {
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const isMobileOpen = open === true;

  return (
    <>
      {/* 
        FIX 1: Lowered z-index to var(--z-overlay) - 1 
        so it sits BEHIND the sidebar but IN FRONT of the main content 
      */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 lg:hidden"
          style={{ zIndex: "var(--z-overlay)" }} // Explicitly set lower z-index
          onClick={() => setOpen?.(false)}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 flex h-dvh flex-col border-r border-[var(--color-border)] bg-[var(--color-bg-soft)] transition-all duration-300",
          collapsed ? "w-[72px]" : "w-[268px]",
          // FIX 2: Ensure Sidebar Z-index is strictly higher than overlay
          "z-[calc(var(--z-overlay)+10)]",
          !isMobileOpen && "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* ... existing header code ... */}
        <div className="flex h-[64px] items-center gap-3 border-b border-[var(--color-border)] px-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-black font-bold text-[13px]">
            R
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-[13px] font-semibold text-white">Rabbit Hire</p>
              <p className="mt-1 text-[11px] text-slate-500">Agentic Talent OS</p>
            </div>
          )}
          <button
            aria-label="Toggle sidebar"
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto hidden h-7 w-7 items-center justify-center rounded-lg text-slate-500 hover:bg-white/5 lg:flex"
          >
            ‹›
          </button>
        </div>

        {/* ... existing nav code ... */}
        <div className="flex-1 overflow-y-auto px-3 py-4 scroll-thin">
          <div className="space-y-6">
            {SIDEBAR_NAV.map((sec) => (
              <div key={sec.section}>
                {!collapsed && (
                  <h3 className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                    {sec.section}
                  </h3>
                )}
                <div className="space-y-1">
                  {sec.items.map((item) => {
                    const Icon = iconMap[item.icon as keyof typeof iconMap] || FiGrid;
                    const active = pathname === item.path || pathname.startsWith(item.path + "/");
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={() => setOpen?.(false)}
                        className={cn(
                          "group flex items-center gap-3 rounded-xl px-2.5 py-2.5 text-[13px] font-medium transition-colors focus-ring",
                          active ? "bg-white text-black" : "text-slate-400 hover:bg-white/[0.06] hover:text-slate-100"
                        )}
                        title={item.label}
                      >
                        <Icon
                          className={cn(
                            "h-[18px] w-[18px] shrink-0",
                            active ? "text-black" : "text-slate-400 group-hover:text-slate-200"
                          )}
                        />
                        {!collapsed && (
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="truncate">{item.label}</span>
                              {"badge" in item && item.badge && (
                                <span
                                  className={cn(
                                    "rounded-full px-1.5 py-0.5 text-[10px] font-bold",
                                    active ? "bg-black text-white" : "bg-white/10 text-white"
                                  )}
                                >
                                  {(item as any).badge}
                                </span>
                              )}
                            </div>
                            <p
                              className={cn(
                                "truncate text-[11px] font-normal",
                                active ? "text-black/60" : "text-slate-500"
                              )}
                            >
                              {item.desc}
                            </p>
                          </div>
                        )}
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* ... existing footer/promo code ... */}
          {!collapsed && (
            <div className="mt-8 rounded-xl border border-[var(--color-border)] bg-gradient-to-b from-[var(--color-surface-raised)] to-[var(--color-surface)] p-3">
              <div className="flex items-center gap-2">
                <FiZap className="h-4 w-4 text-cyan-400" />
                <p className="text-[12px] font-medium text-white">Vector DB</p>
                <span className="ml-auto h-2 w-2 rounded-full bg-emerald-400" />
              </div>
              <p className="mt-2 text-[11px] leading-4 text-slate-400">Qdrant • LangGraph • RAG indexed and ready.</p>
            </div>
          )}
        </div>

        {/* ... existing user profile code ... */}
        <div className="border-t border-[var(--color-border)] p-3">
          <div className="flex items-center gap-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] px-3 py-2.5">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-cyan-400" />
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-[12px] font-medium text-white">Aman • Admin</p>
                <p className="truncate text-[11px] text-slate-500">aman@rabbithire.ai</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
