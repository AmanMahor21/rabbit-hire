from __future__ import annotations
import math
from typing import List, Dict
from collections import Counter

def precision_at_k(predicted: List[str], expected: List[str], k=8) -> float:
    if k == 0: return 0.0
    return len(set(predicted[:k]) & set(expected)) / k

def recall_at_k(predicted: List[str], expected: List[str], k=8) -> float:
    if not expected: return 1.0 if not predicted else 0.0
    return len(set(predicted[:k]) & set(expected)) / len(expected)

def mrr(predicted: List[str], expected: List[str]) -> float:
    for i, doc in enumerate(predicted):
        if doc in expected:
            return 1.0 / (i+1)
    return 0.0

def ndcg_at_k(predicted: List[str], graded: Dict[str, int], k=8) -> float:
    if not graded: return 0.0
    dcg = 0.0
    for i, doc in enumerate(predicted[:k]):
        rel = graded.get(doc, 0)
        dcg += rel / math.log2(i+2)
    ideal = sorted(graded.values(), reverse=True)[:k]
    idcg = sum(s / math.log2(i+2) for i, s in enumerate(ideal))
    return dcg / idcg if idcg else 0.0

def skill_f1(pred_skills: List[str], true_skills: List[str]) -> float:
    p = set(s.strip().upper() for s in pred_skills if s.strip())
    t = set(s.strip().upper() for s in true_skills if s.strip())
    if not p and not t: return 1.0
    if not p or not t: return 0.0
    tp = len(p & t)
    prec = tp / len(p)
    rec = tp / len(t)
    return 2*prec*rec/(prec+rec) if prec+rec else 0.0

def spearman_rank_correlation(pred_rank: List[str], ideal_rank: List[str]) -> float:
    try:
        from scipy.stats import spearmanr
        # Map to positions
        pred_pos = {doc: i for i, doc in enumerate(pred_rank)}
        ideal_pos = {doc: i for i, doc in enumerate(ideal_rank)}
        common = list(set(pred_rank) & set(ideal_rank))
        if len(common) < 2: return 0.0
        x = [pred_pos[d] for d in common]
        y = [ideal_pos[d] for d in common]
        corr, _ = spearmanr(x, y)
        return float(corr) if not math.isnan(corr) else 0.0
    except Exception:
        return 0.0

def top1_accuracy(pred_rank: List[str], ideal_rank: List[str]) -> float:
    if not ideal_rank or not pred_rank: return 0.0
    return 1.0 if pred_rank[0] == ideal_rank[0] else 0.0
