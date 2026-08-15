from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from structextract import registry  # side-effect: registers built-in schemas
from structextract.extractor import extract
from structextract.models import ExtractionResult

app = FastAPI(title="StructExtract", description="Turn documents into structured JSON with source spans.")


class ExtractRequest(BaseModel):
    schema_name: str
    document: str
    provider: str = "anthropic"
    model: str | None = None


@app.get("/schemas")
def list_schemas() -> dict[str, list[str]]:
    return {"schemas": registry.list_schemas()}


@app.post("/extract")
def extract_endpoint(req: ExtractRequest) -> ExtractionResult:
    schema = registry.get(req.schema_name)
    if schema is None:
        raise HTTPException(status_code=404, detail=f"Schema '{req.schema_name}' not found. "
                            f"Available: {registry.list_schemas()}")
    return extract(schema, req.document, provider=req.provider, model=req.model)
