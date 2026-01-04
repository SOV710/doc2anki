"""Pipeline processor for document chunking and processing."""

from dataclasses import dataclass
from typing import Optional

from doc2anki.parser.tree import DocumentTree, HeadingNode
from doc2anki.parser.chunker import count_tokens
from doc2anki.parser.metadata import DocumentMetadata

from .classifier import ChunkType, ClassifiedNode
from .context import ChunkWithContext


@dataclass
class ContentBlock:
    """文档中的一个内容块（heading + 其直接 content）"""

    level: int  # heading 级别 (0 = preamble)
    heading: str  # heading 行，preamble 为空
    content: str  # 直接内容（不含子节点）
    path: tuple[str, ...]  # 祖先路径

    def to_text(self) -> str:
        """转换为文本"""
        parts = []
        if self.heading:
            parts.append(self.heading)
        if self.content.strip():
            parts.append(self.content.strip())
        return "\n\n".join(parts)


def flatten_tree(tree: DocumentTree) -> list[ContentBlock]:
    """
    将 DocumentTree 展平为线性内容块序列。

    按文档顺序输出：
    1. Preamble（如果有）
    2. 每个 heading 及其直接 content（深度优先）

    Args:
        tree: DocumentTree to flatten

    Returns:
        List of ContentBlock in document order
    """
    blocks: list[ContentBlock] = []

    # 1. Preamble
    if tree.preamble.strip():
        blocks.append(
            ContentBlock(
                level=0,
                heading="",
                content=tree.preamble.strip(),
                path=(),
            )
        )

    # 2. 递归展平所有节点
    def flatten_node(node: HeadingNode) -> None:
        heading_line = "#" * node.level + " " + node.title
        blocks.append(
            ContentBlock(
                level=node.level,
                heading=heading_line,
                content=node.content,  # 只取直接 content，不递归
                path=node.path,
            )
        )
        # 递归子节点
        for child in node.children:
            flatten_node(child)

    for child in tree.children:
        flatten_node(child)

    return blocks


def greedy_chunk(
    blocks: list[ContentBlock],
    max_tokens: int,
    metadata: DocumentMetadata,
) -> list[ChunkWithContext]:
    """
    贪婪合并内容块直到接近 max_tokens。

    策略：
    - 从头开始累积
    - 当下一个块会超过 max_tokens 时，切分
    - 每个 chunk 尽可能大

    Args:
        blocks: List of ContentBlock to merge
        max_tokens: Maximum tokens per chunk
        metadata: Document metadata

    Returns:
        List of ChunkWithContext objects
    """
    if not blocks:
        return []

    result: list[ChunkWithContext] = []
    current_blocks: list[ContentBlock] = []
    current_tokens = 0

    for block in blocks:
        block_text = block.to_text()
        block_tokens = count_tokens(block_text)

        # 检查是否需要切分
        if current_blocks and current_tokens + block_tokens > max_tokens:
            # 保存当前 chunk
            chunk_content = "\n\n".join(b.to_text() for b in current_blocks)
            # 使用第一个非空 path 或第一个 block 的 path
            first_path = next((b.path for b in current_blocks if b.path), ())
            result.append(
                ChunkWithContext(
                    metadata=metadata,
                    accumulated_context="",
                    parent_chain=first_path,
                    chunk_content=chunk_content,
                )
            )
            # 重置
            current_blocks = []
            current_tokens = 0

        # 添加当前 block
        current_blocks.append(block)
        current_tokens += block_tokens

    # 保存最后一个 chunk
    if current_blocks:
        chunk_content = "\n\n".join(b.to_text() for b in current_blocks)
        first_path = next((b.path for b in current_blocks if b.path), ())
        result.append(
            ChunkWithContext(
                metadata=metadata,
                accumulated_context="",
                parent_chain=first_path,
                chunk_content=chunk_content,
            )
        )

    return result


def classify_nodes(
    tree: DocumentTree,
    level: int,
    default_type: ChunkType = ChunkType.CARD_ONLY,
) -> list[ClassifiedNode]:
    """
    Classify nodes for chunking at a given level.

    Used by interactive mode only.

    Args:
        tree: DocumentTree to process
        level: Heading level to chunk at
        default_type: Default ChunkType for all nodes

    Returns:
        List of ClassifiedNode objects
    """
    nodes = tree.get_nodes_at_level(level)
    return [ClassifiedNode(node=n, chunk_type=default_type) for n in nodes]


def _process_with_classified_nodes(
    tree: DocumentTree,
    classified_nodes: list[ClassifiedNode],
    max_tokens: int,
    include_parent_chain: bool,
) -> list[ChunkWithContext]:
    """
    Process pre-classified nodes (interactive mode).

    Args:
        tree: DocumentTree
        classified_nodes: Pre-classified nodes
        max_tokens: Maximum tokens per chunk
        include_parent_chain: Whether to include heading hierarchy

    Returns:
        List of ChunkWithContext objects
    """
    accumulated_ctx = ""
    result: list[ChunkWithContext] = []

    for cn in classified_nodes:
        if cn.chunk_type == ChunkType.SKIP:
            continue

        # For nodes that generate cards, create ChunkWithContext
        if cn.should_generate_cards:
            chunk_ctx = ChunkWithContext(
                metadata=tree.metadata,
                accumulated_context=accumulated_ctx,
                parent_chain=cn.node.path if include_parent_chain else (),
                chunk_content=cn.node.full_content,
            )
            result.append(chunk_ctx)

        # Update accumulated context for subsequent chunks
        if cn.should_add_to_context:
            accumulated_ctx += f"\n\n{cn.node.full_content}"

    return result


def process_pipeline(
    tree: DocumentTree,
    max_tokens: int = 3000,
    include_parent_chain: bool = True,
    classified_nodes: Optional[list[ClassifiedNode]] = None,
) -> list[ChunkWithContext]:
    """
    Process a document tree through the chunking pipeline.

    策略：展平 + 贪婪合并
    - 无损：所有内容都被包含
    - 有序：保持文档原始顺序
    - 智能：在 token 边界切分

    Args:
        tree: DocumentTree to process
        max_tokens: Maximum tokens per chunk
        include_parent_chain: Whether to include heading hierarchy
        classified_nodes: Pre-classified nodes (from interactive mode)

    Returns:
        List of ChunkWithContext objects ready for LLM processing
    """
    # 交互模式：使用预分类节点
    if classified_nodes is not None:
        return _process_with_classified_nodes(
            tree, classified_nodes, max_tokens, include_parent_chain
        )

    # 新逻辑：展平 + 贪婪合并
    blocks = flatten_tree(tree)
    return greedy_chunk(blocks, max_tokens, tree.metadata)
