"""CLI evaluation harness and benchmark reporter for contract extraction."""

import json
import os
import sys
import time
from typing import Any
from rich.console import Console
from rich.table import Table

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.extractor import extract_and_score, extract_text_from_file


def run_evaluation(fixtures_dir: str, ground_truth_path: str) -> dict[str, Any]:
    """Execute evaluation across all fixtures and compute accuracy metrics."""
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth: dict[str, Any] = json.load(f)

    start_time = time.perf_counter()

    total_fields = 0
    correct_fields = 0
    triage_correct = 0
    details: list[dict[str, Any]] = []

    for filename, expected in ground_truth.items():
        file_path = os.path.join(fixtures_dir, filename)
        text = extract_text_from_file(file_path)
        result = extract_and_score(text)

        expected_fields = expected["expected_fields"]
        expected_triage = expected["expected_triage_status"]

        doc_field_matches = 0
        doc_field_total = len(expected_fields)

        for field_name, expected_val in expected_fields.items():
            actual_score = result.fields.get(field_name)
            actual_val = actual_score.value if actual_score else None

            # Compare equality with numeric/string tolerance
            match = False
            if expected_val is None and actual_val is None:
                match = True
            elif expected_val is not None and actual_val is not None:
                if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                    match = abs(float(expected_val) - float(actual_val)) < 0.01
                else:
                    match = str(expected_val).strip().lower() == str(actual_val).strip().lower()

            if match:
                doc_field_matches += 1
                correct_fields += 1
            total_fields += 1

        is_triage_match = (result.triage_status.value == expected_triage)
        if is_triage_match:
            triage_correct += 1

        details.append({
            "filename": filename,
            "overall_confidence": result.overall_confidence,
            "triage_status": result.triage_status.value,
            "expected_triage": expected_triage,
            "triage_match": is_triage_match,
            "field_accuracy": round((doc_field_matches / doc_field_total) * 100, 1),
            "reasons": result.triage_reasons,
        })

    elapsed = round(time.perf_counter() - start_time, 4)

    field_acc = round((correct_fields / total_fields) * 100, 2) if total_fields else 0.0
    triage_acc = round((triage_correct / len(ground_truth)) * 100, 2) if ground_truth else 0.0

    return {
        "total_documents": len(ground_truth),
        "total_fields": total_fields,
        "correct_fields": correct_fields,
        "field_accuracy": field_acc,
        "triage_correct": triage_correct,
        "triage_accuracy": triage_acc,
        "elapsed_seconds": elapsed,
        "details": details,
    }


def print_report(summary: dict[str, Any], export_svg_path: str | None = None) -> None:
    """Print formatted terminal report using rich tables and optionally export SVG."""
    console = Console(record=bool(export_svg_path), width=110)
    table = Table(title="Contract Extraction Benchmark Results", header_style="bold magenta")
    table.add_column("Fixture Document", style="cyan", width=32)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Triage Status", justify="center", width=22)
    table.add_column("Expected", justify="center", width=22)
    table.add_column("Field Acc", justify="right", width=10)
    table.add_column("Match", justify="center", width=8)

    for row in summary["details"]:
        match_symbol = "[green]PASS[/green]" if row["triage_match"] else "[red]FAIL[/red]"
        conf_str = f"{row['overall_confidence']:.3f}"
        acc_str = f"{row['field_accuracy']}%"

        status_str = f"[green]{row['triage_status']}[/green]" if row['triage_status'] == "AUTO_APPROVED" else f"[yellow]{row['triage_status']}[/yellow]"
        exp_str = f"[green]{row['expected_triage']}[/green]" if row['expected_triage'] == "AUTO_APPROVED" else f"[yellow]{row['expected_triage']}[/yellow]"

        table.add_row(
            row["filename"],
            conf_str,
            status_str,
            exp_str,
            acc_str,
            match_symbol,
        )

    console.print()
    console.print(table)
    console.print()

    summary_table = Table(title="Benchmark Metrics Summary", header_style="bold green")
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Score", justify="right")

    summary_table.add_row("Total Test Fixtures", str(summary["total_documents"]))
    summary_table.add_row("Total Fields Evaluated", str(summary["total_fields"]))
    summary_table.add_row("Field-Level Accuracy", f"{summary['field_accuracy']}%")
    summary_table.add_row("Triage Gate Accuracy", f"{summary['triage_accuracy']}%")
    summary_table.add_row("Execution Latency", f"{summary['elapsed_seconds'] * 1000:.1f} ms")

    console.print(summary_table)
    console.print()

    if export_svg_path:
        os.makedirs(os.path.dirname(os.path.abspath(export_svg_path)), exist_ok=True)
        console.save_svg(export_svg_path, title="ai-document-evals-demo benchmark")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    fixtures = os.path.join(base_dir, "..", "fixtures", "contracts")
    truth = os.path.join(base_dir, "..", "fixtures", "ground_truth.json")

    results = run_evaluation(fixtures, truth)
    svg_path = os.path.join(base_dir, "..", "assets", "benchmark.svg")
    print_report(results, export_svg_path=svg_path)
