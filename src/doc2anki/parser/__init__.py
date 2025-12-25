"""Document parsing module for doc2anki."""

from pathlib import Path

from .base import ParseResult
from .markdown import MarkdownParser
from .orgmode import OrgModeParser
from .chunker import chunk_document, count_tokens, ChunkingError


def parse_document(file_path: Path) -> tuple[dict[str, str], str]:
    """
    Parse a document file and extract global context and content.

    Args:
        file_path: Path to the document file (.md or .org)

    Returns:
        Tuple of (global_context dict, content string)

    Raises:
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".md":
        parser = MarkdownParser()
    elif suffix == ".org":
        parser = OrgModeParser()
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Supported: .md, .org")

    result = parser.parse(file_path)
    return result.global_context, result.content


__all__ = [
    "parse_document",
    "chunk_document",
    "count_tokens",
    "ChunkingError",
    "ParseResult",
    "MarkdownParser",
    "OrgModeParser",
]
