"""
Regression Testing - Snapshot comparison + CI gate
This is what prevents silent quality drops in production
"""
from __future__ import annotations
import json, pathlib, datetime
from typing import Dict
from app.eval.config import EVAL_CONFIG

SNAPSHOT_DIR = pathlib.Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)
LATEST_SNAPSHOT = SNAPSHOT_DIR / "latest.json"
LAST_GOOD = SNAPSHOT_DIR / "last_good.json"

def save_snapshot(results: Dict, name="latest"):
    path = SNAPSHOT_DIR / f"{name}.json"
    payload = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "results": results
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Snapshot saved: {path}")
    return path

def compare_with_last_good(current_results: Dict) -> Dict:
    if not LAST_GOOD.exists():
        print("No last_good snapshot - saving current as baseline")
        save_snapshot(current_results, "last_good")
        return {"drift": False, "message": "Baseline created"}
    
    with open(LAST_GOOD) as f:
        baseline = json.load(f)["results"]
    
    # Compare average recall
    curr_recall = sum(r.get("recall",0) for r in current_results.get("search", [])) / max(1, len(current_results.get("search", [])))
    base_recall = sum(r.get("recall",0) for r in baseline.get("search", [])) / max(1, len(baseline.get("search", [])))
    
    drift = base_recall - curr_recall
    threshold = EVAL_CONFIG["search"]["drift_threshold"]
    
    if drift > threshold:
        return {
            "drift": True,
            "message": f"REGRESSION: recall dropped {drift:.3f} (baseline {base_recall:.3f} -> current {curr_recall:.3f}) > threshold {threshold}",
            "baseline_recall": base_recall,
            "current_recall": curr_recall,
            "drift_value": drift
        }
    else:
        return {
            "drift": False,
            "message": f"OK: recall {curr_recall:.3f} vs baseline {base_recall:.3f} (drift {drift:.3f})",
            "baseline_recall": base_recall,
            "current_recall": curr_recall
        }

def run_regression_gate():
    """Main entry for CI"""
    from app.eval.runners.test_search import run_search_eval_detailed
    
    print("Running regression eval...")
    search_results = run_search_eval_detailed()
    
    current = {"search": search_results}
    save_snapshot(current, "latest")
    
    comparison = compare_with_last_good(current)
    print(f"\n{comparison['message']}")
    
    if comparison["drift"]:
        print("❌ REGRESSION GATE FAILED")
        # In CI, exit 1
        return False
    else:
        print("✅ REGRESSION GATE PASSED")
        return True

if __name__ == "__main__":
    import sys
    ok = run_regression_gate()
    sys.exit(0 if ok else 1)
