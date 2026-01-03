"""Markdown document parser using tree-sitter."""

from __future__ import annotations

from pathlib import Path

import tree_sitter_markdown
from tree_sitter import Language, Parser, Node

from .tree import DocumentTree
from .metadata import DocumentMetadata
from .builder import TreeBuilder


class MarkdownParser:
    """
    Markdown parser using tree-sitter-markdown.

    Uses tree-sitter's AST for reliable heading extraction.
    Extracts YAML frontmatter for document metadata.
    """

    def __init__(self):
        self._language = Language(tree_sitter_markdown.language())
        self._parser = Parser(self._language)

    def parse(self, source: str | Path) -> DocumentTree:
        """
        Parse Markdown content or file to DocumentTree.

        Args:
            source: Markdown string or Path to .md file

        Returns:
            Immutable DocumentTree
        """
        if isinstance(source, Path):
            content = source.read_text(encoding="utf-8")
        else:
            content = source

        # Extract frontmatter first
        metadata, body = self._extract_frontmatter(content)

        # Parse with tree-sitter
        tree = self._parser.parse(body.encode("utf-8"))

        # Build document tree
        return self._build_tree(tree.root_node, body, metadata)

    def _extract_frontmatter(self, content: str) -> tuple[DocumentMetadata, str]:
        """
        Extract YAML frontmatter from content.

        Frontmatter is delimited by --- at the start of the file.
        """
        lines = content.split("\n")

        # Check for frontmatter delimiter at start
        if not lines or lines[0].strip() != "---":
            return DocumentMetadata.empty(), content

        # Find closing delimiter
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break

        if end_idx is None:
            return DocumentMetadata.empty(), content

        # Extract frontmatter content
        frontmatter_lines = lines[1:end_idx]
        frontmatter_text = "\n".join(frontmatter_lines)

        # Parse as YAML
        try:
            import yaml

            data = yaml.safe_load(frontmatter_text)
            if isinstance(data, dict):
                metadata = DocumentMetadata.from_dict(data, source_format="markdown")
            else:
                metadata = DocumentMetadata.empty()
        except Exception:
            metadata = DocumentMetadata.empty()

        # Return remaining content
        body = "\n".join(lines[end_idx + 1 :])
        return metadata, body

    def _build_tree(
        self, root: Node, source: str, metadata: DocumentMetadata
    ) -> DocumentTree:
        """Build DocumentTree from tree-sitter AST."""
        builder = TreeBuilder(source_format="markdown")
        builder.set_metadata(metadata)

        source_bytes = source.encode("utf-8")

        def get_text(node: Node) -> str:
            """Extract text for a node."""
            return source_bytes[node.start_byte : node.end_byte].decode("utf-8")

        def process_children(node: Node) -> None:
            """Process all children of a node."""
            for child in node.children:
                process_node(child)

        def process_node(node: Node) -> None:
            """Process AST node."""
            if node.type == "atx_heading":
                # ATX heading: # Title, ## Title, etc.
                level = 0
                title = ""

                for child in node.children:
                    if child.type == "atx_h1_marker":
                        level = 1
                    elif child.type == "atx_h2_marker":
                        level = 2
                    elif child.type == "atx_h3_marker":
                        level = 3
                    elif child.type == "atx_h4_marker":
                        level = 4
                    elif child.type == "atx_h5_marker":
                        level = 5
                    elif child.type == "atx_h6_marker":
                        level = 6
                    elif child.type in ("heading_content", "inline"):
                        title = get_text(child).strip()

                if level > 0:
                    builder.add_heading(level, title)

            elif node.type == "setext_heading":
                # Setext heading: Title\n===== or Title\n-----
                level = 0
                title = ""

                for child in node.children:
                    if child.type == "setext_h1_underline":
                        level = 1
                    elif child.type == "setext_h2_underline":
                        level = 2
                    elif child.type == "paragraph":
                        title = get_text(child).strip()

                if level > 0 and title:
                    builder.add_heading(level, title)

            elif node.type in (
                "paragraph",
                "fenced_code_block",
                "indented_code_block",
                "block_quote",
                "list",
                "html_block",
                "thematic_break",
                "table",
            ):
                # Content blocks
                text = get_text(node)
                builder.add_content(text)

            elif node.type in ("document", "section"):
                # Container nodes - process children
                process_children(node)

            else:
                # Unknown node type - try processing children
                process_children(node)

        process_node(root)
        return builder.build()


def build_tree(content: str) -> DocumentTree:
    """
    Convenience function to build tree from Markdown content.

    Args:
        content: Markdown content string

    Returns:
        Immutable DocumentTree
    """
    parser = MarkdownParser()
    return parser.parse(content)
