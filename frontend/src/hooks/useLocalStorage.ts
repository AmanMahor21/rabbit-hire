import { useCallback, useEffect, useState } from "react";

export function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // quota exceeded - ignore
    }
  }, [key, value]);

  const remove = useCallback(() => {
    try {
      localStorage.removeItem(key);
      setValue(initial);
    } catch {}
  }, [key, initial]);

  return [value, setValue, remove] as const;
}
