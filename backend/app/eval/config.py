from __future__ import annotations

EVAL_CONFIG = {
    "search": {
        "min_recall_at_k": 0.7,
        "min_precision_at_k": 0.5,
        "min_ndcg": 0.65,
        "k": 8,
        "drift_threshold": 0.05,  # fail CI if recall drops >5%
    },
    "parser": {
        "min_skill_f1": 0.75,
        "min_exp_accuracy": 0.85,
    },
    "ranker": {
        "min_spearman": 0.7,
        "min_top1_accuracy": 0.8,
        "max_score_mae": 15.0, # vs human ideal score
    },
    "rag": {
        "min_faithfulness": 0.8,
        "min_answer_relevancy": 0.75,
        "min_context_precision": 0.7,
    },
    "llm_judge": {
        "model": "gpt-4o-mini",  # cheap judge
        "temperature": 0.0,
    }
}

ERROR_TAXONOMY = [
    "skill_missed",
    "skill_hallucinated", 
    "location_wrong",
    "experience_misparsed",
    "domain_misclassified",
    "ranking_keyword_overfit",
    "ranking_exp_ignored",
    "rag_unfaithful",
    "rag_irrelevant",
    "outreach_generic",
    "filter_ignored",
]
