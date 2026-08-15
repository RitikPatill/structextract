from __future__ import annotations

import importlib.util
import sys

import click
from pydantic import BaseModel

from structextract.extractor import extract
from structextract.loader import load_document


@click.group()
def cli():
    """StructExtract — turn documents into structured JSON."""


@cli.command("run")
@click.option("--schema", "schema_path", required=True, type=click.Path(exists=True), help="Path to a Python file defining a Pydantic schema class.")
@click.option("--doc", "doc_path", required=True, type=click.Path(exists=True), help="Path to the document (.txt, .pdf, .html, .md).")
@click.option("--provider", default="anthropic", show_default=True, help="LLM provider: 'anthropic' or 'openai'.")
@click.option("--model", default=None, help="Model name override (uses provider default if omitted).")
def run_cmd(schema_path: str, doc_path: str, provider: str, model: str | None) -> None:
    """Extract structured data from a document using a Pydantic schema."""
    # Dynamically load schema module
    spec = importlib.util.spec_from_file_location("_schema", schema_path)
    if spec is None or spec.loader is None:
        raise click.UsageError(f"Cannot load schema file: {schema_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find BaseModel subclasses defined in the module
    schema_classes = [
        obj
        for obj in vars(module).values()
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
    ]

    if len(schema_classes) == 0:
        raise click.UsageError(f"No Pydantic BaseModel subclass found in {schema_path}")
    if len(schema_classes) > 1:
        names = ", ".join(c.__name__ for c in schema_classes)
        raise click.UsageError(
            f"Multiple BaseModel subclasses found in {schema_path}: {names}. "
            "Please define exactly one schema class per file."
        )

    schema_class = schema_classes[0]

    text = load_document(doc_path)
    result = extract(schema_class, text, provider=provider, model=model)
    click.echo(result.model_dump_json(indent=2))
