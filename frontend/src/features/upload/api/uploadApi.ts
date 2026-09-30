import { apiClient } from "@/lib/api-client";
export const uploadApi = {
  upload: (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return apiClient
      .post<{ message: string }>("/upload", form, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
  process: () =>
    apiClient.post<{ message: string; filters?: Record<string, string[]> }>("/process").then((r) => r.data),
};
