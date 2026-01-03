"""Builder pattern for constructing immutable document trees."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .metadata import DocumentMetadata


@dataclass
class MutableNode:
    """Mutable node used during tree construction."""

    level: int
    title: str
    content: str = ""
    children: list[MutableNode] = field(default_factory=list)
    parent: Optional[MutableNode] = field(default=None, repr=False)

    def add_child(self, child: MutableNode) -> None:
        """Add a child node."""
        child.parent = self
        self.children.append(child)

    def freeze(self, parent_titles: tuple[str, ...] = ()) -> "HeadingNode":
        """
        Convert to immutable HeadingNode (recursive).

        Args:
            parent_titles: Tuple of ancestor heading titles

        Returns:
            Frozen HeadingNode with all descendants frozen
        """
        # Import here to avoid circular dependency
        from .tree import HeadingNode

        frozen_children = tuple(
            child.freeze(parent_titles=(*parent_titles, self.title))
            for child in self.children
        )

        return HeadingNode(
            level=self.level,
            title=self.title,
            content=self.content,
            children=frozen_children,
            parent_titles=parent_titles,
        )


class TreeBuilder:
    """
    Builder for constructing immutable DocumentTree.

    Usage:
        builder = TreeBuilder()
        builder.set_preamble("intro text")
        builder.set_metadata(metadata)
        builder.add_heading(1, "Title")
        builder.add_content("Some content")
        builder.add_heading(2, "Subsection")
        tree = builder.build()
    """

    def __init__(self, source_format: str = "markdown"):
        self._source_format = source_format
        self._preamble_lines: list[str] = []
        self._metadata: DocumentMetadata = DocumentMetadata.empty()
        self._root_children: list[MutableNode] = []
        self._stack: list[MutableNode] = []
        self._current_content: list[str] = []
        self._found_first_heading = False

    def set_preamble(self, preamble: str) -> "TreeBuilder":
        """Set document preamble."""
        self._preamble_lines = [preamble]
        return self

    def add_preamble_line(self, line: str) -> "TreeBuilder":
        """Add a line to preamble."""
        self._preamble_lines.append(line)
        return self

    def set_metadata(self, metadata: DocumentMetadata) -> "TreeBuilder":
        """Set document metadata."""
        self._metadata = metadata
        return self

    def add_heading(self, level: int, title: str) -> "TreeBuilder":
        """Add a heading, establishing proper hierarchy."""
        self._flush_content()

        self._found_first_heading = True
        node = MutableNode(level=level, title=title)

        # Pop stack until we find appropriate parent
        while self._stack and self._stack[-1].level >= level:
            self._stack.pop()

        # Add to parent or root
        if self._stack:
            self._stack[-1].add_child(node)
        else:
            self._root_children.append(node)

        self._stack.append(node)
        return self

    def add_content(self, content: str) -> "TreeBuilder":
        """Add content to current section."""
        if self._found_first_heading:
            self._current_content.append(content)
        else:
            self._preamble_lines.append(content)
        return self

    def add_content_line(self, line: str) -> "TreeBuilder":
        """Add a line of content."""
        return self.add_content(line)

    def _flush_content(self) -> None:
        """Flush accumulated content to current node."""
        if self._stack and self._current_content:
            content = "\n".join(self._current_content).strip()
            self._stack[-1].content = content
        self._current_content = []

    def build(self) -> "DocumentTree":
        """Build the immutable DocumentTree."""
        # Import here to avoid circular dependency
        from .tree import DocumentTree

        self._flush_content()

        frozen_children = tuple(node.freeze() for node in self._root_children)

        return DocumentTree(
            children=frozen_children,
            preamble="\n".join(self._preamble_lines).strip(),
            metadata=self._metadata,
            source_format=self._source_format,
        )
