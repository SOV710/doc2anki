"""Context management for the processing pipeline."""

from dataclasses import dataclass, field


@dataclass
class ChunkWithContext:
    """
    A chunk ready for LLM processing, with all context attached.

    This is the final form before sending to the LLM API.
    """

    # Original document-level context (from context blocks)
    global_context: dict[str, str] = field(default_factory=dict)

    # Accumulated context from previous FULL/CONTEXT_ONLY chunks
    accumulated_context: str = ""

    # Heading hierarchy for this chunk
    parent_chain: list[str] = field(default_factory=list)

    # The actual chunk content
    chunk_content: str = ""

    def get_full_context_for_prompt(self) -> str:
        """
        Get the full context string for the LLM prompt.

        Returns formatted context including global and accumulated.
        """
        parts = []

        # Global context (definitions, terms)
        if self.global_context:
            parts.append("## Global Context")
            for term, definition in self.global_context.items():
                parts.append(f"- **{term}**: {definition}")
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
