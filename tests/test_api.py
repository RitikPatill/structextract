from __future__ import annotations

from fastapi.testclient import TestClient

from structextract.api import app
from structextract.models import ExtractionResult, FieldResult, SourceSpan

client = TestClient(app)


def test_list_schemas_includes_builtins():
    r = client.get("/schemas")
    assert r.status_code == 200
    names = r.json()["schemas"]
    assert "Invoice" in names
    assert "Contact" in names


def test_extract_unknown_schema_returns_404():
    r = client.post("/extract", json={"schema_name": "NoSuchSchema", "document": "hello"})
    assert r.status_code == 404


def test_extract_returns_result(monkeypatch):
    fake_result = ExtractionResult(
        schema_name="Invoice",
        fields={
            "vendor_name": FieldResult(
                value="Acme Corp",
                source_span=SourceSpan(start=0, end=9, quote="Acme Corp"),
                confidence="high",
            )
        },
    )
    monkeypatch.setattr("structextract.api.extract", lambda *a, **kw: fake_result)
    r = client.post("/extract", json={"schema_name": "Invoice", "document": "Acme Corp invoice"})
    assert r.status_code == 200
    body = r.json()
    assert body["schema_name"] == "Invoice"
    assert "vendor_name" in body["fields"]
