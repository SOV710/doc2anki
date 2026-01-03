"""Document metadata representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    """
    Immutable document-level metadata.

    Abstracts over format-specific metadata:
    - Markdown: YAML frontmatter
    - Org-mode: #+PROPERTY and :PROPERTIES: drawers

    The raw_data preserves original structure for format-specific access.
    """

    # Common metadata fields (extracted if present)
    title: str | None = None
    author: str | None = None
    date: str | None = None
    tags: tuple[str, ...] = ()

    # Raw metadata preserving original structure
    raw_data: Mapping[str, Any] = field(default_factory=dict)

    # Source format for introspection
    source_format: str = "unknown"

    def get(self, key: str, default: Any = None) -> Any:
        """Get raw metadata value by key."""
        return self.raw_data.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.raw_data

    @classmethod
    def empty(cls) -> DocumentMetadata:
        """Create empty metadata."""
        return cls()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], source_format: str) -> DocumentMetadata:
        """Create metadata from a dictionary."""
        # Extract tags, handling both list and string formats
        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, str):
            tags = tuple(t.strip() for t in raw_tags.split(",") if t.strip())
        elif isinstance(raw_tags, list):
            tags = tuple(str(t) for t in raw_tags)
        else:
            tags = ()

        return cls(
            title=data.get("title"),
            author=data.get("author"),
            date=str(data.get("date")) if data.get("date") is not None else None,
            tags=tags,
            raw_data=dict(data),
            source_format=source_format,
        )
