"""Pipeline processor for document chunking and processing."""

from typing import Optional

from doc2anki.parser.tree import DocumentTree, HeadingNode
from doc2anki.parser.chunker import count_tokens

from .classifier import ChunkType, ClassifiedNode
from .context import ChunkWithContext


def auto_detect_level(tree: DocumentTree, max_tokens: int = 3000) -> int:
    """
    Automatically detect the optimal heading level for chunking.

    Pure local heuristics - zero API cost.

    Strategy:
    1. Count nodes at each heading level
    2. Estimate average tokens per node at each level
    3. Check variance - if too high, go deeper
    4. Choose level that produces:
       - At least 2 chunks
       - Average chunk size between 500-2500 tokens
       - Reasonably balanced distribution (low variance)

    Args:
        tree: DocumentTree to analyze
        max_tokens: Maximum tokens per chunk

    Returns:
        Recommended heading level for chunking
    """
    levels = sorted(tree.get_all_levels())

    if not levels:
        return 1

    for level in levels:
        nodes = tree.get_nodes_at_level(level)
        if len(nodes) < 2:
            continue

        token_counts = [count_tokens(n.full_content) for n in nodes]
        avg_tokens = sum(token_counts) / len(token_counts)

        # Variance check: if std_dev > 0.5 * avg, distribution is too uneven
        variance = sum((t - avg_tokens) ** 2 for t in token_counts) / len(token_counts)
        std_dev = variance ** 0.5
        if std_dev > 0.5 * avg_tokens:
            continue  # Too uneven, try deeper level

        if 500 <= avg_tokens <= max_tokens * 0.8:
            return level

    # Fallback: deepest level with multiple nodes
    for level in reversed(levels):
        if len(tree.get_nodes_at_level(level)) >= 2:
            return level

    # Ultimate fallback
    return levels[0] if levels else 1


def classify_nodes(
    tree: DocumentTree,
    level: int,
    default_type: ChunkType = ChunkType.CARD_ONLY,
) -> list[ClassifiedNode]:
    """
    Classify all nodes at a given level.

    In v1, all nodes get the same default type (CARD_ONLY).
    Future versions may support interactive classification.

    Args:
        tree: DocumentTree to process
        level: Heading level to extract
        default_type: Default ChunkType for all nodes

    Returns:
        List of ClassifiedNode objects
    """
    nodes = tree.get_nodes_at_level(level)
    return [ClassifiedNode(node=n, chunk_type=default_type) for n in nodes]


def process_pipeline(
    tree: DocumentTree,
    chunk_level: Optional[int] = None,
    max_tokens: int = 3000,
    global_context: Optional[dict[str, str]] = None,
    include_parent_chain: bool = True,
) -> list[ChunkWithContext]:
    """
    Process a document tree through the chunking pipeline.

    Args:
        tree: DocumentTree to process
        chunk_level: Heading level to chunk at (None for auto)
        max_tokens: Maximum tokens per chunk (for auto-detection)
        global_context: Document-level context dict
        include_parent_chain: Whether to include heading hierarchy

    Returns:
        List of ChunkWithContext objects ready for LLM processing
    """
    if global_context is None:
        global_context = {}

    # Auto-detect level if not specified
    if chunk_level is None:
        chunk_level = auto_detect_level(tree, max_tokens)

    # Classify nodes (v1: all CARD_ONLY)
    classified = classify_nodes(tree, chunk_level)

    # Process nodes and build ChunkWithContext objects
    accumulated_ctx = ""
    result: list[ChunkWithContext] = []

    for cn in classified:
        if cn.chunk_type == ChunkType.SKIP:
            continue

        # For nodes that generate cards, create ChunkWithContext
        if cn.should_generate_cards:
            chunk_ctx = ChunkWithContext(
                global_context=global_context,
                accumulated_context=accumulated_ctx,
                parent_chain=cn.node.path if include_parent_chain else [],
                chunk_content=cn.node.full_content,
            )
            result.append(chunk_ctx)

        # Update accumulated context for subsequent chunks
        if cn.should_add_to_context:
            accumulated_ctx += f"\n\n{cn.node.full_content}"

    return result
