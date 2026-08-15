import json

import pytest
from pydantic import BaseModel

from structextract.extractor import (
    ExtractionError,
    _build_prompt,
    _resolve_span,
    extract,
)
from structextract.models import SourceSpan


class Invoice(BaseModel):
    total: float
    vendor: str


DOCUMENT = "Invoice from Acme Corp. Amount due: $99.50"


def test_build_prompt_contains_schema():
    prompt = _build_prompt(Invoice, "some text")
    assert "total" in prompt
    assert "vendor" in prompt
    assert "quote" in prompt


def test_resolve_span_found():
    span = _resolve_span("Acme Corp", "Invoice from Acme Corp dated...")
    assert span == SourceSpan(start=13, end=22, quote="Acme Corp")


def test_resolve_span_not_found():
    span = _resolve_span("Invented Text", "Invoice from Acme Corp")
    assert span is None


def _fake_llm_response(prompt, provider, model):
    return json.dumps({
        "total": {"value": 99.50, "quote": "$99.50", "confidence": "high"},
        "vendor": {"value": "Acme Corp", "quote": "Acme Corp", "confidence": "high"},
    })


def test_extract_happy_path(monkeypatch):
    monkeypatch.setattr("structextract.extractor._call_llm", _fake_llm_response)
    result = extract(Invoice, DOCUMENT)
    assert result.schema_name == "Invoice"
    assert result.fields["total"].value == 99.50
    assert result.fields["total"].source_span is not None
    assert result.fields["vendor"].source_span.start == 13


def test_extract_invalid_json_raises(monkeypatch):
    monkeypatch.setattr("structextract.extractor._call_llm", lambda *a, **kw: "not json")
    with pytest.raises(ExtractionError):
        extract(Invoice, DOCUMENT)
