
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { STORAGE_KEYS } from "@/config/constants";

type HireState = {
  jd: string;
  topK: number;
  autoOutreach: boolean;
  activeJobId: string | null;
  setJd: (jd: string) => void;
  setTopK: (k: number) => void;
  setAutoOutreach: (v: boolean) => void;
  setActiveJobId: (id: string | null) => void;
  clear: () => void;
};

export const useHireStore = create<HireState>()(
  persist(
    (set) => ({
      jd: "",
      topK: 8,
      autoOutreach: true,
      activeJobId: null,
      setJd: (jd) => set({ jd }),
      setTopK: (topK) => set({ topK }),
      setAutoOutreach: (autoOutreach) => set({ autoOutreach }),
      setActiveJobId: (activeJobId) => set({ activeJobId }),
      clear: () => set({ jd: "", topK: 8, autoOutreach: true, activeJobId: null }),
    }),
    {
      name: STORAGE_KEYS.hire,
      partialize: (s) => ({ topK: s.topK, autoOutreach: s.autoOutreach, activeJobId: s.activeJobId }),
    }
  )
);
