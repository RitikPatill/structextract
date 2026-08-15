from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from structextract.eval import (
    EvalReport,
    FieldMetrics,
    _match,
    print_report,
    run_eval,
)
from structextract.extractor import ExtractionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_response(field_values: dict[str, str | None]) -> str:
    """Build the JSON string that _call_llm would return for the given field values."""
    payload = {}
    for fname, val in field_values.items():
        payload[fname] = {
            "value": val,
            "quote": val if val else "",
            "confidence": "high" if val else "low",
        }
    return json.dumps(payload)


def _write_jsonl(tmp_path: Path, lines: list[dict]) -> Path:
    p = tmp_path / "samples.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_match_is_case_insensitive():
    assert _match("Acme Corp", "acme corp") is True
    assert _match("  HELLO  ", "hello") is True
    assert _match(None, "anything") is False
    assert _match("foo", "bar") is False


def test_run_eval_perfect_score(tmp_path, monkeypatch):
    """All 3 examples return exact expected values → all metrics = 1.0."""
    examples = [
        {
            "doc": "INVOICE #INV-001\nVendor: Acme Corp\nTotal: $100.00\nDue: 2024-01-31",
            "expected": {
                "vendor_name": "Acme Corp",
                "invoice_number": "INV-001",
                "total_amount": "$100.00",
                "due_date": "2024-01-31",
            },
        },
        {
            "doc": "INVOICE #INV-002\nVendor: Beta LLC\nTotal: $200.00\nDue: 2024-02-28",
            "expected": {
                "vendor_name": "Beta LLC",
                "invoice_number": "INV-002",
                "total_amount": "$200.00",
                "due_date": "2024-02-28",
            },
        },
        {
            "doc": "INVOICE #INV-003\nVendor: Gamma Inc\nTotal: $300.00\nDue: 2024-03-31",
            "expected": {
                "vendor_name": "Gamma Inc",
                "invoice_number": "INV-003",
                "total_amount": "$300.00",
                "due_date": "2024-03-31",
            },
        },
    ]
    dataset = _write_jsonl(tmp_path, examples)

    # Mock _call_llm to return perfect answers
    responses = [
        _make_llm_response({"vendor_name": "Acme Corp", "invoice_number": "INV-001", "total_amount": "$100.00", "due_date": "2024-01-31"}),
        _make_llm_response({"vendor_name": "Beta LLC", "invoice_number": "INV-002", "total_amount": "$200.00", "due_date": "2024-02-28"}),
        _make_llm_response({"vendor_name": "Gamma Inc", "invoice_number": "INV-003", "total_amount": "$300.00", "due_date": "2024-03-31"}),
    ]
    call_count = {"n": 0}

    def fake_call_llm(prompt: str, provider: str, model: str) -> str:
        idx = call_count["n"]
        call_count["n"] += 1
        return responses[idx]

    monkeypatch.setattr("structextract.extractor._call_llm", fake_call_llm)

    report = run_eval(dataset, "Invoice")

    assert report.n_examples == 3
    assert report.micro_f1 == pytest.approx(1.0)
    for fname in ("vendor_name", "invoice_number", "total_amount", "due_date"):
        m = report.fields[fname]
        assert m.precision == pytest.approx(1.0), fname
        assert m.recall == pytest.approx(1.0), fname
        assert m.f1 == pytest.approx(1.0), fname
        assert m.support == 3


def test_run_eval_partial_match(tmp_path, monkeypatch):
    """2 of 3 examples correct for vendor_name → recall ≈ 0.667, precision = 1.0."""
    examples = [
        {
            "doc": "Vendor: Acme Corp\nInvoice #: A1\nTotal: $10.00\nDue: 2024-01-01",
            "expected": {"vendor_name": "Acme Corp"},
        },
        {
            "doc": "Vendor: Beta LLC\nInvoice #: B2\nTotal: $20.00\nDue: 2024-02-01",
            "expected": {"vendor_name": "Beta LLC"},
        },
        {
            "doc": "Vendor: Gamma Inc\nInvoice #: C3\nTotal: $30.00\nDue: 2024-03-01",
            "expected": {"vendor_name": "Gamma Inc"},
        },
    ]
    dataset = _write_jsonl(tmp_path, examples)

    # Third example returns wrong vendor_name
    responses = [
        _make_llm_response({"vendor_name": "Acme Corp", "invoice_number": "A1", "total_amount": "$10.00", "due_date": "2024-01-01"}),
        _make_llm_response({"vendor_name": "Beta LLC", "invoice_number": "B2", "total_amount": "$20.00", "due_date": "2024-02-01"}),
        _make_llm_response({"vendor_name": "WRONG", "invoice_number": "C3", "total_amount": "$30.00", "due_date": "2024-03-01"}),
    ]
    call_count = {"n": 0}

    def fake_call_llm(prompt: str, provider: str, model: str) -> str:
        idx = call_count["n"]
        call_count["n"] += 1
        return responses[idx]

    monkeypatch.setattr("structextract.extractor._call_llm", fake_call_llm)

    report = run_eval(dataset, "Invoice")

    vendor = report.fields["vendor_name"]
    # 2 TP, 0 FP (wrong value goes to FN), 1 FN → precision=1.0, recall=2/3
    assert vendor.precision == pytest.approx(1.0)
    assert vendor.recall == pytest.approx(2 / 3, rel=1e-3)
    assert vendor.support == 3


def test_run_eval_extraction_error_counts_as_fn(tmp_path, monkeypatch):
    """ExtractionError causes example to count as all-FN; report returns without raising."""
    examples = [
        {
            "doc": "Vendor: Acme Corp\nTotal: $50.00",
            "expected": {"vendor_name": "Acme Corp", "total_amount": "$50.00"},
        },
    ]
    dataset = _write_jsonl(tmp_path, examples)

    def fake_call_llm(prompt: str, provider: str, model: str) -> str:
        raise ExtractionError("LLM returned invalid JSON")

    monkeypatch.setattr("structextract.extractor._call_llm", fake_call_llm)

    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        report = run_eval(dataset, "Invoice")
        assert len(w) == 1
        assert "ExtractionError" in str(w[0].message)

    assert report.n_examples == 1
    # All expected fields are FN → recall = 0
    for fname in ("vendor_name", "total_amount"):
        m = report.fields[fname]
        assert m.recall == pytest.approx(0.0)
    assert report.micro_f1 == pytest.approx(0.0)


def test_print_report_runs_without_error():
    """Smoke test: print_report does not raise on a synthetic EvalReport."""
    report = EvalReport(
        schema_name="Invoice",
        n_examples=5,
        fields={
            "vendor_name": FieldMetrics(precision=1.0, recall=0.8, f1=0.889, support=5),
            "total_amount": FieldMetrics(precision=0.9, recall=1.0, f1=0.947, support=5),
        },
        micro_f1=0.92,
    )
    # Should not raise
    print_report(report)
