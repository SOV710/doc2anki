"""Markdown document parser."""

import re
from pathlib import Path

from markdown_it import MarkdownIt

from .base import BaseParser, ParseResult, parse_context_yaml
from .tree import HeadingNode, DocumentTree


class MarkdownParser(BaseParser):
    """Parser for Markdown documents."""

    def __init__(self):
        self.md = MarkdownIt()

    def parse(self, file_path: Path) -> ParseResult:
        """Parse a Markdown document."""
        content = file_path.read_text(encoding="utf-8")
        global_context, remaining = self.extract_context_block(content)

        return ParseResult(
            global_context=global_context,
            content=remaining,
        )

    def extract_context_block(self, content: str) -> tuple[dict[str, str], str]:
        """
        Extract context block from Markdown content.

        Looks for fenced code block with 'context' language:
        ```context
        - Term: "Definition"
        ```
        """
        # Pattern for context fenced code block
        # Matches ```context or ~~~context blocks
        pattern = r"^(```|~~~)context\s*\n(.*?)\n\1\s*$"

        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

        if not match:
            return {}, content

        context_content = match.group(2)
        global_context = parse_context_yaml(context_content)

        # Remove the context block from content
        remaining = content[: match.start()] + content[match.end() :]
        # Clean up extra blank lines
        remaining = re.sub(r"\n{3,}", "\n\n", remaining)

        return global_context, remaining.strip()


def extract_headings_and_sections(content: str) -> list[tuple[int, str, str]]:
    """
    Extract headings and their sections from Markdown content.

    Returns list of (level, heading_text, section_content) tuples.
    Sections include everything from the heading to the next heading of same or higher level.
    """
    # Pattern for ATX headings (# Heading)
    heading_pattern = r"^(#{1,6})\s+(.+?)$"

    lines = content.split("\n")
    sections = []
    current_level = 0
    current_heading = ""
    current_content = []
    in_code_block = False

    for line in lines:
        # Track code blocks to avoid matching headings inside them
        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            in_code_block = not in_code_block

        if in_code_block:
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


def split_by_top_headings(content: str) -> list[str]:
    """
    Split content by top-level headings.

    If document has h1 headings, split by h1.
    If no h1 but has h2, split by h2.
    And so on.

    Returns list of content chunks, each starting with its heading.
    """
    sections = extract_headings_and_sections(content)

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
    Build a DocumentTree from Markdown content.

    Parses the content and creates a hierarchical tree structure
    based on heading levels.

    Args:
        content: Markdown content string

    Returns:
        DocumentTree with parsed heading hierarchy
    """
    tree = DocumentTree()
    heading_pattern = r"^(#{1,6})\s+(.+?)$"

    lines = content.split("\n")
    in_code_block = False

    # Stack to track parent nodes: [(level, node), ...]
    # We use this to find the correct parent for each new heading
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
        # Track code blocks to avoid matching headings inside them
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block

        if in_code_block:
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
