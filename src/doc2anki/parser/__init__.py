"""Document parsing module for doc2anki."""

from pathlib import Path

from .base import ParseResult
from .markdown import MarkdownParser
from .markdown import build_tree as build_markdown_tree
from .orgmode import OrgModeParser
from .orgmode import build_tree as build_org_tree
from .chunker import chunk_document, count_tokens, ChunkingError
from .tree import HeadingNode, DocumentTree


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


def build_document_tree(content: str, format: str = "markdown") -> DocumentTree:
    """
    Build a DocumentTree from document content.

    Args:
        content: Document content string
        format: Document format ("markdown" or "org")

    Returns:
        DocumentTree with parsed heading hierarchy

    Raises:
        ValueError: If format is not supported
    """
    if format in ("markdown", "md"):
        return build_markdown_tree(content)
    elif format in ("org", "orgmode"):
        return build_org_tree(content)
    else:
        raise ValueError(f"Unsupported format: {format}. Supported: markdown, org")


def detect_format(content: str) -> str:
    """
    Detect document format from content.

    Returns "markdown" or "org" based on heading patterns.
    """
    import re

    md_headings = len(re.findall(r"^#{1,6}\s+.+$", content, re.MULTILINE))
    org_headings = len(re.findall(r"^\*+\s+.+$", content, re.MULTILINE))

    return "org" if org_headings > md_headings else "markdown"


__all__ = [
    "parse_document",
    "build_document_tree",
    "detect_format",
    "chunk_document",
    "count_tokens",
    "ChunkingError",
    "ParseResult",
    "MarkdownParser",
    "OrgModeParser",
    "HeadingNode",
    "DocumentTree",
]
