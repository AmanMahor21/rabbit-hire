
import { create } from "zustand";

type Filters = {
  skills: string[];
  locations: string[];
  domains: string[];
  degrees: string[];
  experience: number;
};

type SearchState = {
  query: string;
  filters: Filters;
  topK: number;
  setQuery: (q: string) => void;
  setFilters: (f: Partial<Filters>) => void;
  toggleFilter: (key: keyof Omit<Filters, "experience">, value: string) => void;
  clearFilters: () => void;
  setTopK: (k: number) => void;
  reset: () => void;
};

const createInitialFilters = (): Filters => ({
  skills: [], locations: [], domains: [], degrees: [], experience: 0,
});

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  filters: createInitialFilters(),
  topK: 8,
  setQuery: (query) => set({ query }),
  setFilters: (partial) => set((s) => ({ filters: { ...s.filters, ...partial } })),
  toggleFilter: (key, value) =>
    set((s) => {
      const current = s.filters[key] as string[];
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
      return { filters: { ...s.filters, [key]: next } };
    }),
  clearFilters: () => set({ filters: createInitialFilters() }),
  setTopK: (topK) => set({ topK }),
  reset: () => set({ query: "", filters: createInitialFilters(), topK: 8 }),
}));
