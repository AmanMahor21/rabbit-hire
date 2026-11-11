"""
Human Evaluation helpers - LLM-as-judge + human rating aggregation
"""
from __future__ import annotations
from typing import List, Dict
from app.core.llm import get_fast_llm
from app.eval.config import EVAL_CONFIG

JUDGE_PROMPT = """
You are an expert evaluator for a talent search system.

Job Description:
{job_description}

Candidate: {candidate_filename}
Candidate Skills: {candidate_skills}
Candidate Experience: {candidate_exp} years

Human ideal score: {human_score}
AI predicted score: {ai_score}
AI reasoning: {ai_reasoning}

Rate on 1-5:
- 5 = Perfect match, reasoning is faithful
- 4 = Good match, minor reasoning flaw
- 3 = Partial match
- 2 = Poor match, reasoning hallucinated
- 1 = Completely wrong

Return JSON: {{"rating": int, "faithful": bool, "error_tags": [], "comment": str}}
"""

def llm_as_judge(job_description: str, candidate: Dict, ai_result: Dict, human_ideal: Dict) -> Dict:
    llm = get_fast_llm(temperature=EVAL_CONFIG["llm_judge"]["temperature"])
    if not llm:
        return {"rating": 3, "faithful": True, "error_tags": [], "comment": "LLM not configured"}
    
    payload = candidate.get("payload", {})
    prompt = JUDGE_PROMPT.format(
        job_description=job_description[:1000],
        candidate_filename=payload.get("filename",""),
        candidate_skills=payload.get("skills", [])[:10],
        candidate_exp=payload.get("experience", 0),
        human_score=human_ideal.get("score", 0),
        ai_score=ai_result.get("rank_score", 0),
        ai_reasoning=ai_result.get("ranking_reason", "")[:500]
    )
    
    try:
        res = llm.invoke(prompt)
        content = getattr(res, "content", str(res))
        import json
        start = content.find("{")
        end = content.rfind("}")
        if start != -1:
            return json.loads(content[start:end+1])
        return {"rating": 3, "comment": content[:200]}
    except Exception as e:
        return {"rating": 3, "error": str(e)}

def aggregate_human_ratings(feedbacks: List[Dict]) -> Dict:
    from collections import Counter
    ratings = [f.get("human_rating", 3) for f in feedbacks]
    avg = sum(ratings)/len(ratings) if ratings else 0
    dist = Counter(ratings)
    return {
        "count": len(ratings),
        "avg_rating": avg,
        "distribution": dict(dist),
        "nps": (dist.get(5,0) + dist.get(4,0) - dist.get(1,0) - dist.get(2,0)) / len(ratings) if ratings else 0
    }
