"""Card Pydantic models for validation."""

import re
from typing import Literal, Union, List, Optional

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated


class BasicCard(BaseModel):
    """Basic question-answer card."""

    type: Literal["basic"]
    front: str = Field(min_length=5, max_length=1000)
    back: str = Field(min_length=1, max_length=3000)
    tags: List[str] = Field(default_factory=list)

    # Runtime fields (not from LLM)
    file_path: Optional[str] = None
    extra_tags: List[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v):
        """Normalize tags: remove special characters, lowercase."""
        if not v:
            return []
        return [re.sub(r'[&/\\:*?"<>|]', "_", tag.lower().strip()) for tag in v]


class ClozeCard(BaseModel):
    """Cloze deletion card."""

    type: Literal["cloze"]
    text: str = Field(min_length=10, max_length=3000)
    tags: List[str] = Field(default_factory=list)

    # Runtime fields (not from LLM)
    file_path: Optional[str] = None
    extra_tags: List[str] = Field(default_factory=list)

    @field_validator("text")
    @classmethod
    def must_have_cloze_marker(cls, v: str) -> str:
        """Ensure cloze card has {{cN::...}} marker."""
        if not re.search(r"\{\{c\d+::", v):
            raise ValueError("Cloze card must contain {{cN::...}} marker")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v):
        """Normalize tags: remove special characters, lowercase."""
        if not v:
            return []
        return [re.sub(r'[&/\\:*?"<>|]', "_", tag.lower().strip()) for tag in v]


Card = Annotated[Union[BasicCard, ClozeCard], Field(discriminator="type")]


class CardOutput(BaseModel):
    """Container for LLM-generated cards."""

    cards: List[Card]
