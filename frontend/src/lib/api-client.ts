import axios, { AxiosError } from "axios";
import { env } from "@/config/env";
import type { ApiError } from "@/types/api";

export const apiClient = axios.create({
  baseURL: env.API_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("rh_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError<ApiError>) => {
    const data = error.response?.data;
    const message = data?.detail || data?.message || data?.error || error.message || "Something went wrong";
    const err = new Error(message) as Error & { status?: number; data?: ApiError };
    err.status = error.response?.status;
    err.data = data;
    return Promise.reject(err);
  }
);
