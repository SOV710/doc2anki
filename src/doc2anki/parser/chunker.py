"""Document chunking with token counting."""

import re
import sys

import tiktoken
from rich.console import Console

console = Console()

# Use cl100k_base encoding (compatible with GPT-4, Claude, etc.)
_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    return len(_encoder.encode(text))


class ChunkingError(Exception):
    """Error during chunking that requires fatal exit."""

    pass


def chunk_document(content: str, max_tokens: int = 3000) -> list[str]:
    """
    Chunk document content respecting token limits.

    Strategy:
    1. Split by top-level headings first
    2. If any chunk exceeds max_tokens, recursively split by next heading level
    3. If a leaf node (no sub-headings) still exceeds, fatal exit

    Args:
        content: Document content (without context block)
        max_tokens: Maximum tokens per chunk

    Returns:
        List of content chunks, each under max_tokens

    Raises:
        ChunkingError: If an indivisible block exceeds token limit
    """
    if not content.strip():
        return []

    # Check if whole content fits
    if count_tokens(content) <= max_tokens:
        return [content]

    # Try to split by headings (works for both Markdown and Org)
    chunks = split_by_headings(content)

    if len(chunks) == 1 and chunks[0] == content:
        # Could not split further - this is an atomic block that's too large
        raise ChunkingError(
            f"Content block exceeds {max_tokens} tokens ({count_tokens(content)} tokens) "
            f"and cannot be further divided. Please manually split this content:\n"
            f"{content[:200]}..."
        )

    # Recursively check and split each chunk
    result = []
    for chunk in chunks:
        token_count = count_tokens(chunk)
        if token_count <= max_tokens:
            result.append(chunk)
        else:
            # Try to recursively split this chunk
            sub_chunks = chunk_document(chunk, max_tokens)
            result.extend(sub_chunks)

    return result


def split_by_headings(content: str) -> list[str]:
    """
    Split content by the top-level headings found.

    Works for both Markdown (# ## ###) and Org-mode (* ** ***).
    Detects format automatically.
    """
    # Detect if it's Markdown or Org-mode by checking heading patterns
    md_headings = re.findall(r"^#{1,6}\s+.+$", content, re.MULTILINE)
    org_headings = re.findall(r"^\*+\s+.+$", content, re.MULTILINE)

    if len(md_headings) >= len(org_headings):
        return split_markdown_by_headings(content)
    else:
        return split_org_by_headings(content)


def split_markdown_by_headings(content: str) -> list[str]:
    """Split Markdown content by top-level headings."""
    # Find all heading levels present
    levels = set()
    for match in re.finditer(r"^(#{1,6})\s+.+$", content, re.MULTILINE):
        levels.add(len(match.group(1)))

    if not levels:
        return [content]

    # Split by the top (smallest number) level
    top_level = min(levels)
    pattern = rf"^({'#' * top_level})\s+"

    chunks = []
    current_chunk = []
    in_code_block = False

    for line in content.split("\n"):
        # Track code blocks
        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            in_code_block = not in_code_block

        if not in_code_block and re.match(pattern, line):
            # New top-level heading
            if current_chunk:
                chunk_text = "\n".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
            current_chunk = [line]
        else:
            current_chunk.append(line)

    # Add last chunk
    if current_chunk:
        chunk_text = "\n".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks if chunks else [content]


def split_org_by_headings(content: str) -> list[str]:
    """Split Org-mode content by top-level headings."""
    # Find all heading levels present
    levels = set()
    for match in re.finditer(r"^(\*+)\s+.+$", content, re.MULTILINE):
        levels.add(len(match.group(1)))

    if not levels:
        return [content]

    # Split by the top (smallest number) level
    top_level = min(levels)
    pattern = rf"^({'\\*' * top_level})\s+"

    chunks = []
    current_chunk = []
    in_block = False

    for line in content.split("\n"):
        # Track blocks
        if re.match(r"^\s*#\+BEGIN_", line, re.IGNORECASE):
            in_block = True
        elif re.match(r"^\s*#\+END_", line, re.IGNORECASE):
            in_block = False

        if not in_block and re.match(pattern, line):
            # New top-level heading
            if current_chunk:
                chunk_text = "\n".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
            current_chunk = [line]
        else:
            current_chunk.append(line)

    # Add last chunk
    if current_chunk:
        chunk_text = "\n".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks if chunks else [content]
