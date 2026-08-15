# StructExtract

> Status: active development — M2 extraction engine complete.

Turn unstructured documents (plain text, PDF, HTML, Markdown) into validated, schema-defined JSON — with every extracted field linked back to the exact span of source text that supports it.

## The problem

LLM extraction is now table-stakes in enterprise AI pipelines, but most demos skip two critical production concerns:

1. **Provenance** — where in the document does each value come from?
2. **Reliability** — how do I know the prompt isn't regressing between model updates?

StructExtract wraps these concerns into a single small, auditable library that any Python developer can drop into a pipeline.

## What works now (M2)

| Deliverable | Notes |
|-------------|-------|
| `structextract/` Python package | Installable via `pip install -e .`; exposes `__version__ = "0.1.0"` |
| `structextract/models.py` | `SourceSpan`, `FieldResult`, `ExtractionResult` Pydantic types |
| `structextract/extractor.py` | `extract()` — prompt builder, LLM caller, span resolver, JSON parser |
| `ExtractionError` | Raised on unparseable LLM responses; subclass of `RuntimeError` |
| Anthropic + OpenAI backend | Switch via `provider="anthropic"` (default) or `provider="openai"` |
| Source spans | Each field carries `source_span` with `start`/`end` char offsets + verbatim `quote` |
| Confidence scoring | `"high"`, `"medium"`, or `"low"` per field |
| `tests/test_extractor.py` | 5 unit tests; monkeypatched — no real API key required |
| `pyproject.toml` | Hatchling build backend; `requires-python = ">=3.10"` |
| `requirements.txt` | Pinned deps for all planned milestones |
| `LICENSE` | MIT |

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

## Architecture

```
                  ┌─────────────┐
    document ────►│  Loader     │  txt / pdf / html / md → plain text   [M3]
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
    schema  ─────►│  Extractor  │  Pydantic schema → prompt → LLM call  [M2]
                  └──────┬──────┘
                         │  raw JSON + source spans
                  ┌──────▼──────┐
                  │  Validator  │  Pydantic parse + confidence tags      [M2]
                  └──────┬──────┘
                         │
              ExtractionResult (fields + source_spans)
```

Components labelled `[M2]` are implemented and tested. `[M3]` is planned.

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

## Usage

```python
import os
from pydantic import BaseModel, Field
import structextract

# 1. Define your schema
class Invoice(BaseModel):
    vendor: str = Field(description="Name of the vendor or supplier")
    total: float = Field(description="Total amount due")
    due_date: str = Field(description="Payment due date (ISO 8601)")

# 2. Extract
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."   # or set in environment
result = structextract.extract(schema=Invoice, document="Invoice from Acme Corp. Amount due: $99.50. Due: 2024-02-01.")

# 3. Inspect
for name, field in result.fields.items():
    print(f"{name}: {field.value!r}  [{field.confidence}]")
    if field.source_span:
        print(f"  ↳ chars {field.source_span.start}–{field.source_span.end}: {field.source_span.quote!r}")
```

If the LLM returns malformed JSON, `extract()` raises `structextract.extractor.ExtractionError` (a `RuntimeError` subclass).

To use OpenAI instead:

```python
result = structextract.extract(schema=Invoice, document=text, provider="openai")
```

## Requirements

- Python 3.10+
- An Anthropic API key (`ANTHROPIC_API_KEY`) or OpenAI API key (`OPENAI_API_KEY`)

## License

MIT — see [LICENSE](LICENSE).
