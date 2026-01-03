"""Org-mode document parser using orgparse."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import orgparse
from orgparse.node import OrgNode, OrgRootNode

from .tree import DocumentTree
from .metadata import DocumentMetadata
from .builder import TreeBuilder


class OrgParser:
    """
    Org-mode parser using orgparse library.

    Extracts:
    - Document structure (headings, content)
    - File-level #+PROPERTY declarations
    - Node-level :PROPERTIES: drawers
    """

    def parse(self, source: str | Path) -> DocumentTree:
        """
        Parse Org-mode content or file to DocumentTree.

        Args:
            source: Org-mode string or Path to .org file

        Returns:
            Immutable DocumentTree
        """
        if isinstance(source, Path):
            root = orgparse.load(str(source))
            content = source.read_text(encoding="utf-8")
        else:
            root = orgparse.loads(source)
            content = source

        # Extract file-level metadata
        metadata = self._extract_metadata(root, content)

        # Build document tree
        return self._build_tree(root, metadata)

    def _extract_metadata(
        self, root: OrgRootNode, content: str
    ) -> DocumentMetadata:
        """
        Extract document-level metadata.

        Sources:
        - #+TITLE, #+AUTHOR, #+DATE etc. (file-level keywords)
        - Properties from root node if any
        """
        raw_data: dict[str, Any] = {}

        # Extract #+KEYWORD declarations from content
        keyword_pattern = r"^#\+(\w+):\s*(.+)$"
        for match in re.finditer(keyword_pattern, content, re.MULTILINE):
            key = match.group(1).lower()
            value = match.group(2).strip()
            raw_data[key] = value

        # Extract root node properties (if any)
        if hasattr(root, "properties") and root.properties:
            for key, value in root.properties.items():
                raw_data[key.lower()] = value

        # Parse filetags
        tags: tuple[str, ...] = ()
        if "filetags" in raw_data:
            filetags = raw_data["filetags"]
            # Org filetags format: :tag1:tag2:tag3:
            tags = tuple(t for t in filetags.split(":") if t)

        return DocumentMetadata(
            title=raw_data.get("title"),
            author=raw_data.get("author"),
            date=raw_data.get("date"),
            tags=tags,
            raw_data=raw_data,
            source_format="org",
        )

    def _build_tree(
        self, root: OrgRootNode, metadata: DocumentMetadata
    ) -> DocumentTree:
        """Build DocumentTree from orgparse AST."""
        builder = TreeBuilder(source_format="org")
        builder.set_metadata(metadata)

        # Handle preamble (content before first heading)
        # orgparse stores this in root.body
        if hasattr(root, "body") and root.body:
            # Filter out #+KEYWORD lines from preamble
            preamble_lines = []
            for line in root.body.split("\n"):
                if not line.strip().startswith("#+"):
                    preamble_lines.append(line)
            preamble = "\n".join(preamble_lines).strip()
            if preamble:
                builder.set_preamble(preamble)

        def process_node(node: OrgNode) -> None:
            """Process orgparse node recursively."""
            # orgparse node levels are 1-indexed
            level = node.level

            if level > 0:  # Skip root node (level 0)
                builder.add_heading(level, node.heading)

                # Add node body content
                if node.body:
                    builder.add_content(node.body.strip())

            # Process children
            for child in node.children:
                process_node(child)

        # Process all children of root
        for child in root.children:
            process_node(child)

        return builder.build()


def build_tree(content: str) -> DocumentTree:
    """
    Convenience function to build tree from Org-mode content.

    Args:
        content: Org-mode content string

    Returns:
        Immutable DocumentTree
    """
    parser = OrgParser()
    return parser.parse(content)
