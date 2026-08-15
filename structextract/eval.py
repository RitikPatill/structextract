from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from structextract import registry
from structextract.extractor import ExtractionError, extract


@dataclass
class FieldMetrics:
    precision: float
    recall: float
    f1: float
    support: int  # number of examples where field appears in expected


@dataclass
class EvalReport:
    schema_name: str
    n_examples: int
    fields: dict[str, FieldMetrics]
    micro_f1: float


def _match(extracted_value: str | None, expected_value: str) -> bool:
    """Case-insensitive exact match after stripping whitespace."""
    if extracted_value is None:
        return False
    return str(extracted_value).strip().lower() == expected_value.strip().lower()


def _compute_metrics(
    per_field_counts: dict[str, dict[str, int]],
) -> dict[str, FieldMetrics]:
    """Compute precision/recall/F1 from accumulated TP/FP/FN per field."""
    result: dict[str, FieldMetrics] = {}
    for fname, counts in per_field_counts.items():
        tp = counts.get("tp", 0)
        fp = counts.get("fp", 0)
        fn = counts.get("fn", 0)
        support = tp + fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        result[fname] = FieldMetrics(
            precision=precision, recall=recall, f1=f1, support=support
        )
    return result


def run_eval(
    jsonl_path: str | Path,
    schema_name: str,
    provider: str = "anthropic",
    model: str | None = None,
) -> EvalReport:
    """Run extraction on every line of a JSONL file and compute field-level metrics."""
    SchemaClass = registry.get(schema_name)
    if SchemaClass is None:
        raise KeyError(f"Unknown schema: {schema_name!r}. Available: {registry.list_schemas()}")

    schema_fields = set(SchemaClass.model_fields.keys())

    # per-field TP/FP/FN accumulators
    per_field: dict[str, dict[str, int]] = {
        f: {"tp": 0, "fp": 0, "fn": 0} for f in schema_fields
    }

    examples = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            examples.append(json.loads(line))

    for example in examples:
        doc: str = example["doc"]
        expected: dict[str, str] = example["expected"]

        try:
            result = extract(SchemaClass, doc, provider=provider, model=model)
        except ExtractionError as exc:
            warnings.warn(f"ExtractionError for example (doc[:40]={doc[:40]!r}): {exc}")
            # Count all expected fields as FN
            for fname in expected:
                if fname in per_field:
                    per_field[fname]["fn"] += 1
            continue

        extracted_fields = result.fields

        # TP / FN: expected fields
        for fname, exp_val in expected.items():
            if fname not in schema_fields:
                continue
            field_result = extracted_fields.get(fname)
            ext_val = field_result.value if field_result is not None else None
            if _match(ext_val, exp_val):
                per_field[fname]["tp"] += 1
            else:
                per_field[fname]["fn"] += 1

        # FP: schema fields the LLM returned that are not in expected
        for fname in schema_fields:
            if fname in expected:
                continue  # already counted above
            field_result = extracted_fields.get(fname)
            if field_result is not None and field_result.value is not None:
                per_field[fname]["fp"] += 1

    field_metrics = _compute_metrics(per_field)

    # Micro F1: aggregate TP/FP/FN across all fields
    total_tp = sum(per_field[f]["tp"] for f in per_field)
    total_fp = sum(per_field[f]["fp"] for f in per_field)
    total_fn = sum(per_field[f]["fn"] for f in per_field)
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0.0
    )

    return EvalReport(
        schema_name=schema_name,
        n_examples=len(examples),
        fields=field_metrics,
        micro_f1=micro_f1,
    )


def print_report(report: EvalReport) -> None:
    """Render eval results as a Rich table."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(
        title=f"Eval: {report.schema_name}  ({report.n_examples} examples)",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Field", style="bold")
    table.add_column("Precision", justify="right", min_width=10)
    table.add_column("Recall", justify="right", min_width=10)
    table.add_column("F1", justify="right", min_width=10)
    table.add_column("Support", justify="right", min_width=10)

    for fname, metrics in sorted(report.fields.items()):
        table.add_row(
            fname,
            f"{metrics.precision:.3f}",
            f"{metrics.recall:.3f}",
            f"{metrics.f1:.3f}",
            str(metrics.support),
        )

    table.add_section()
    table.add_row(
        "OVERALL (micro)",
        "",
        "",
        f"{report.micro_f1:.3f}",
        "",
        style="bold yellow",
    )

    console.print(table)
