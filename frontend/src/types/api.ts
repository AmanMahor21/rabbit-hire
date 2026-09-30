// frontend/src/types/api.ts

export type ApiError = {
  detail?: string;
  message?: string;
  error?: string;
};

export type PaginatedResponse<T> = {
  results: T[];
  total?: number;
  charts?: Record<string, unknown>;
};

export type SearchFiltersDto = {
  skills?: string[];
  locations?: string[];
  domains?: string[];
  degrees?: string[];
  experience?: number;
  strict_skill_search?: boolean;
  has_clearance?: boolean;
};

export type ResumeItem = {
  id: string;
  filename: string;
  name?: string;
  full_name?: string;
  skills: string[];
  location: string[];
  domains: string[];
  experience_years?: number;
  experience?: number;
  email?: string | null;
  phone?: string | null;
  text?: string;
  summary?: string;
  rank_score?: number;
  ranking_reason?: string;
};

export type DashboardStats = {
  total_resumes: number;
  parsed_resumes: number;
  unique_skills: number;
  total_candidates?: number;
};

export type HireJob = {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  stage: string;
  progress: number;
  result?: {
    results: ResumeItem[];
    outreach?: { candidate_id: string; email_body: string }[];
  };
  error?: string;
};

export type FilterOptions = {
  skills: string[];
  locations: string[];
  domains: string[];
  degrees: string[];
  experience_range: { min: number; max: number };
  skill_counts: Record<string, number>;
  location_counts: Record<string, number>;
  domain_counts: Record<string, number>;
};
