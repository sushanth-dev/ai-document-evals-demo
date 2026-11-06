import os
from evals.run_evals import run_evaluation

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "contracts")
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ground_truth.json")


def test_run_evaluation_metrics():
    summary = run_evaluation(FIXTURES_DIR, GROUND_TRUTH_PATH)
    assert summary["total_documents"] == 10
    assert summary["field_accuracy"] >= 80.0
    assert summary["triage_accuracy"] >= 90.0
    assert summary["elapsed_seconds"] < 2.0
    assert len(summary["details"]) == 10
