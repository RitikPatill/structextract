# StructExtract

> Status: active development — M1 scaffold complete, extraction engine coming in M2.

Turn unstructured documents (plain text, PDF, HTML, Markdown) into validated, schema-defined JSON — with every extracted field linked back to the exact span of source text that supports it.

## The problem

LLM extraction is now table-stakes in enterprise AI pipelines, but most demos skip two critical production concerns:

1. **Provenance** — where in the document does each value come from?
2. **Reliability** — how do I know the prompt isn't regressing between model updates?

StructExtract wraps these concerns into a single small, auditable library that any Python developer can drop into a pipeline.

## What works now (M1)

| Deliverable | Notes |
|-------------|-------|
| `structextract/` Python package | Installable via `pip install -e .`; exposes `__version__ = "0.1.0"` |
| `pyproject.toml` | Hatchling build backend; `requires-python = ">=3.10"` |
| `requirements.txt` | Pinned deps for all planned milestones (LLM clients, PDF/HTML parsing, FastAPI, Pydantic, pytest) |
| `tests/test_import.py` | Smoke test — verifies the package imports and `__version__` is a string |
| `LICENSE` | MIT |
| `.gitignore` | Standard Python ignores |

## Roadmap

| Feature | Status |
|---------|--------|
| Pydantic schema definitions | M2 |
| Claude (default) and OpenAI backend support | M2 |
| Source spans — char offsets + quoted text per field | M2 |
| Confidence scoring per extracted field | M2 |
| `.txt`, `.pdf`, `.html`, `.md` input support | M3 |
| FastAPI REST endpoint: `POST /extract` | M4 |
| CLI: `structextract run --schema invoice.py --doc scan.pdf` | M5 |
| Eval harness: JSONL test set → precision/recall report | M6 |

## Architecture (planned)

```
                  ┌─────────────┐
    document ────►│  Loader     │  txt / pdf / html / md → plain text
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
    schema  ─────►│  Extractor  │  Pydantic schema → prompt → LLM call
                  └──────┬──────┘
                         │  raw JSON + source spans
                  ┌──────▼──────┐
                  │  Validator  │  Pydantic parse + confidence tags
                  └──────┬──────┘
                         │
              ExtractionResult (fields + source_spans)
```

## Getting started (bootstrap)

```bash
# 1. Install build backend (one-time)
pip install hatchling

# 2. Install in editable mode
pip install -e .

# 3. Install runtime + dev deps
pip install -r requirements.txt

# 4. Verify the package imports
python -c "import structextract; print(structextract.__version__)"
# 0.1.0

# 5. Run tests
pytest tests/
```

## Planned usage (coming in M2+)

```python
# Define your schema
from pydantic import BaseModel, Field

class Invoice(BaseModel):
    vendor: str = Field(description="Name of the vendor or supplier")
    total: float = Field(description="Total amount due")
    due_date: str = Field(description="Payment due date (ISO 8601)")

# Extract (API not yet implemented)
# result = structextract.extract(schema=Invoice, document="invoice.pdf")
# print(result.fields)        # validated Invoice instance
# print(result.source_spans)  # {"vendor": {"text": "Acme Corp", "start": 42, "end": 51}}
```

## Requirements

- Python 3.10+
- An Anthropic API key (`ANTHROPIC_API_KEY`) or OpenAI API key (`OPENAI_API_KEY`)

## License

MIT — see [LICENSE](LICENSE).
