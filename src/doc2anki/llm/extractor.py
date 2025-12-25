"""JSON extraction from LLM responses."""

import json
import re
from typing import Any


class JSONExtractionError(Exception):
    """Failed to extract JSON from response."""

    pass


def extract_json(text: str) -> dict[str, Any]:
    """
    Extract JSON from LLM response text.

    Tries in order:
    1. Direct parse (response is pure JSON)
    2. Extract from ```json ... ``` code block
    3. Find content between first { and last }

    Args:
        text: LLM response text

    Returns:
        Parsed JSON as dict

    Raises:
        JSONExtractionError: If JSON cannot be extracted
    """
    text = text.strip()

    # Try 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try 2: Extract from markdown code block
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Try 3: Find { ... } content
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise JSONExtractionError(
        f"Failed to extract JSON from response. Response preview:\n{text[:500]}..."
    )
