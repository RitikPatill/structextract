from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel

from structextract.models import ExtractionResult, FieldResult, SourceSpan


class ExtractionError(RuntimeError):
    pass


_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
}


def _build_prompt(schema: type[BaseModel], document: str) -> str:
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    field_names = list(schema.model_fields.keys())
    fields_example = ", ".join(
        f'"{f}": {{"value": ..., "quote": "<verbatim substring>", "confidence": "high"|"medium"|"low"}}'
        for f in field_names
    )
    return f"""You are a structured data extraction assistant.

Extract the following fields from the document below according to the JSON schema provided.

## Schema
```json
{schema_json}
```

## Instructions
Return a single JSON object where every key from the schema maps to an object with:
- "value": the extracted value matching the field type
- "quote": the EXACT verbatim substring from the document that supports this value (copy-paste, no paraphrasing)
- "confidence": one of "high", "medium", or "low"

If a field cannot be found, set "value" to null, "quote" to "", and "confidence" to "low".

Do NOT invent text. The "quote" field MUST be a verbatim substring of the document.

## Expected output format
{{
  {fields_example}
}}

Return ONLY valid JSON — no markdown, no explanation.

## Document
{document}"""


def _call_llm(prompt: str, provider: str, model: str) -> str:
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    elif provider == "openai":
        import openai
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Use 'anthropic' or 'openai'.")


def _resolve_span(quote: str, document: str) -> SourceSpan | None:
    if not quote:
        return None
    idx = document.find(quote)
    if idx < 0:
        return None
    return SourceSpan(start=idx, end=idx + len(quote), quote=quote)


def extract(
    schema: type[BaseModel],
    document: str,
    provider: str = "anthropic",
    model: str | None = None,
) -> ExtractionResult:
    if model is None:
        model = _DEFAULT_MODELS.get(provider, "claude-sonnet-4-6")

    prompt = _build_prompt(schema, document)
    raw = _call_llm(prompt, provider, model)

    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

    try:
        parsed: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"LLM returned invalid JSON: {exc}\n\nRaw response:\n{raw}") from exc

    fields: dict[str, FieldResult] = {}
    for field_name in schema.model_fields:
        entry = parsed.get(field_name, {})
        if not isinstance(entry, dict):
            entry = {"value": entry, "quote": "", "confidence": "low"}

        value = entry.get("value")
        quote = entry.get("quote", "")
        confidence = entry.get("confidence", "low")
        if confidence not in ("high", "medium", "low"):
            confidence = "low"

        span = _resolve_span(quote, document) if quote else None
        fields[field_name] = FieldResult(value=value, source_span=span, confidence=confidence)

    return ExtractionResult(schema_name=schema.__name__, fields=fields)
