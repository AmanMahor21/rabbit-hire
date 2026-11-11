# backend/app/eval/run_all.py
"""
One-click eval runner - generates HTML report
Usage: python -m app.eval.run_all --html
This is what you show in interviews
"""
from __future__ import annotations
import json
import pathlib
import datetime
import argparse
from app.eval.runners.test_search import run_search_eval_detailed


def run_all(html=False):
    print("🚀 Running full eval suite...")

    search_results = run_search_eval_detailed()

    avg_recall = sum(r["recall"] for r in search_results) / \
        len(search_results) if search_results else 0
    avg_prec = sum(r["precision"] for r in search_results) / \
        len(search_results) if search_results else 0
    avg_ndcg = sum(r["ndcg"] for r in search_results) / \
        len(search_results) if search_results else 0
    pass_rate = sum(
        1 for r in search_results if r["pass"]) / len(search_results) if search_results else 0

    report = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "search": {
            "total": len(search_results),
            "avg_recall": avg_recall,
            "avg_precision": avg_prec,
            "avg_ndcg": avg_ndcg,
            "pass_rate": pass_rate,
            "details": search_results,
        },
    }

    out_path = pathlib.Path(
        __file__).parent / f"report_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    # ✅ FIX: always write UTF-8 so non-ASCII (skill names, emoji) never crashes on Windows
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n=== EVAL REPORT ===")
    print(f"Search: {len(search_results)} cases | Recall@{8}: {avg_recall:.3f} | Prec: {avg_prec:.3f} | NDCG: {avg_ndcg:.3f} | Pass: {pass_rate:.1%}")
    print(f"Report saved: {out_path}")

    if html:
        html_path = out_path.with_suffix(".html")
        html_content = f"""
        <html><head><meta charset="utf-8"><title>Rabbit Hire Eval Report</title>
        <style>body{{font-family: monospace; background:#080d1a; color:#e2e8f0; padding:20px}} .pass{{color:#10b981}} .fail{{color:#ef4444}} table{{border-collapse:collapse; width:100%}} th,td{{border:1px solid #1e2a45; padding:8px; text-align:left}} th{{background:#0e172a}}</style>
        </head><body>
        <h1>🐰 Rabbit Hire Eval Report - {report['timestamp']}</h1>
        <h2>Search - {len(search_results)} cases</h2>
        <p>Avg Recall: {avg_recall:.3f} | Avg Precision: {avg_prec:.3f} | NDCG: {avg_ndcg:.3f} | Pass Rate: {pass_rate:.1%}</p>
        <table><tr><th>ID</th><th>Recall</th><th>NDCG</th><th>Pred</th><th>Expected</th><th>Status</th></tr>
        """
        for r in search_results:
            status = "<span class='pass'>PASS</span>" if r["pass"] else "<span class='fail'>FAIL</span>"
            html_content += f"<tr><td>{r['id']}</td><td>{r['recall']:.2f}</td><td>{r['ndcg']:.2f}</td><td>{','.join(r['pred'][:2])}</td><td>{','.join(r['expected'][:2])}</td><td>{status}</td></tr>"
        html_content += "</table></body></html>"
        # ✅ FIX: UTF-8 output so the 🐰 emoji (and any other Unicode) encodes correctly
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML report: {html_path}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", action="store_true")
    args = parser.parse_args()
    run_all(html=args.html)
