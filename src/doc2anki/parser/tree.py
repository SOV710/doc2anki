"""Document tree structure for hierarchical parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class HeadingNode:
    """
    AST node representing a heading and its content.

    A HeadingNode represents a section in the document, containing:
    - The heading level (1-6 for Markdown, 1-N for Org-mode)
    - The heading title text
    - The content directly under this heading (excluding children)
    - Child nodes for nested sub-headings
    """

    level: int
    title: str
    content: str = ""
    children: list[HeadingNode] = field(default_factory=list)
    _parent: HeadingNode | None = field(default=None, repr=False)

    def add_child(self, child: HeadingNode) -> None:
        """Add a child node."""
        child._parent = self
        self.children.append(child)

    @property
    def full_content(self) -> str:
        """
        Get content including all descendants.

        Returns the heading line, content, and recursively all children.
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
    def path(self) -> list[str]:
        """
        Get heading hierarchy as a list of titles.

        Returns list from root to this node, e.g., ["Network", "TCP", "Handshake"]
        """
        if self._parent is None:
            return [self.title]
        return self._parent.path + [self.title]

    @property
    def depth(self) -> int:
        """Get depth in tree (0 for root)."""
        if self._parent is None:
            return 0
        return self._parent.depth + 1

    def iter_descendants(self) -> Iterator[HeadingNode]:
        """Iterate over all descendant nodes (depth-first)."""
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    def __repr__(self) -> str:
        return f"HeadingNode(level={self.level}, title={self.title!r}, children={len(self.children)})"


@dataclass
class DocumentTree:
    """
    Tree structure representing a parsed document.

    The tree has a virtual root that contains all top-level headings.
    """

    # Top-level heading nodes
    children: list[HeadingNode] = field(default_factory=list)

    # Optional: content before any headings
    preamble: str = ""

    def add_child(self, child: HeadingNode) -> None:
        """Add a top-level heading node."""
        self.children.append(child)

    def get_nodes_at_level(self, level: int) -> list[HeadingNode]:
        """
        Get all nodes at a specific heading level.

        Args:
            level: Heading level (1-6)

        Returns:
            List of HeadingNode objects at that level
        """
        result = []

        def collect(nodes: list[HeadingNode]) -> None:
            for node in nodes:
                if node.level == level:
                    result.append(node)
                collect(node.children)

        collect(self.children)
        return result

    def get_all_levels(self) -> set[int]:
        """Get all heading levels present in the document."""
        levels = set()

        def collect(nodes: list[HeadingNode]) -> None:
            for node in nodes:
                levels.add(node.level)
                collect(node.children)

        collect(self.children)
        return levels

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
        return f"DocumentTree(children={len(self.children)}, levels={self.get_all_levels()})"
