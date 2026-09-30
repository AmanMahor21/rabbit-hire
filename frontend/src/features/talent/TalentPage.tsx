// frontend/src/features/talent/TalentPage.tsx
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchStore } from "@/stores/useSearchStore";
import { useDebounce } from "@/hooks/useDebounce";
import { candidateApi } from "./api/candidateApi";
import { useFilterOptions } from "./hooks/useFilterOptions";
import { CandidateCard } from "./components/CandidateCard";
import { CandidateDetailDrawer } from "./components/CandidateDetailDrawer";
import { FiltersPanel } from "./components/FiltersPanel";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { APP_CONFIG } from "@/config/constants";
import { FiSearch, FiSliders, FiX, FiZap, FiArrowUpRight } from "react-icons/fi";
import { CardSkeleton } from "@/components/ui/skeleton";
import type { ResumeItem } from "@/types/api";

export default function TalentPage() {
  const { query, setQuery, filters, topK, setTopK } = useSearchStore();
  const debounced = useDebounce(query, APP_CONFIG.SEARCH_DEBOUNCE_MS);
  const [selected, setSelected] = useState<ResumeItem | null>(null);
  const [showFilters, setShowFilters] = useState(true);

  const { data: filterOptions, isLoading: filtersLoading, isError: filtersError } = useFilterOptions();

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["talent-search", debounced, filters, topK],
    queryFn: () => candidateApi.search({ query: debounced, filters, top_k: topK }),
    enabled: debounced.trim().length > 1,
  });

  const list = data?.results || [];

  const activeFilterCount = useMemo(
    () =>
      filters.skills.length +
      filters.locations.length +
      filters.domains.length +
      filters.degrees.length +
      (filters.experience ? 1 : 0),
    [filters]
  );

  return (
    <div className="space-y-5">
      <Card className="p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <FiSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && refetch()}
              placeholder="Try: Python developer with RAG and 3 years in Bangalore"
              className="h-11 w-full rounded-xl border border-[var(--color-border-strong)] bg-[var(--color-surface)] pl-10 pr-10 text-[14px] text-white outline-none placeholder:text-slate-500 focus:border-[var(--color-border-focus)] focus:ring-2 focus:ring-white/10"
            />
            {query && (
              <button
                type="button"
                aria-label="Clear"
                onClick={() => setQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
              >
                <FiX className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="flex h-11 items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3">
              <span className="text-[11px] text-slate-500">Top K</span>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="bg-transparent text-[13px] text-white outline-none"
              >
                {[8, 12, 16, 20].map((k) => (
                  <option key={k} value={k} className="bg-[var(--color-surface)]">
                    {k}
                  </option>
                ))}
              </select>
            </div>

            <Button
              variant={showFilters ? "primary" : "secondary"}
              onClick={() => setShowFilters(!showFilters)}
              className="h-11"
            >
              <FiSliders className="mr-2 h-4 w-4" />
              Filters
              {activeFilterCount > 0 && (
                <span className="ml-1 rounded-full bg-black/20 px-1.5 py-0.5 text-[11px] text-white">
                  {activeFilterCount}
                </span>
              )}
            </Button>

            <Button onClick={() => refetch()} className="h-11">
              <FiZap className="mr-2 h-4 w-4" />
              Search
            </Button>
          </div>
        </div>

        {(isFetching || isLoading) && (
          <div className="mt-3 flex items-center gap-2 text-[12px] text-slate-500">
            <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-600 border-t-white" />
            Searching vector DB…
          </div>
        )}
      </Card>

      <div className={`grid grid-cols-1 gap-4 ${showFilters ? "lg:grid-cols-[300px_1fr]" : "lg:grid-cols-1"}`}>
        {showFilters && (
          <Card className="h-fit p-5 lg:sticky lg:top-[88px]">
            {filtersError ? (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-[12px] text-red-300">
                Could not load filter options. Please refresh.
              </div>
            ) : (
              <FiltersPanel
                options={{
                  skills: filterOptions?.skills ?? [],
                  locations: filterOptions?.locations ?? [],
                  domains: filterOptions?.domains ?? [],
                  degrees: filterOptions?.degrees ?? [],
                  skill_counts: filterOptions?.skill_counts ?? {},
                  location_counts: filterOptions?.location_counts ?? {},
                  domain_counts: filterOptions?.domain_counts ?? {},
                }}
                isLoading={filtersLoading}
                experienceRange={filterOptions?.experience_range}
              />
            )}
          </Card>
        )}

        <div className="min-w-0 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[14px] font-medium text-white">
              {list.length > 0 ? (
                <span className="flex items-center gap-2">
                  <span>{list.length} candidates</span>
                  <span className="font-normal text-slate-500">for “{debounced}”</span>
                </span>
              ) : debounced ? (
                <span className="text-slate-500">No results yet</span>
              ) : (
                <span className="text-slate-500">Start typing to search</span>
              )}
            </h2>
            {list.length > 0 && (
              <div className="flex items-center gap-1 text-[11px] text-slate-500">
                <FiArrowUpRight />
                Sorted by semantic relevance
              </div>
            )}
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {list.map((c) => (
                <CandidateCard
                  key={c.id}
                  candidate={c}
                  onClick={() => setSelected(c)}
                  selected={selected?.id === c.id}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <CandidateDetailDrawer candidate={selected} open={!!selected} onClose={() => setSelected(null)} />
    </div>
  );
}
