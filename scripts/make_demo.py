"""
Generate demo.gif (an SVG file) showing StructExtract CLI output.

Run from the repo root:
    python scripts/make_demo.py

Produces demo.gif in the repo root (SVG content, .gif extension so GitHub
renders it inline via <img> in Markdown).
"""
import pathlib
from rich.console import Console
from rich.table import Table
from rich import box

OUTPUT_PATH = pathlib.Path(__file__).parent.parent / "demo.gif"


def main() -> None:
    console = Console(record=True, width=100)

    # ── Section 1: CLI extraction run ────────────────────────────────────────
    console.print(
        "[bold green]$[/] [bold]structextract run --schema invoice_schema.py --doc invoice.txt[/]"
    )
    console.print()

    extraction_json = """\
{
  "schema_name": "Invoice",
  "fields": {
    "vendor_name": {
      "value": "Acme Corp",
      "source_span": {"start": 17, "end": 26, "quote": "Acme Corp"},
      "confidence": "high"
    },
    "invoice_number": {
      "value": "INV-001",
      "source_span": {"start": 9, "end": 16, "quote": "INV-001"},
      "confidence": "high"
    },
    "total_amount": {
      "value": "$1,200.00",
      "source_span": {"start": 42, "end": 51, "quote": "$1,200.00"},
      "confidence": "high"
    },
    "due_date": {
      "value": "2024-03-31",
      "source_span": {"start": 58, "end": 68, "quote": "2024-03-31"},
      "confidence": "high"
    }
  }
}"""
    console.print(extraction_json, markup=False)
    console.print()

    # ── Section 2: Eval run ───────────────────────────────────────────────────
    console.print(
        "[bold green]$[/] [bold]structextract eval --schema Invoice"
        " --dataset evals/invoice_samples.jsonl[/]"
    )
    console.print()

    table = Table(
        title="Eval: Invoice (5 examples)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        min_width=70,
    )
    table.add_column("Field", style="white", min_width=18)
    table.add_column("Precision", justify="right", style="green")
    table.add_column("Recall", justify="right", style="green")
    table.add_column("F1", justify="right", style="bold green")
    table.add_column("Support", justify="right")

    rows = [
        ("due_date",        "1.000", "1.000", "1.000", "5"),
        ("invoice_number",  "1.000", "0.800", "0.889", "5"),
        ("total_amount",    "1.000", "1.000", "1.000", "5"),
        ("vendor_name",     "1.000", "1.000", "1.000", "5"),
    ]
    for row in rows:
        table.add_row(*row)

    table.add_section()
    table.add_row(
        "[bold]OVERALL (micro)[/]", "", "", "[bold]0.972[/]", ""
    )

    console.print(table)
    console.print()
    console.print("[dim]Done.[/]")

    # ── Export ────────────────────────────────────────────────────────────────
    svg = console.export_svg(title="StructExtract demo")
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
