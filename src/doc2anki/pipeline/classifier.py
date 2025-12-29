"""Chunk classification for the processing pipeline."""

from dataclasses import dataclass
from enum import Enum

from doc2anki.parser.tree import HeadingNode


class ChunkType(Enum):
    """
    Classification of how a chunk should be processed.

    The two dimensions are orthogonal:
    - Generate cards: whether to create Anki cards from this chunk
    - Add to context: whether to include this chunk in accumulated context

    | Generate | Context | Type         | Use Case                    |
    |----------|---------|--------------|----------------------------|
    | Yes      | Yes     | FULL         | Fundamental concepts       |
    | Yes      | No      | CARD_ONLY    | Independent knowledge (v1 default) |
    | No       | Yes     | CONTEXT_ONLY | Background info            |
    | No       | No      | SKIP         | Irrelevant content         |
    """

    FULL = "full"                 # Generate cards + add to context
    CARD_ONLY = "card_only"       # Generate cards, don't add to context
    CONTEXT_ONLY = "context_only" # Add to context, don't generate cards
    SKIP = "skip"                 # Ignore completely


@dataclass
class ClassifiedNode:
    """A HeadingNode with its classification decision."""

    node: HeadingNode
    chunk_type: ChunkType

    @property
    def should_generate_cards(self) -> bool:
        """Whether this chunk should generate cards."""
        return self.chunk_type in (ChunkType.FULL, ChunkType.CARD_ONLY)

    @property
    def should_add_to_context(self) -> bool:
        """Whether this chunk should be added to accumulated context."""
        return self.chunk_type in (ChunkType.FULL, ChunkType.CONTEXT_ONLY)
