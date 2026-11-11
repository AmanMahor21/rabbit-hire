# backend/app/eval/runners/test_search.py
"""
Pytest runner for search eval - automated + regression
"""
from __future__ import annotations

import json
import pathlib

import pytest

from app.eval.metrics import precision_at_k, recall_at_k, ndcg_at_k, mrr
from app.eval.config import EVAL_CONFIG

# ✅ The committed file is a JSON array (search_golden.json), not JSONL.
GOLDEN = pathlib.Path(__file__).parent.parent / \
    "datasets" / "search_golden.json"


def load_golden():
    """
    Load the search golden set.

    Fails loudly if the file is missing or malformed. A silently-empty golden
    set would let regressions pass CI, which defeats the purpose of eval.
    """
    if not GOLDEN.exists():
        raise FileNotFoundError(
            f"Search golden set not found at {GOLDEN}. "
            "Eval cannot run without it."
        )
    with open(GOLDEN, "r", encoding="utf-8") as f:
        cases = json.load(f)
    if not isinstance(cases, list) or not cases:
        raise ValueError(
            f"Search golden set at {GOLDEN} must be a non-empty JSON array."
        )
    return cases


@pytest.mark.eval
@pytest.mark.parametrize("case", load_golden())
def test_search_case(case):
    from app.services.vectorstore import hybrid_search, filter_only_search

    query = case.get("query", "").strip()
    filters = case.get("filters")

    if query:
        results = hybrid_search(
            query=query, top_k=EVAL_CONFIG["search"]["k"], filters=filters)
    else:
        results = filter_only_search(
            filters=filters, top_k=EVAL_CONFIG["search"]["k"])

    pred = [r["payload"]["filename"] for r in results]
    expected = case["expected_ids"]
    graded = case.get("graded_relevance", {})

    rec = recall_at_k(pred, expected, k=EVAL_CONFIG["search"]["k"])
    prec = precision_at_k(pred, expected, k=EVAL_CONFIG["search"]["k"])
    ndcg = ndcg_at_k(pred, graded, k=EVAL_CONFIG["search"]["k"])

    # Attach for reporting
    print(f"\n[{case['id']}] R@{EVAL_CONFIG['search']['k']}={rec:.2f} P={prec:.2f} NDCG={ndcg:.2f} | pred={pred[:3]}")

    assert rec >= EVAL_CONFIG["search"][
        "min_recall_at_k"], f"Recall {rec} < threshold for {case['id']}. Pred: {pred}, Exp: {expected}"
    assert ndcg >= EVAL_CONFIG["search"]["min_ndcg"] - \
        0.2, f"NDCG too low for {case['id']}"


def run_search_eval_detailed():
    """Non-pytest runner for CI reports"""
    cases = load_golden()
    results = []
    for case in cases:
        from app.services.vectorstore import hybrid_search, filter_only_search
        query = case.get("query", "").strip()
        filters = case.get("filters")
        if query:
            res = hybrid_search(query=query, top_k=8, filters=filters)
        else:
            res = filter_only_search(filters=filters, top_k=8)
        print(f"\n\n Results for {case['id']}: {res} \n\n")
        pred = [r["payload"]["filename"] for r in res]
        rec = recall_at_k(pred, case["expected_ids"], k=8)
        prec = precision_at_k(pred, case["expected_ids"], k=2)
        ndcg = ndcg_at_k(pred, case.get("graded_relevance", {}), k=8)
        mrr_score = mrr(pred, case["expected_ids"])
        results.append({
            "id": case["id"],
            "recall": rec,
            "precision": prec,
            "ndcg": ndcg,
            "mrr": mrr_score,
            "pred": pred,
            "expected": case["expected_ids"],
            "pass": rec >= EVAL_CONFIG["search"]["min_recall_at_k"]
        })
    return results
