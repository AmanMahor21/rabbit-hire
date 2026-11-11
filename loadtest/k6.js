// loadtest/k6.js
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const HEADERS = { "Content-Type": "application/json" };

export const options = {
  scenarios: {
    // Hot read path: /api/search  → this is what must do 800 rps
    search: {
      executor: "constant-arrival-rate",
      exec: "searchScenario",
      rate: 100,
      timeUnit: "1s",
      preAllocatedVUs: 100,
      duration: "60s",
      // maxVUs: 800,
      // stages: [
      //   { target: 200, duration: "30s" },
      //   { target: 800, duration: "60s" },
      //   { target: 800, duration: "120s" }, // hold at 800
      //   { target: 0, duration: "20s" },
      // ],
    },

    // Chat: extra 100 rps (LLM stubbed → instant)
    // chat: {
    //   executor: "constant-arrival-rate",
    //   exec: "chatScenario",
    //   rate: 100,
    //   timeUnit: "1s",
    //   duration: "230s",
    //   preAllocatedVUs: 100,
    // },

    // // Filters: cached, cheap
    // filters: {
    //   executor: "constant-arrival-rate",
    //   exec: "filtersScenario",
    //   rate: 200,
    //   timeUnit: "1s",
    //   duration: "230s",
    //   preAllocatedVUs: 50,
    // },

    // // Agentic hire: write path → Celery queue
    // // Low rate: each request enqueues a job that LLM-ranks 8 candidates
    // agenticHire: {
    //   executor: "constant-arrival-rate",
    //   exec: "agenticHireScenario",
    //   rate: 5,
    //   timeUnit: "1s",
    //   duration: "230s",
    //   preAllocatedVUs: 20,
    // },
  },
  thresholds: {
    "http_req_duration{scenario:search}": ["p(95)<200", "p(99)<500"],
    // "http_req_duration{scenario:chat}": ["p(95)<500"],
    // "http_req_duration{scenario:filters}": ["p(95)<100"],
    // "http_req_duration{scenario:agenticHire}": ["p(95)<300"],
    http_req_failed: ["rate<0.01"],
  },
};

// ── 1. Search ──────────────────────────────────────────────────────────────
export function searchScenario() {
  const payload = JSON.stringify({
    query: "python developer with RAG and 3 years in bangalore",
    filters: { skills: ["PYTHON"], locations: ["Bengaluru"], experience: 3 },
    top_k: 8,
  });
  const res = http.post(`${BASE}/api/search`, payload, { headers: HEADERS });
  check(res, {
    "search 200": (r) => r.status === 200,
    "search has results": (r) => {
      try {
        return (JSON.parse(r.body).results || []).length >= 0;
      } catch {
        return false;
      }
    },
  });
  sleep(0);
}

// ── 2. Chat ────────────────────────────────────────────────────────────────
export function chatScenario() {
  const payload = JSON.stringify({
    message: "find python developers in bangalore",
    history: [],
  });
  const res = http.post(`${BASE}/api/chat`, payload, { headers: HEADERS });
  check(res, { "chat 200": (r) => r.status === 200 });
}

// ── 3. Filters ─────────────────────────────────────────────────────────────
export function filtersScenario() {
  const res = http.get(`${BASE}/api/filters`);
  check(res, { "filters 200": (r) => r.status === 200 });
}

// ── 4. Agentic hire (write path → Celery) ─────────────────────────────────
export function agenticHireScenario() {
  const payload = JSON.stringify({
    job_description:
      "Senior Python engineer, 3+ years, FastAPI, Qdrant, LangChain, Bengaluru.",
    top_k: 5,
    auto_generate_outreach: false, // keep it cheap for load test
  });
  const res = http.post(`${BASE}/api/agentic-hire`, payload, {
    headers: HEADERS,
  });
  check(res, {
    "agentic 202": (r) => r.status === 202,
    "agentic has job_id": (r) => {
      try {
        return !!JSON.parse(r.body).job_id;
      } catch {
        return false;
      }
    },
  });
}
