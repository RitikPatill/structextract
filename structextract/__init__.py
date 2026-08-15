__version__ = "0.1.0"

from structextract.extractor import extract
from structextract.models import ExtractionResult, FieldResult, SourceSpan

__all__ = ["extract", "ExtractionResult", "FieldResult", "SourceSpan"]
