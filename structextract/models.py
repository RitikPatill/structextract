from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class SourceSpan(BaseModel):
    start: int
    end: int
    quote: str


class FieldResult(BaseModel):
    value: Any
    source_span: SourceSpan | None
    confidence: Literal["high", "medium", "low"]


class ExtractionResult(BaseModel):
    schema_name: str
    fields: dict[str, FieldResult]
