// frontend/src/features/talent/components/FiltersPanel.tsx
import { useMemo, useState } from "react";
import Select from "react-select";
import { useSearchStore } from "@/stores/useSearchStore";
import { Skeleton } from "@/components/ui/skeleton";

type FilterOptionsShape = {
  skills: string[];
  locations: string[];
  domains: string[];
  degrees: string[];
  skill_counts?: Record<string, number>;
  location_counts?: Record<string, number>;
  domain_counts?: Record<string, number>;
};

type Props = {
  options: FilterOptionsShape;
  isLoading?: boolean;
  experienceRange?: { min: number; max: number };
};

const EMPTY: FilterOptionsShape = {
  skills: [],
  locations: [],
  domains: [],
  degrees: [],
  skill_counts: {},
  location_counts: {},
  domain_counts: {},
};

const POPULAR_COUNT = 12;

// Shared dark theme styles for react-select
const selectStyles = {
  control: (base: any, state: any) => ({
    ...base,
    background: "var(--color-surface)",
    borderColor: state.isFocused ? "var(--color-border-focus)" : "var(--color-border-strong)",
    borderRadius: "0.75rem",
    minHeight: "38px",
    boxShadow: state.isFocused ? "0 0 0 2px rgba(255,255,255,0.08)" : "none",
    "&:hover": { borderColor: "var(--color-border-strong)" },
  }),
  menu: (base: any) => ({
    ...base,
    background: "var(--color-surface-raised)",
    border: "1px solid var(--color-border)",
    borderRadius: "0.75rem",
    overflow: "hidden",
    zIndex: 60,
  }),
  menuList: (base: any) => ({ ...base, maxHeight: 240, padding: 4 }),
  option: (base: any, state: any) => ({
    ...base,
    background: state.isFocused ? "var(--color-surface-hover)" : "transparent",
    color: state.isSelected ? "#fff" : "var(--color-text)",
    fontSize: "13px",
    borderRadius: "0.5rem",
    cursor: "pointer",
    padding: "8px 10px",
  }),
  multiValue: (base: any) => ({
    ...base,
    background: "rgba(255,255,255,0.08)",
    borderRadius: "0.5rem",
  }),
  multiValueLabel: (base: any) => ({
    ...base,
    color: "#e2e8f0",
    fontSize: "12px",
    padding: "2px 6px",
  }),
  multiValueRemove: (base: any) => ({
    ...base,
    color: "#94a3b8",
    ":hover": { background: "rgba(255,255,255,0.1)", color: "#fff" },
  }),
  input: (base: any) => ({ ...base, color: "#e2e8f0", fontSize: "13px" }),
  placeholder: (base: any) => ({ ...base, color: "#64748b", fontSize: "13px" }),
  singleValue: (base: any) => ({ ...base, color: "#e2e8f0" }),
  dropdownIndicator: (base: any) => ({ ...base, color: "#64748b" }),
  clearIndicator: (base: any) => ({ ...base, color: "#64748b" }),
  indicatorSeparator: () => ({ display: "none" }),
  noOptionsMessage: (base: any) => ({ ...base, color: "#64748b", fontSize: "12px" }),
};

export function FiltersPanel({ options, isLoading, experienceRange }: Props) {
  const { filters, toggleFilter, setFilters } = useSearchStore();
  const safeOptions = options ?? EMPTY;
  const maxExp = experienceRange?.max ?? 20;
  const minExp = experienceRange?.min ?? 0;

  // react-select option shape — with count in the label
  const skillOptions = useMemo(
    () =>
      safeOptions.skills.map((s) => ({
        value: s,
        label: safeOptions.skill_counts?.[s] != null ? `${s} · ${safeOptions.skill_counts[s]}` : s,
      })),
    [safeOptions.skills, safeOptions.skill_counts]
  );
  const locationOptions = useMemo(
    () =>
      safeOptions.locations.map((l) => ({
        value: l,
        label: safeOptions.location_counts?.[l] != null ? `${l} · ${safeOptions.location_counts[l]}` : l,
      })),
    [safeOptions.locations, safeOptions.location_counts]
  );
  const domainOptions = useMemo(
    () =>
      safeOptions.domains.map((d) => ({
        value: d,
        label: safeOptions.domain_counts?.[d] != null ? `${d} · ${safeOptions.domain_counts[d]}` : d,
      })),
    [safeOptions.domains, safeOptions.domain_counts]
  );

  const selectedSkills = useMemo(() => filters.skills.map((s) => ({ value: s, label: s })), [filters.skills]);
  const selectedLocations = useMemo(() => filters.locations.map((l) => ({ value: l, label: l })), [filters.locations]);
  const selectedDomains = useMemo(() => filters.domains.map((d) => ({ value: d, label: d })), [filters.domains]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i}>
            <Skeleton className="mb-2 h-3 w-20" />
            <Skeleton className="h-10 w-full rounded-xl" />
          </div>
        ))}
        <div>
          <Skeleton className="mb-2 h-3 w-24" />
          <Skeleton className="h-2 w-full rounded-full" />
        </div>
      </div>
    );
  }

  // Popular skills — top N from the count-sorted list
  const popularSkills = safeOptions.skills.slice(0, POPULAR_COUNT);

  return (
    <div className="space-y-6">
      {/* ─── POPULAR SKILLS (quick click chips) ─── */}
      {popularSkills.length > 0 && (
        <div>
          <h4 className="mb-2 text-[12px] font-medium text-white">Popular skills</h4>
          <div className="flex flex-wrap gap-1.5">
            {popularSkills.map((s) => {
              const active = filters.skills.includes(s);
              const count = safeOptions.skill_counts?.[s];
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => toggleFilter("skills", s)}
                  className={`rounded-full border px-2.5 py-1 text-[11px] transition-colors ${
                    active
                      ? "border-white bg-white text-black"
                      : "border-[var(--color-border)] bg-[var(--color-surface)] text-slate-300 hover:border-[var(--color-border-strong)] hover:text-white"
                  }`}
                  title={count != null ? `${count} candidates` : s}
                >
                  {s}
                  {count != null && (
                    <span className={`ml-1 ${active ? "text-black/60" : "text-slate-500"}`}>{count}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ─── SKILLS MULTISELECT ─── */}
      <div>
        <h4 className="mb-2 text-[12px] font-medium text-white">
          Skills {filters.skills.length > 0 && <span className="ml-1 text-slate-500">({filters.skills.length})</span>}
        </h4>
        <Select
          isMulti
          isSearchable
          options={skillOptions}
          value={selectedSkills}
          onChange={(opts) => setFilters({ skills: (opts as any[]).map((o) => o.value) })}
          placeholder="Search skills..."
          styles={selectStyles}
          menuPortalTarget={typeof document !== "undefined" ? document.body : undefined}
          menuPosition="fixed"
          noOptionsMessage={({ inputValue }) =>
            inputValue ? `No skills match "${inputValue}"` : "No skills available"
          }
        />
      </div>

      {/* ─── LOCATION MULTISELECT ─── */}
      <div>
        <h4 className="mb-2 text-[12px] font-medium text-white">
          Location{" "}
          {filters.locations.length > 0 && <span className="ml-1 text-slate-500">({filters.locations.length})</span>}
        </h4>
        <Select
          isMulti
          isSearchable
          options={locationOptions}
          value={selectedLocations}
          onChange={(opts) => setFilters({ locations: (opts as any[]).map((o) => o.value) })}
          placeholder="Search locations..."
          styles={selectStyles}
          menuPortalTarget={typeof document !== "undefined" ? document.body : undefined}
          menuPosition="fixed"
        />
      </div>

      {/* ─── DOMAIN MULTISELECT ─── */}
      <div>
        <h4 className="mb-2 text-[12px] font-medium text-white">
          Domain {filters.domains.length > 0 && <span className="ml-1 text-slate-500">({filters.domains.length})</span>}
        </h4>
        <Select
          isMulti
          isSearchable
          options={domainOptions}
          value={selectedDomains}
          onChange={(opts) => setFilters({ domains: (opts as any[]).map((o) => o.value) })}
          placeholder="Search domains..."
          styles={selectStyles}
          menuPortalTarget={typeof document !== "undefined" ? document.body : undefined}
          menuPosition="fixed"
        />
      </div>

      {/* ─── DEGREE (kept as chips — small list) ─── */}
      <div>
        <h4 className="mb-2 text-[12px] font-medium text-white">Degree</h4>
        <div className="flex flex-wrap gap-1.5">
          {safeOptions.degrees.map((d) => {
            const active = filters.degrees.includes(d);
            return (
              <button
                key={d}
                type="button"
                onClick={() => toggleFilter("degrees", d)}
                className={`rounded-full border px-2.5 py-1 text-[11px] transition-colors ${
                  active
                    ? "border-white bg-white text-black"
                    : "border-[var(--color-border)] bg-[var(--color-surface)] text-slate-400 hover:text-white"
                }`}
              >
                {d}
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── MIN EXPERIENCE ─── */}
      <div>
        <h4 className="mb-2 text-[12px] font-medium text-white">Min Experience</h4>
        <input
          type="range"
          min={minExp}
          max={maxExp}
          value={filters.experience}
          onChange={(e) => setFilters({ experience: Number(e.target.value) })}
          className="w-full"
        />
        <div className="flex justify-between text-[11px] text-slate-500">
          <span>{filters.experience} yrs</span>
          <span>max {maxExp}</span>
        </div>
      </div>
    </div>
  );
}
