import json
import os
import pytest
from src.extractor import extract_and_score, extract_text_from_file

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "contracts")
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ground_truth.json")


def test_ground_truth_has_ten_fixtures():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        gt = json.load(f)
    assert len(gt) == 10
    for filename in gt:
        file_path = os.path.join(FIXTURES_DIR, filename)
        assert os.path.exists(file_path), f"Missing fixture file: {filename}"

def test_all_fixtures_extract_and_score():
    fixture_files = [
        "01_clean_standard_msa.txt",
        "02_missing_termination.txt",
        "03_ambiguous_payment_terms.txt",
        "04_contradictory_dates.txt",
        "05_ocr_typo_vendor.txt",
        "06_extreme_liability_cap.txt",
        "07_multi_page_spans.txt",
        "08_missing_governing_law.txt",
        "09_foreign_currency_msa.txt",
        "10_zero_dollar_nda.txt",
    ]
    for filename in fixture_files:
        file_path = os.path.join(FIXTURES_DIR, filename)
        text = extract_text_from_file(file_path)
        assert len(text) > 50, f"Empty text in {filename}"

        result = extract_and_score(text)
        assert result.overall_confidence >= 0.0, f"Invalid confidence in {filename}"
        assert result.triage_status in ["AUTO_APPROVED", "NEEDS_HUMAN_REVIEW"], f"Bad triage in {filename}"
        assert len(result.fields) == 7, f"Field count mismatch in {filename}"
