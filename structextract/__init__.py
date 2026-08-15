__version__ = "0.1.0"

from structextract.extractor import extract
from structextract.loader import load_document
from structextract.models import ExtractionResult, FieldResult, SourceSpan

__all__ = ["extract", "load_document", "ExtractionResult", "FieldResult", "SourceSpan"]
