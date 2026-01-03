"""Document parsing module for doc2anki."""

from pathlib import Path
import re

from .tree import HeadingNode, DocumentTree
from .metadata import DocumentMetadata
from .builder import TreeBuilder
from .markdown import MarkdownParser
from .markdown import build_tree as build_markdown_tree
from .orgmode import OrgParser
from .orgmode import build_tree as build_org_tree
from .chunker import chunk_document, count_tokens, ChunkingError


def build_document_tree(source: str | Path, format: str | None = None) -> DocumentTree:
    """
    Build a DocumentTree from document content or file.

    Args:
        source: Document content string or Path to file
        format: Document format ("markdown" or "org").
                If None, auto-detect from file extension or content.

    Returns:
        Immutable DocumentTree with parsed heading hierarchy and metadata

    Raises:
        ValueError: If format is not supported or cannot be detected
    """
    # Determine format
    if format is None:
        if isinstance(source, Path):
            suffix = source.suffix.lower()
            if suffix == ".md":
                format = "markdown"
            elif suffix == ".org":
                format = "org"
            else:
                # Try to detect from content
                content = source.read_text(encoding="utf-8")
                format = detect_format(content)
        else:
            format = detect_format(source)

    # Parse based on format
    if format in ("markdown", "md"):
        parser = MarkdownParser()
        return parser.parse(source)
    elif format in ("org", "orgmode"):
        parser = OrgParser()
        return parser.parse(source)
    else:
        raise ValueError(f"Unsupported format: {format}. Supported: markdown, org")


def detect_format(content: str) -> str:
    """
    Detect document format from content.

    Returns "markdown" or "org" based on heading patterns.
    """
    md_headings = len(re.findall(r"^#{1,6}\s+.+$", content, re.MULTILINE))
    org_headings = len(re.findall(r"^\*+\s+.+$", content, re.MULTILINE))

    return "org" if org_headings > md_headings else "markdown"


__all__ = [
    # Core types
    "HeadingNode",
    "DocumentTree",
    "DocumentMetadata",
    "TreeBuilder",
    # Parsers
    "MarkdownParser",
    "OrgParser",
    # Functions
    "build_document_tree",
    "detect_format",
    # Chunking
    "chunk_document",
    "count_tokens",
    "ChunkingError",
]
