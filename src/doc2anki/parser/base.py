"""Base parser interface and utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ParseResult:
    """Result of parsing a document."""

    global_context: dict[str, str]
    content: str  # Document content without context block


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """
        Parse a document and extract global context and content.

        Args:
            file_path: Path to the document file

        Returns:
            ParseResult with global_context dict and content string
        """
        pass

    @abstractmethod
    def extract_context_block(self, content: str) -> tuple[dict[str, str], str]:
        """
        Extract context block from document content.

        Args:
            content: Raw document content

        Returns:
            Tuple of (context_dict, remaining_content)
        """
        pass


def parse_context_yaml(content: str) -> dict[str, str]:
    """
    Parse context block content as YAML.

    Expected format:
    - Term: "Definition"
    - Term2: "Definition2"

    Returns empty dict on parse failure (lenient parsing).
    """
    if not content.strip():
        return {}

    try:
        items = yaml.safe_load(content)

        if items is None:
            return {}

        if isinstance(items, dict):
            # Direct dict format: {Term: "Definition"}
            return {str(k): str(v) for k, v in items.items()}

        if isinstance(items, list):
            # List format: [{Term: "Definition"}, ...]
            result = {}
            for item in items:
                if isinstance(item, dict):
                    for k, v in item.items():
                        result[str(k)] = str(v)
            return result

        return {}
    except yaml.YAMLError:
        return {}
    except Exception:
        return {}
