from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from structextract.loader import load_document

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_txt():
    text = load_document(FIXTURES / "sample.txt")
    assert "Invoice #INV-2024-001" in text
    assert "Acme Corp" in text
    assert "$1,250.00" in text


def test_load_html():
    text = load_document(FIXTURES / "sample.html")
    # Tags should be stripped
    assert "<h1>" not in text
    assert "<p>" not in text
    # Visible text should be present
    assert "Invoice Summary" in text
    assert "Acme Corp" in text
    assert "INV-2024-001" in text


def test_load_md():
    text = load_document(FIXTURES / "sample.md")
    # Should contain the heading content without markdown syntax
    assert "Invoice Summary" in text
    assert "Acme Corp" in text
    assert "INV-2024-001" in text


def test_load_pdf(tmp_path: Path):
    """Test PDF loading using a monkeypatched pdfplumber."""
    fake_pdf_path = tmp_path / "fake.pdf"
    fake_pdf_path.write_bytes(b"%PDF fake")  # non-real PDF, never opened

    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page one content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page two content"

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page1, mock_page2]

    with patch("pdfplumber.open", return_value=mock_pdf):
        text = load_document(fake_pdf_path)

    assert "Page one content" in text
    assert "Page two content" in text
    assert "\n\n" in text  # pages joined with double newline


def test_load_pdf_empty_page(tmp_path: Path):
    """Test that None from extract_text is handled gracefully."""
    fake_pdf_path = tmp_path / "fake.pdf"
    fake_pdf_path.write_bytes(b"%PDF fake")

    mock_page = MagicMock()
    mock_page.extract_text.return_value = None  # simulate empty page

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=mock_pdf):
        text = load_document(fake_pdf_path)

    assert text == ""


def test_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        load_document("file.docx")


def test_load_document_accepts_string_path():
    text = load_document(str(FIXTURES / "sample.txt"))
    assert "Invoice" in text
