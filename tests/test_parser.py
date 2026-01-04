"""Tests for document parsing."""

from pathlib import Path

import pytest

from doc2anki.parser import (
    build_document_tree,
    chunk_document,
    HeadingNode,
    DocumentTree,
    DocumentMetadata,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDocumentMetadata:
    """Tests for document metadata extraction."""

    def test_metadata_from_dict(self):
        data = {
            "title": "Test Title",
            "author": "Test Author",
            "tags": ["tag1", "tag2"],
        }
        metadata = DocumentMetadata.from_dict(data, source_format="markdown")

        assert metadata.title == "Test Title"
        assert metadata.author == "Test Author"
        assert metadata.tags == ("tag1", "tag2")
        assert metadata.source_format == "markdown"

    def test_metadata_empty(self):
        metadata = DocumentMetadata.empty()

        assert metadata.title is None
        assert metadata.author is None
        assert metadata.tags == ()
        assert metadata.raw_data == {}

    def test_metadata_get(self):
        data = {"custom_field": "custom_value"}
        metadata = DocumentMetadata.from_dict(data, source_format="markdown")

        assert metadata.get("custom_field") == "custom_value"
        assert metadata.get("nonexistent", "default") == "default"

    def test_metadata_contains(self):
        data = {"title": "Test"}
        metadata = DocumentMetadata.from_dict(data, source_format="markdown")

        assert "title" in metadata
        assert "nonexistent" not in metadata


class TestMarkdownParser:
    """Tests for Markdown document parsing."""

    def test_parse_markdown_with_frontmatter(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        # Should extract metadata from frontmatter
        assert tree.metadata.title == "TCP/IP 基础"
        assert tree.metadata.author == "test"
        assert "networking" in tree.metadata.tags
        assert "tcp" in tree.metadata.tags

    def test_parse_markdown_headings(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        # Should have parsed heading structure
        assert len(tree.children) >= 1

        # Check heading levels
        levels = tree.get_all_levels()
        assert 1 in levels or 2 in levels

    def test_parse_markdown_content(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        # Check that content is parsed
        all_content = "".join(node.full_content for node in tree.iter_all_nodes())
        assert "三次握手" in all_content
        assert "四次挥手" in all_content

    def test_chunk_markdown(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        # Get content from a node for chunking
        if tree.children:
            content = tree.children[0].full_content
            chunks = chunk_document(content, max_tokens=3000)

            # Should have at least one chunk
            assert len(chunks) >= 1

            # Each chunk should have content
            for chunk in chunks:
                assert len(chunk.strip()) > 0


class TestOrgModeParser:
    """Tests for Org-mode document parsing."""

    def test_parse_org_with_properties(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.org")

        # Should extract metadata from #+KEYWORD declarations
        assert tree.metadata.title == "数据结构基础"
        assert tree.metadata.author == "test"

        # Check filetags
        assert "datastructure" in tree.metadata.tags
        assert "algorithms" in tree.metadata.tags

    def test_parse_org_headings(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.org")

        # Should have parsed heading structure
        assert len(tree.children) >= 1

        # Check heading levels
        levels = tree.get_all_levels()
        assert 1 in levels or 2 in levels

    def test_parse_org_content(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.org")

        # Check that content is parsed
        all_content = "".join(node.full_content for node in tree.iter_all_nodes())
        assert "数组" in all_content
        assert "链表" in all_content

    def test_chunk_org(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.org")

        # Get content from a node for chunking
        if tree.children:
            content = tree.children[0].full_content
            chunks = chunk_document(content, max_tokens=3000)

            # Should have at least one chunk
            assert len(chunks) >= 1

            # Each chunk should have content
            for chunk in chunks:
                assert len(chunk.strip()) > 0


class TestDocumentTree:
    """Tests for DocumentTree structure."""

    def test_tree_immutability(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        # Tree should be frozen (immutable)
        with pytest.raises(AttributeError):
            tree.children = ()

    def test_heading_node_immutability(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        if tree.children:
            node = tree.children[0]
            # Node should be frozen (immutable)
            with pytest.raises(AttributeError):
                node.title = "Modified"

    def test_heading_node_path(self):
        content = """# Level 1

## Level 2

### Level 3
"""
        tree = build_document_tree(content, format="markdown")

        # Find the deepest node
        for node in tree.iter_all_nodes():
            if node.level == 3:
                assert node.path == ("Level 1", "Level 2", "Level 3")

    def test_tree_get_nodes_at_level(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        levels = tree.get_all_levels()
        for level in levels:
            nodes = tree.get_nodes_at_level(level)
            assert all(n.level == level for n in nodes)

    def test_get_chunks_at_level_includes_shallow_branches(self):
        """Test that get_chunks_at_level doesn't discard branches without target level."""
        content = """# Title

## 1

### 1-1

Content 1-1

## 2

### 2-1

#### 2-1-1

Content 2-1-1

### 2-2

Content 2-2
"""
        tree = build_document_tree(content, format="markdown")

        # At level 4, we should get:
        # - 1-1 (leaf, depth insufficient)
        # - 2-1-1 (exactly level 4)
        # - 2-2 (leaf, depth insufficient)
        chunks = tree.get_chunks_at_level(4)

        assert len(chunks) == 3

        titles = [chunk.title for chunk in chunks]
        assert "1-1" in titles
        assert "2-1-1" in titles
        assert "2-2" in titles

    def test_tree_iter_all_nodes(self):
        tree = build_document_tree(FIXTURES_DIR / "sample.md")

        nodes = list(tree.iter_all_nodes())
        # Should have some nodes
        assert len(nodes) > 0

        # All should be HeadingNode instances
        assert all(isinstance(n, HeadingNode) for n in nodes)


class TestChunking:
    """Tests for document chunking."""

    def test_small_content_single_chunk(self):
        content = "Small content that fits in one chunk."
        chunks = chunk_document(content, max_tokens=1000)
        assert len(chunks) == 1
        assert chunks[0] == content

    def test_empty_content(self):
        chunks = chunk_document("", max_tokens=1000)
        assert len(chunks) == 0

    def test_whitespace_only(self):
        chunks = chunk_document("   \n\n  ", max_tokens=1000)
        assert len(chunks) == 0


class TestFormatDetection:
    """Tests for format detection."""

    def test_detect_markdown_format(self):
        from doc2anki.parser import detect_format

        content = """# Heading 1
## Heading 2
Some content
"""
        assert detect_format(content) == "markdown"

    def test_detect_org_format(self):
        from doc2anki.parser import detect_format

        content = """* Heading 1
** Heading 2
Some content
"""
        assert detect_format(content) == "org"

    def test_build_tree_auto_detect(self):
        md_content = "# Markdown Heading\nContent"
        tree = build_document_tree(md_content)
        assert tree.source_format == "markdown"

        org_content = "* Org Heading\nContent"
        tree = build_document_tree(org_content)
        assert tree.source_format == "org"
