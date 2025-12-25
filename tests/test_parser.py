"""Tests for document parsing."""

from pathlib import Path

import pytest

from doc2anki.parser import parse_document, chunk_document
from doc2anki.parser.base import parse_context_yaml


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestContextParsing:
    """Tests for context block parsing."""

    def test_parse_context_yaml_list_format(self):
        content = """- TCP: "传输控制协议"
- IP: "网际协议"
"""
        result = parse_context_yaml(content)
        assert result == {"TCP": "传输控制协议", "IP": "网际协议"}

    def test_parse_context_yaml_dict_format(self):
        content = """TCP: "传输控制协议"
IP: "网际协议"
"""
        result = parse_context_yaml(content)
        assert result == {"TCP": "传输控制协议", "IP": "网际协议"}

    def test_parse_context_yaml_empty(self):
        result = parse_context_yaml("")
        assert result == {}

    def test_parse_context_yaml_invalid(self):
        result = parse_context_yaml("not valid yaml: [[[")
        assert result == {}


class TestMarkdownParser:
    """Tests for Markdown document parsing."""

    def test_parse_markdown_with_context(self):
        global_context, content = parse_document(FIXTURES_DIR / "sample.md")

        # Should extract context
        assert "TCP" in global_context
        assert "IP" in global_context
        assert "三次握手" in global_context

        # Context block should be removed from content
        assert "```context" not in content
        assert "TCP/IP 基础" in content

    def test_chunk_markdown(self):
        _, content = parse_document(FIXTURES_DIR / "sample.md")
        chunks = chunk_document(content, max_tokens=3000)

        # Should have at least one chunk
        assert len(chunks) >= 1

        # Each chunk should have content
        for chunk in chunks:
            assert len(chunk.strip()) > 0


class TestOrgModeParser:
    """Tests for Org-mode document parsing."""

    def test_parse_org_with_context(self):
        global_context, content = parse_document(FIXTURES_DIR / "sample.org")

        # Should extract context
        assert "时间复杂度" in global_context
        assert "空间复杂度" in global_context

        # Context block should be removed from content
        assert "#+BEGIN_CONTEXT" not in content
        assert "数据结构基础" in content

    def test_chunk_org(self):
        _, content = parse_document(FIXTURES_DIR / "sample.org")
        chunks = chunk_document(content, max_tokens=3000)

        # Should have at least one chunk
        assert len(chunks) >= 1

        # Each chunk should have content
        for chunk in chunks:
            assert len(chunk.strip()) > 0


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
