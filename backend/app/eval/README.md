# Rabbit Hire Eval Framework - For AI Engineer Interviews

This eval pack covers all 5 pillars asked in modern AI Engineer JDs:

1. **Representative Datasets** -> `datasets/*.jsonl` versioned golden sets
2. **Automated Eval** -> `runners/test_*.py` + `metrics.py` + `ragas_eval.py`
3. **Human Eval** -> `human_eval.py` (LLM-as-judge) + feedback API + frontend EvalPage
4. **Regression Testing** -> `regression.py` + snapshot + GitHub Action gate
5. **Production Signals** -> `production_signals.py` + `EvalFeedback` table + self-expanding golden sets

### Quick Start (copy-paste)
