# StructExtract — LLM Structured Extraction with Source Grounding & Evals


> **Video walkthrough:** https://youtu.be/K8UPkchNYeo
> **60-second overview:** https://youtu.be/_RUqJlXaGvA

> Extract typed, schema-defined data from any document with LLMs, source citations, and a built-in eval harness.

<!-- TODO: replace with a 5-10 second demo gif. Record with ScreenToGif on
     Windows or peek on macOS. Save to docs/demo.gif and update path here. -->
![demo](docs/demo.gif)

## What it is

StructExtract turns unstructured documents — plain text, PDF, HTML, Markdown — into validated, schema-defined JSON using an LLM backend. Every extracted field carries a `source_span` (character offsets and a verbatim quote) so you can trace exactly where in the source document each value came from. It also ships a `confidence` rating per field and a built-in eval harness that runs a JSONL test set through the extractor and returns field-level precision, recall, and F1.

Two production concerns that most extraction demos skip motivated the project: *provenance* (which part of the document supports this value?) and *reliability* (is extraction getting worse between model updates?). StructExtract wraps both into a single small, auditable library. You define schemas with ordinary Pydantic models, run extraction with a one-line call or the CLI, and track accuracy with the eval command.

## Quickstart

```bash
git clone https://github.com/RitikPatill/structextract.git
cd structextract

# Install the package and all dependencies
pip install -e .

# Confirm the package version
python -c "import structextract; print(structextract.__version__)"
# 0.1.0

# Run the test suite (no API key required — all LLM calls are monkeypatched)
pip install pytest
pytest tests/

# Set your LLM provider key, then extract from a document
export ANTHROPIC_API_KEY=sk-ant-...
structextract run --schema <schema_file.py> --doc <document.pdf>
```

## Usage

**CLI — extract fields from a document:**

```bash
structextract run --schema invoice_schema.py --doc scan.pdf
```

`--schema` points to a `.py` file containing exactly one `BaseModel` subclass. `--doc` accepts `.txt`, `.pdf`, `.html`, `.htm`, or `.md`. Add `--provider openai` and `export OPENAI_API_KEY=...` to switch backends.

**CLI — run an eval against a JSONL dataset:**

```bash
structextract eval --schema Invoice --dataset evals/invoice_samples.jsonl
```

This prints a Rich table with per-field precision, recall, F1, and an overall micro-averaged score. Each row in the JSONL file needs a `"doc"` string and an `"expected"` object with field-value pairs.

**CLI — start the REST server:**

```bash
structextract serve
```

**REST API — extract via HTTP:**

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"schema_name": "Invoice", "document": "Invoice from Acme Corp. Total: $99.50. Due: 2024-02-01."}'
```

`GET /schemas` returns the list of registered schema names (`Invoice`, `Contact`, `job_posting` are built in).

**Python API — embed in a pipeline:**

```python
from pydantic import BaseModel, Field
import structextract

class Invoice(BaseModel):
    vendor: str = Field(description="Name of the vendor or supplier")
    total: float = Field(description="Total amount due")
    due_date: str = Field(description="Payment due date (ISO 8601)")

result = structextract.extract(schema=Invoice, document=open("invoice.txt").read())
for name, field in result.fields.items():
    print(f"{name}: {field.value!r}  [{field.confidence}]")
    if field.source_span:
        print(f"  chars {field.source_span.start}–{field.source_span.end}: {field.source_span.quote!r}")
```

## Architecture

```
  CLI / HTTP client
        │
        ▼
  ┌───────────┐     ┌──────────┐
  │  FastAPI  │────▶│ Registry │  schema name → BaseModel class
  │  api.py   │     └────┬─────┘
  └───────────┘          │
        │                ▼
        │         ┌────────────┐     ┌─────────────────────────┐
        │         │   Loader   │────▶│       Extractor         │
        │         │  loader.py │     │  prompt → LLM → JSON    │
        │         └────────────┘     │  → span resolver        │
        │                            └───────────┬─────────────┘
        │                                        │
        │                            ExtractionResult
        │                        (fields + source_spans + confidence)
        │
  ┌─────▼──────┐
  │    Eval    │  JSONL test set → precision / recall / F1
  │   eval.py  │
  └────────────┘
```

## Project structure

```
structextract/          Python package
  models.py             SourceSpan, FieldResult, ExtractionResult types
  extractor.py          extract() — prompt builder, LLM caller, span resolver
  loader.py             load_document() — txt / pdf / html / md → plain text
  registry.py           In-process schema registry + built-in schemas
  api.py                FastAPI app (GET /schemas, POST /extract)
  cli.py                Click CLI (run, serve, eval subcommands)
  eval.py               run_eval(), print_report() — Rich table output
tests/                  Unit tests (monkeypatched; no API key required)
evals/                  JSONL eval sets for Invoice and job_posting schemas
scripts/                make_demo.py — generates demo SVG without an API key
pyproject.toml          Hatchling build config + console script entry point
requirements.txt        Pinned runtime and dev dependencies
```

## Roadmap

- [ ] Streaming extraction — yield fields as the LLM produces them rather than waiting for a full response
- [ ] Nested schema support — allow `BaseModel` fields that are themselves models
- [ ] PDF bounding-box spans — map `source_span` offsets back to page/line coordinates in PDF inputs
- [ ] Schema registry persistence — register schemas from YAML or a config file without writing Python
- [ ] OpenTelemetry tracing — emit spans for each extraction call to integrate with existing observability stacks

## License

MIT — see LICENSE.

---

Built autonomously by [autodev](https://github.com/RitikPatill/autodev),
a multi-agent orchestrator I designed. Each commit in this repo was
authored by me; the implementation work was performed by Sonnet under
the orchestrator's control. Read the orchestrator's README to see how.
