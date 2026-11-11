"""
RAGAS evaluation for Talent Chat - faithfulness, relevancy
This is what FAANG AI interviewers look for
"""
from __future__ import annotations
import json
import pathlib
from typing import List


def run_ragas_eval(sample_size=20):
    """
    Uses ragas metrics: faithfulness, answer_relevancy, context_precision
    Requires OPENAI_API_KEY set
    """
    try:
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        from ragas import evaluate
        from datasets import Dataset
    except ImportError as e:
        print(f"RAGAS not installed: {e}. Run pip install ragas datasets")
        return None

    golden_path = pathlib.Path(__file__).parent / \
        "datasets" / "chat_golden.json"
    if not golden_path.exists():
        print("No chat_golden found")
        return None

    # Build dataset for ragas
    questions = []
    contexts = []
    answers = []
    ground_truths = []

    from app.services.chat_service import execute_chat_turn

    with open(golden_path) as f:
        for i, line in enumerate(f):
            if i >= sample_size:
                break
            if not line.strip():
                continue
            case = json.loads(line)
            if case.get("expected_tool") == "none":
                continue

            res = execute_chat_turn(case["message"], case.get("history", []))
            # ragas needs list of context strings
            ctx = [c.get("text", "")[:500]
                   for c in res.get("candidates", [])] or ["No context"]
            questions.append(case["message"])
            contexts.append(ctx)
            answers.append(res.get("answer", ""))
            ground_truths.append(" ".join(case.get("expected_contains", [])))

    dataset = Dataset.from_dict({
        "question": questions,
        "contexts": contexts,
        "answer": answers,
        "ground_truth": ground_truths
    })

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision]
    )

    print(result)
    return result


if __name__ == "__main__":
    run_ragas_eval()
