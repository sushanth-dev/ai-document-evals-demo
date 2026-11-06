"""Contract text extraction and confidence scoring pipeline."""

import os
import re
from typing import Any
from src.schemas import (
    ContractExtraction,
    FieldScore,
    ScoredExtraction,
)
from src.scorer import score_field, compute_overall_confidence
from src.triage import evaluate_triage


def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from a text file or PDF document."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.lower().endswith(".pdf"):
        import pdfplumber

        text_pages: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
        return "\n\n".join(text_pages)

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_vendor(raw_text: str) -> tuple[str | None, str | None]:
    # Match patterns like: between Acme Corp ("Vendor")
    m = re.search(r'between\s+([A-Za-z0-9\s.,&]+?)\s*\([\"\'](?:Vendor|Party A)[\"\']\)', raw_text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        return name, name

    # Match: Vendor:\s*Name
    m2 = re.search(r'Vendor:\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m2:
        raw_val = m2.group(1).strip().rstrip(".")
        name = re.sub(r'\s*\([\"\']?(?:Vendor|Provider)[\"\']?\)\s*$', '', raw_val, flags=re.IGNORECASE).strip()
        return name, name

    # Match: Provider / Contractor
    m3 = re.search(r'(?:Provider|Contractor):\s*([^\n\r]+)', raw_text, re.IGNORECASE)
    if m3:
        raw_val = m3.group(1).strip().rstrip(".")
        name = re.sub(r'\s*\([\"\']?(?:Vendor|Provider|Contractor)[\"\']?\)\s*$', '', raw_val, flags=re.IGNORECASE).strip()
        return name, name

    return None, None


def _extract_effective_date(raw_text: str) -> tuple[str | None, str | None]:
    # Match: entered into on October 15, 2026
    m = re.search(r'(?:on|dated|Effective Date:?)\s*([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2})', raw_text, re.IGNORECASE)
    if m:
        span = m.group(1).strip()
        return span, span
    return None, None


def _extract_contract_value(raw_text: str) -> tuple[float | None, str | None]:
    # Match: total contract sum of $85,000 or Cost: $10,000 or compensation shall be $150,000
    m = re.search(r'(?:sum of|compensation shall be|value of|Cost:?)\s*(\$[\d,]+(?:\.\d{2})?)', raw_text, re.IGNORECASE)
    if m:
        span = m.group(1).strip()
        val = float(re.sub(r"[^\d.]", "", span))
        return val, span

    # Match zero dollar
    if re.search(r'zero\s*dollars?|\$0(?:\.00)?|no monetary compensation', raw_text, re.IGNORECASE):
        return 0.0, "$0"

    return None, None


def _extract_payment_terms(raw_text: str) -> tuple[int | None, str | None]:
    # Match: Net 30 or within thirty (30) days or within 30 days
    m = re.search(r'(?:within|payable within)\s+(?:[A-Za-z]+\s+)?\(?(\d{1,3})\)?\s*days', raw_text, re.IGNORECASE)
    if m:
        days = int(m.group(1))
        return days, m.group(0).strip()

    m_net = re.search(r'Net\s*(\d{1,3})', raw_text, re.IGNORECASE)
    if m_net:
        days = int(m_net.group(1))
        return days, m_net.group(0).strip()

    return None, None


def _extract_liability_cap(raw_text: str) -> tuple[float | None, str | None]:
    # Match: liability exceed $500,000 or limited to $250,000
    m = re.search(r'(?:liability.*?(?:exceed|limited to))\s*(\$[\d,]+(?:\.\d{2})?)', raw_text, re.IGNORECASE)
    if m:
        span = m.group(1).strip()
        val = float(re.sub(r"[^\d.]", "", span))
        return val, span
    return None, None


def _extract_governing_law(raw_text: str) -> tuple[str | None, str | None]:
    # Match: laws of (the State of )?California
    m = re.search(r'laws of (?:the State of )?([A-Za-z\s]+?)(?:\.|\n|$)', raw_text, re.IGNORECASE)
    if m:
        state = m.group(1).strip()
        return state, state
    return None, None


def _extract_termination_notice(raw_text: str) -> tuple[int | None, str | None]:
    # Match: upon forty-five (45) days or upon 60 days
    words_to_num = {
        "thirty": 30, "forty-five": 45, "forty five": 45,
        "sixty": 60, "ninety": 90,
    }
    m = re.search(r'upon\s+([A-Za-z-]+|\d+)(?:\s*\((?P<num>\d+)\))?\s*days', raw_text, re.IGNORECASE)
    if m:
        if m.group("num"):
            days = int(m.group("num"))
        else:
            token = m.group(1).lower()
            if token.isdigit():
                days = int(token)
            elif token in words_to_num:
                days = words_to_num[token]
            else:
                return None, None
        return days, m.group(0).strip()
    return None, None


def extract_and_score(document_text: str) -> ScoredExtraction:
    """
    Extract structured contract fields from document text and evaluate calibrated confidence scores.
    """
    vendor, vendor_span = _extract_vendor(document_text)
    eff_date, date_span = _extract_effective_date(document_text)
    val, val_span = _extract_contract_value(document_text)
    pay_terms, pay_span = _extract_payment_terms(document_text)
    liab_cap, liab_span = _extract_liability_cap(document_text)
    gov_law, law_span = _extract_governing_law(document_text)
    term_notice, term_span = _extract_termination_notice(document_text)

    field_scores: dict[str, FieldScore] = {
        "vendor_name": score_field(document_text, "vendor_name", vendor, vendor_span),
        "effective_date": score_field(document_text, "effective_date", eff_date, date_span),
        "contract_value_usd": score_field(document_text, "contract_value_usd", val, val_span),
        "payment_terms_days": score_field(document_text, "payment_terms_days", pay_terms, pay_span),
        "liability_cap_usd": score_field(document_text, "liability_cap_usd", liab_cap, liab_span),
        "governing_law": score_field(document_text, "governing_law", gov_law, law_span),
        "termination_notice_days": score_field(document_text, "termination_notice_days", term_notice, term_span),
    }

    overall_confidence = compute_overall_confidence(field_scores)
    triage_status, triage_reasons = evaluate_triage(field_scores, overall_confidence)

    return ScoredExtraction(
        fields=field_scores,
        overall_confidence=overall_confidence,
        triage_status=triage_status,
        triage_reasons=triage_reasons,
    )
