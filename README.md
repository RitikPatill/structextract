# StructExtract

> Status: active development — M4 FastAPI REST endpoint complete.

Turn unstructured documents (plain text, PDF, HTML, Markdown) into validated, schema-defined JSON — with every extracted field linked back to the exact span of source text that supports it.

## The problem

LLM extraction is now table-stakes in enterprise AI pipelines, but most demos skip two critical production concerns:

1. **Provenance** — where in the document does each value come from?
2. **Reliability** — how do I know the prompt isn't regressing between model updates?

StructExtract wraps these concerns into a single small, auditable library that any Python developer can drop into a pipeline.

## What works now (M4)

| Deliverable | Notes |
|-------------|-------|
| `structextract/` Python package | Installable via `pip install -e .`; exposes `__version__ = "0.1.0"` |
| `structextract/models.py` | `SourceSpan`, `FieldResult`, `ExtractionResult` Pydantic types |
| `structextract/extractor.py` | `extract()` — prompt builder, LLM caller, span resolver, JSON parser |
| `structextract/loader.py` | `load_document()` — loads `.txt`, `.pdf` (pdfplumber), `.html`/`.htm` (BeautifulSoup), `.md` (markdown-it-py + BeautifulSoup) → plain text |
| `structextract/registry.py` | In-process schema registry; built-in `Invoice` and `Contact` schemas |
| `structextract/api.py` | FastAPI app — `GET /schemas`, `POST /extract` |
| `structextract/cli.py` | `structextract run` + `structextract serve` CLI commands via Click |
| `ExtractionError` | Raised on unparseable LLM responses; subclass of `RuntimeError` |
| Anthropic + OpenAI backend | Switch via `provider="anthropic"` (default) or `provider="openai"` |
| Source spans | Each field carries `source_span` with `start`/`end` char offsets + verbatim `quote` |
| Confidence scoring | `"high"`, `"medium"`, or `"low"` per field |
| `tests/test_extractor.py` | 5 unit tests; monkeypatched — no real API key required |
| `tests/test_loader.py` | 7 unit tests for loader; no real API key or PDF required |
| `tests/test_api.py` | 3 unit tests for REST API; monkeypatched — no real API key required |
| `pyproject.toml` | Hatchling build backend; console script entry point |
| `requirements.txt` | Pinned deps for all planned milestones |
| `LICENSE` | MIT |

## Roadmap

| Feature | Status |
|---------|--------|
| Pydantic schema definitions | M2 ✓ |
| Claude (default) and OpenAI backend support | M2 ✓ |
| Source spans — char offsets + quoted text per field | M2 ✓ |
| Confidence scoring per extracted field | M2 ✓ |
| `.txt`, `.pdf`, `.html`, `.md` input support | M3 ✓ |
| CLI: `structextract run --schema invoice.py --doc scan.pdf` | M3 ✓ |
| FastAPI REST endpoint: `POST /extract` | M4 ✓ |
| Eval harness: JSONL test set → precision/recall report | M6 |

## Architecture

```
  HTTP client
      │
      │  POST /extract          GET /schemas
      ▼
  ┌───────────┐
  │  FastAPI  │  request validation, error handling          [M4]
  │  api.py   │
  └─────┬─────┘
        │  schema name + document text
        ▼
  ┌───────────┐
  │  Registry │  name → BaseModel class lookup               [M4]
  └─────┬─────┘
        │
        ├──────────────────────────────────────┐
        │                                      │
  ┌─────▼──────┐                     ┌─────────▼──────┐
  │   Loader   │  txt/pdf/html/md    │   Extractor    │  schema → prompt → LLM  [M2]
  │            │  → plain text [M3]  └────────┬───────┘
  └─────┬──────┘                              │  raw JSON + source spans
        └──────────────────────────┐          │
                                   ▼          ▼
                              ┌──────────────────┐
                              │    Validator     │  Pydantic parse + confidence  [M2]
                              └────────┬─────────┘
                                       │
                            ExtractionResult (fields + source_spans)
```

All components are implemented and tested (M2 – M4).

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

## CLI usage

After installing (`pip install -e .`), the `structextract` command is available:

```bash
structextract run --schema my_schema.py --doc invoice.pdf
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--schema` | required | Path to a `.py` file with exactly one `BaseModel` subclass |
| `--doc` | required | Path to the document (`.txt`, `.pdf`, `.html`, `.htm`, `.md`) |
| `--provider` | `anthropic` | LLM provider: `anthropic` or `openai` |
| `--model` | provider default | Override the model name |

Example schema file (`invoice_schema.py`):

```python
from pydantic import BaseModel, Field

class Invoice(BaseModel):
    vendor: str = Field(description="Name of the vendor")
    total: float = Field(description="Total amount due")
    due_date: str = Field(description="Payment due date")
```

```bash
structextract run --schema invoice_schema.py --doc invoice.pdf
# Outputs ExtractionResult JSON to stdout
```

## Python API usage

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

## REST API usage

Start the server:

```bash
structextract serve
# or with options:
structextract serve --host 0.0.0.0 --port 9000
```

### `GET /schemas`

Returns the list of registered schema names.

```bash
curl http://127.0.0.1:8000/schemas
# {"schemas":["Invoice","Contact"]}
```

### `POST /extract`

Body fields:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `schema_name` | `str` | yes | — | Name of a registered schema (e.g. `"Invoice"`) |
| `document` | `str` | yes | — | Plain-text document content |
| `provider` | `str` | no | `"anthropic"` | `"anthropic"` or `"openai"` |
| `model` | `str \| null` | no | `null` | Model name override |

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"schema_name": "Invoice", "document": "Invoice from Acme Corp. Total: $99.50. Due: 2024-02-01."}'
```

Response is an `ExtractionResult` JSON object with `schema_name` and `fields` (each field has `value`, `source_span`, and `confidence`).

## Requirements

- Python 3.10+
- An Anthropic API key (`ANTHROPIC_API_KEY`) or OpenAI API key (`OPENAI_API_KEY`)
- Document-parsing libs (installed automatically via `pip install -e .`): `pdfplumber`, `beautifulsoup4`, `markdown-it-py`

## License

MIT — see [LICENSE](LICENSE).
