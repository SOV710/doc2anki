"""Immutable document tree structure for hierarchical parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from .metadata import DocumentMetadata


@dataclass(frozen=True, slots=True)
class HeadingNode:
    """
    Immutable AST node representing a heading and its content.

    All fields are immutable:
    - level, title, content are primitives/strings
    - children is a tuple (immutable sequence)
    - parent_titles provides hierarchy without mutable parent reference
    """

    level: int
    title: str
    content: str = ""
    children: tuple[HeadingNode, ...] = ()
    parent_titles: tuple[str, ...] = ()

    @property
    def path(self) -> tuple[str, ...]:
        """Heading hierarchy as immutable tuple of titles."""
        return (*self.parent_titles, self.title)

    @property
    def depth(self) -> int:
        """Depth in tree (0 for top-level nodes)."""
        return len(self.parent_titles)

    @property
    def full_content(self) -> str:
        """
        Get content including all descendants.

        Returns the heading line, content, and recursively all children.
        Computed on-demand, not stored.
        """
        parts = []

        # Heading line (Markdown format for display)
        heading_marker = "#" * self.level
        parts.append(f"{heading_marker} {self.title}")

        # Direct content
        if self.content.strip():
            parts.append(self.content.strip())

        # Children content
        for child in self.children:
            parts.append(child.full_content)

        return "\n\n".join(parts)

    @property
    def own_text(self) -> str:
        """
        Get only this node's own text (without children).

        Used for "independent classification" semantics where each node
        is classified independently. Only includes:
        - Heading line (Markdown format)
        - Direct content (no descendants)

        Format is consistent with full_content's heading line style.
        """
        parts = []

        # Heading line (Markdown format)
        heading_marker = "#" * self.level
        parts.append(f"{heading_marker} {self.title}")

        # Direct content only (no children)
        if self.content.strip():
            parts.append(self.content.strip())

        return "\n\n".join(parts)

    def iter_descendants(self) -> Iterator[HeadingNode]:
        """Iterate over all descendant nodes (depth-first)."""
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    def with_children(self, children: tuple[HeadingNode, ...]) -> HeadingNode:
        """Create a new node with updated children (structural sharing)."""
        return HeadingNode(
            level=self.level,
            title=self.title,
            content=self.content,
            children=children,
            parent_titles=self.parent_titles,
        )

    def __repr__(self) -> str:
        return f"HeadingNode(level={self.level}, title={self.title!r}, children={len(self.children)})"


@dataclass(frozen=True, slots=True)
class DocumentTree:
    """
    Immutable tree structure representing a parsed document.

    Supports:
    - Structural sharing for efficient transformations
    - Thread-safe concurrent access
    - Potential undo/redo via tree diffing
    """

    children: tuple[HeadingNode, ...] = ()
    preamble: str = ""
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata.empty)
    source_format: str = "markdown"

    def get_nodes_at_level(self, level: int) -> tuple[HeadingNode, ...]:
        """
        Get all nodes at a specific heading level.

        Args:
            level: Heading level (1-6)

        Returns:
            Tuple of HeadingNode objects at that level
        """
        result: list[HeadingNode] = []

        def collect(nodes: tuple[HeadingNode, ...]) -> None:
            for node in nodes:
                if node.level == level:
                    result.append(node)
                collect(node.children)

        collect(self.children)
        return tuple(result)

    def get_all_levels(self) -> frozenset[int]:
        """Get all heading levels present in the document (immutable)."""
        levels: set[int] = set()

        def collect(nodes: tuple[HeadingNode, ...]) -> None:
            for node in nodes:
                levels.add(node.level)
                collect(node.children)

        collect(self.children)
        return frozenset(levels)

    @property
    def max_level(self) -> int:
        """Get the maximum (deepest) heading level in the document."""
        levels = self.get_all_levels()
        return max(levels) if levels else 0

    @property
    def min_level(self) -> int:
        """Get the minimum (shallowest) heading level in the document."""
        levels = self.get_all_levels()
        return min(levels) if levels else 0

    def iter_all_nodes(self) -> Iterator[HeadingNode]:
        """Iterate over all nodes in depth-first order."""
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    def __repr__(self) -> str:
        return f"DocumentTree(children={len(self.children)}, levels={set(self.get_all_levels())})"
