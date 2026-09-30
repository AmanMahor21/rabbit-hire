# backend/app/agents/outreach_agent.py
from __future__ import annotations

from typing import Any

from app.core.llm import get_fast_llm

MAX_OUTREACH_CANDIDATES = 3


def outreach_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    ranked = state.get("ranked", [])
    auto_generate = state.get("auto_generate_outreach", False)

    print(auto_generate, "outreach_agent_node")
    print(ranked, "rankedddddddddddd node")

    if not auto_generate or not ranked:
        print("No outreach generation needed.")
        return {"outreach": []}

    job_description = state.get("job_description", "")
    candidates = ranked[:MAX_OUTREACH_CANDIDATES]
    llm = get_fast_llm(temperature=0.4)

    outreach: list[dict[str, Any]] = []

    for candidate in candidates:
        payload = candidate.get("payload", {})
        name = payload.get("name", "Candidate")
        email = payload.get("email")
        skills = payload.get("skills", [])

        prompt = f"""
Write a short, professional recruiter outreach email.

Candidate:
{name}

Skills:
{skills}

Job:
{job_description[:3000]}

Requirements:
- 100-150 words
- professional and personalized
- mention 1-2 relevant skills
- include a clear call to action
- do not invent candidate experience
- do not include a subject line

Return only the email body.
"""
        try:
            response = llm.invoke(prompt)
            content = getattr(response, "content", str(response)).strip()
            outreach.append({
                "candidate": name,
                "email": email,
                "message": content,
            })
        except Exception as exc:
            print(f"Outreach generation error for {name}: {exc}")
            outreach.append({
                "candidate": name,
                "email": email,
                "message": (
                    f"Hi {name},\n\n"
                    "I came across your profile and believe your background "
                    "could be relevant to an opportunity we are hiring for. "
                    "Would you be open to a quick conversation?\n\n"
                    "Best,\nRecruiting Team"
                ),
            })

    return {"outreach": outreach}
