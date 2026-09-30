
import { apiClient } from "@/lib/api-client";
import type { ResumeItem } from "@/types/api";
export type ChatResponse = { answer: string; candidates?: ResumeItem[] };
export const chatApi = { chat: (message: string, history: { role: string; content: string }[]) => apiClient.post<ChatResponse>("/chat", { message, history }).then(r => r.data) };
