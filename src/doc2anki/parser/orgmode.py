"""Org-mode document parser."""

import re
from pathlib import Path

import orgparse

from .base import BaseParser, ParseResult, parse_context_yaml
from .tree import HeadingNode, DocumentTree


class OrgModeParser(BaseParser):
    """Parser for Org-mode documents."""

    def parse(self, file_path: Path) -> ParseResult:
        """Parse an Org-mode document."""
        content = file_path.read_text(encoding="utf-8")
        global_context, remaining = self.extract_context_block(content)

        return ParseResult(
            global_context=global_context,
            content=remaining,
        )

    def extract_context_block(self, content: str) -> tuple[dict[str, str], str]:
        """
        Extract context block from Org-mode content.

        Looks for special block:
        #+BEGIN_CONTEXT
        - Term: "Definition"
        #+END_CONTEXT
        """
        # Pattern for context special block (case-insensitive)
        pattern = r"^\s*#\+BEGIN_CONTEXT\s*\n(.*?)\n\s*#\+END_CONTEXT\s*$"

        match = re.search(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if not match:
            return {}, content

        context_content = match.group(1)
        global_context = parse_context_yaml(context_content)

        # Remove the context block from content
        remaining = content[: match.start()] + content[match.end() :]
        # Clean up extra blank lines
        remaining = re.sub(r"\n{3,}", "\n\n", remaining)

        return global_context, remaining.strip()


def extract_org_sections(content: str) -> list[tuple[int, str, str]]:
    """
    Extract headings and their sections from Org-mode content.

    Returns list of (level, heading_text, section_content) tuples.
    """
    # Pattern for org headings (* Heading, ** Subheading, etc.)
    heading_pattern = r"^(\*+)\s+(.+?)$"

    lines = content.split("\n")
    sections = []
    current_level = 0
    current_heading = ""
    current_content = []
    in_block = False

    for line in lines:
        # Track blocks to avoid matching headings inside them
        if re.match(r"^\s*#\+BEGIN_", line, re.IGNORECASE):
            in_block = True
        elif re.match(r"^\s*#\+END_", line, re.IGNORECASE):
            in_block = False

        if in_block:
            current_content.append(line)
            continue

        match = re.match(heading_pattern, line)
        if match:
            # Save previous section
            if current_heading or current_content:
                sections.append(
                    (current_level, current_heading, "\n".join(current_content).strip())
                )

            # Start new section
            current_level = len(match.group(1))
            current_heading = match.group(2).strip()
            current_content = [line]  # Include the heading in content
        else:
            current_content.append(line)

    # Don't forget the last section
    if current_heading or current_content:
        sections.append(
            (current_level, current_heading, "\n".join(current_content).strip())
        )

    return sections


def split_org_by_top_headings(content: str) -> list[str]:
    """
    Split Org-mode content by top-level headings.

    If document has * headings, split by *.
    If no * but has **, split by **.
    And so on.

    Returns list of content chunks, each starting with its heading.
    """
    sections = extract_org_sections(content)

    if not sections:
        return [content] if content.strip() else []

    # Find the minimum (top) heading level
    heading_levels = [level for level, heading, _ in sections if heading]
    if not heading_levels:
        return [content] if content.strip() else []

    top_level = min(heading_levels)

    # Group sections by top-level headings
    chunks = []
    current_chunk = []

    for level, heading, section_content in sections:
        if level == top_level and heading:
            # Start new chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [section_content]
        else:
            current_chunk.append(section_content)

    # Don't forget the last chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return [c for c in chunks if c.strip()]


def build_tree(content: str) -> DocumentTree:
    """
    Build a DocumentTree from Org-mode content.

    Parses the content and creates a hierarchical tree structure
    based on heading levels.

    Args:
        content: Org-mode content string

    Returns:
        DocumentTree with parsed heading hierarchy
    """
    tree = DocumentTree()
    heading_pattern = r"^(\*+)\s+(.+?)$"

    lines = content.split("\n")
    in_block = False

    # Stack to track parent nodes: [(level, node), ...]
    stack: list[tuple[int, HeadingNode]] = []

    # Content accumulator for the current section
    current_content_lines: list[str] = []

    # Track content before any heading (preamble)
    preamble_lines: list[str] = []
    found_first_heading = False

    def flush_content() -> None:
        """Flush accumulated content to the current node."""
        nonlocal current_content_lines
        if not stack:
            return
        content_str = "\n".join(current_content_lines).strip()
        if content_str:
            stack[-1][1].content = content_str
        current_content_lines = []

    for line in lines:
        # Track blocks to avoid matching headings inside them
        if re.match(r"^\s*#\+BEGIN_", line, re.IGNORECASE):
            in_block = True
        elif re.match(r"^\s*#\+END_", line, re.IGNORECASE):
            in_block = False

        if in_block:
            if found_first_heading:
                current_content_lines.append(line)
            else:
                preamble_lines.append(line)
            continue

        match = re.match(heading_pattern, line)
        if match:
            # Save content of previous section
            flush_content()

            found_first_heading = True
            level = len(match.group(1))
            title = match.group(2).strip()

            # Create new node
            node = HeadingNode(level=level, title=title)

            # Find parent: pop stack until we find a lower level
            while stack and stack[-1][0] >= level:
                stack.pop()

            # Add to parent or tree root
            if stack:
                stack[-1][1].add_child(node)
            else:
                tree.add_child(node)

            # Push to stack
            stack.append((level, node))
        else:
            if found_first_heading:
                current_content_lines.append(line)
            else:
                preamble_lines.append(line)

    # Flush any remaining content
    flush_content()

    # Set preamble
    tree.preamble = "\n".join(preamble_lines).strip()

    return tree
