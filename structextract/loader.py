from __future__ import annotations

from pathlib import Path


def load_document(path: str | Path) -> str:
    """Return normalized plain text from a .txt/.pdf/.html/.md file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return _load_txt(path)
    elif suffix == ".pdf":
        return _load_pdf(path)
    elif suffix in (".html", ".htm"):
        return _load_html(path)
    elif suffix == ".md":
        return _load_md(path)
    else:
        raise ValueError(f"Unsupported file extension: {suffix!r}. Supported: .txt, .pdf, .html, .htm, .md")


def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_pdf(path: Path) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n\n".join(pages)


def _load_html(path: Path) -> str:
    from bs4 import BeautifulSoup
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


def _load_md(path: Path) -> str:
    from markdown_it import MarkdownIt
    from bs4 import BeautifulSoup
    md_text = path.read_text(encoding="utf-8")
    md = MarkdownIt()
    html = md.render(md_text)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")
