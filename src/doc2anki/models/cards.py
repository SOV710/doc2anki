"""Card Pydantic models for validation.

This module validates LLM-generated cards and normalizes fields to ensure:
- HTML payloads (Tokyo Night styled) can pass length constraints
- Cloze placeholders like [CLOZE:c1:...] are converted to Anki {{c1::...}} markers
- Tags are normalized and robust to common LLM output shapes
"""

from __future__ import annotations

import re
from typing import Annotated, List, Literal, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict


# HTML cards can be quite large (inline styles + <style> blocks).
# Keep an upper bound to avoid runaway outputs while not rejecting valid cards.
MAX_HTML_LEN = 20_000

# Accept both:
# 1) Standard Anki cloze markers: {{c1::...}}
# 2) Template-safe placeholders: [CLOZE:c1:...]
_CLOZE_ANKI_RE = re.compile(r"\{\{c\d+::", re.IGNORECASE)
_CLOZE_PLACEHOLDER_RE = re.compile(r"\[CLOZE:c(\d+):(.+?)\]", re.IGNORECASE | re.DOTALL)

# Remove characters that can break Anki tags / filesystem-ish conventions
_TAG_SANITIZE_RE = re.compile(r'[&/\\:*?"<>|]')


def _normalize_tags(v: Any) -> list[str]:
    """Normalize tags from common LLM outputs."""
    if v is None or v == "":
        return []

    # LLM sometimes returns a single string: "tag1, tag2"
    if isinstance(v, str):
        # split by comma or whitespace (but keep simple)
        raw = [t for t in re.split(r"[,\n]\s*|\s{2,}", v) if t.strip()]
    elif isinstance(v, (list, tuple, set)):
        raw = [str(t) for t in v if str(t).strip()]
    else:
        # Unexpected type: coerce to string
        raw = [str(v).strip()] if str(v).strip() else []

    return [_TAG_SANITIZE_RE.sub("_", t.lower().strip()) for t in raw if t.strip()]


def _convert_cloze_placeholders_to_anki(text: str) -> str:
    """Convert [CLOZE:cN:...] placeholders to {{cN::...}} markers."""
    def repl(m: re.Match) -> str:
        n = m.group(1)
        content = m.group(2).strip()
        return f"{{{{c{n}::{content}}}}}"

    # Convert all occurrences
    return _CLOZE_PLACEHOLDER_RE.sub(repl, text)


class BasicCard(BaseModel):
    """Basic question-answer card."""
    model_config = ConfigDict(extra="ignore")

    type: Literal["basic"]
    front: str = Field(min_length=5, max_length=MAX_HTML_LEN)
    back: str = Field(min_length=1, max_length=MAX_HTML_LEN)
    tags: List[str] = Field(default_factory=list)

    # Runtime fields (not from LLM)
    file_path: Optional[str] = None
    extra_tags: List[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v: Any) -> list[str]:
        return _normalize_tags(v)


class ClozeCard(BaseModel):
    """Cloze deletion card."""
    model_config = ConfigDict(extra="ignore")

    type: Literal["cloze"]
    text: str = Field(min_length=10, max_length=MAX_HTML_LEN)
    tags: List[str] = Field(default_factory=list)

    # Runtime fields (not from LLM)
    file_path: Optional[str] = None
    extra_tags: List[str] = Field(default_factory=list)

    @field_validator("text")
    @classmethod
    def ensure_cloze_marker(cls, v: str) -> str:
        """
        Ensure cloze card contains valid cloze markers.

        Accepts:
        - Standard Anki: {{cN::...}}
        - Placeholder: [CLOZE:cN:...], converted automatically
        """
        if not isinstance(v, str):
            raise TypeError("Cloze card text must be a string")

        text = v.strip()
        if not text:
            raise ValueError("Cloze card text cannot be empty")

        # Convert placeholder form -> Anki form
        if _CLOZE_PLACEHOLDER_RE.search(text):
            text = _convert_cloze_placeholders_to_anki(text)

        # Validate Anki cloze markers exist
        if not _CLOZE_ANKI_RE.search(text):
            raise ValueError("Cloze card must contain {{cN::...}} marker (or [CLOZE:cN:...] placeholder)")

        return text

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v: Any) -> list[str]:
        return _normalize_tags(v)


Card = Annotated[Union[BasicCard, ClozeCard], Field(discriminator="type")]


class CardOutput(BaseModel):
    """Container for LLM-generated cards."""
    model_config = ConfigDict(extra="ignore")

    cards: List[Card]
