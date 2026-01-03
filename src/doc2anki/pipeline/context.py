"""Context management for the processing pipeline."""

from dataclasses import dataclass, field

from doc2anki.parser.metadata import DocumentMetadata


@dataclass
class ChunkWithContext:
    """
    A chunk ready for LLM processing, with all context attached.

    This is the final form before sending to the LLM API.
    """

    # Document metadata (from frontmatter/properties)
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata.empty)

    # Accumulated context from previous FULL/CONTEXT_ONLY chunks
    accumulated_context: str = ""

    # Heading hierarchy for this chunk (immutable tuple)
    parent_chain: tuple[str, ...] = ()

    # The actual chunk content
    chunk_content: str = ""

    def get_full_context_for_prompt(self) -> str:
        """
        Get the full context string for the LLM prompt.

        Returns formatted context including metadata and accumulated context.
        """
        parts = []

        # Document metadata
        if self.metadata.raw_data:
            parts.append("## Document Metadata")
            for key, value in self.metadata.raw_data.items():
                parts.append(f"- **{key}**: {value}")
            parts.append("")

        # Accumulated context from previous chunks
        if self.accumulated_context.strip():
            parts.append("## Previous Content")
            parts.append(self.accumulated_context.strip())
            parts.append("")

        # Parent chain (hierarchy breadcrumb)
        if self.parent_chain:
            breadcrumb = " > ".join(self.parent_chain)
            parts.append(f"## Location: {breadcrumb}")
            parts.append("")

        return "\n".join(parts) if parts else ""
