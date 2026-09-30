
const getEnv = (key: string, fallback?: string) => {
  const v = (import.meta.env as any)[key] as string | undefined;
  return v ?? fallback;
};

function requireEnv(key: string, fallback?: string) {
  const v = getEnv(key, fallback);
  if (!v) throw new Error(`Missing env: ${key}`);
  return v;
}

export const env = {
  API_URL: getEnv("VITE_API_URL", "/api")!,
  APP_NAME: getEnv("VITE_APP_NAME", "Rabbit Hire")!,
  isProd: import.meta.env.PROD,
  isDev: import.meta.env.DEV,
} as const;
