"""LLM client for card generation."""

import sys
from pathlib import Path
from typing import Optional, List, Union

from openai import OpenAI
from pydantic import ValidationError
from rich.console import Console

from ..config import ProviderConfig
from ..models import CardOutput, BasicCard, ClozeCard
from .extractor import extract_json, JSONExtractionError
from .prompt import load_template, build_prompt

console = Console()


class LLMError(Exception):
    """LLM call error."""

    pass


def create_client(provider_config: ProviderConfig) -> OpenAI:
    """Create OpenAI-compatible client."""
    return OpenAI(
        base_url=provider_config.base_url,
        api_key=provider_config.api_key,
    )


def call_llm(
    client: OpenAI,
    model: str,
    prompt: str,
    use_json_mode: bool = True,
) -> str:
    """
    Call LLM API and get response.

    Args:
        client: OpenAI client
        model: Model name
        prompt: Prompt text
        use_json_mode: Whether to request JSON response format

    Returns:
        Response text

    Raises:
        LLMError: If API call fails
    """
    try:
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)

        if not response.choices:
            raise LLMError("Empty response from LLM")

        return response.choices[0].message.content or ""

    except Exception as e:
        if "response_format" in str(e).lower():
            # Provider doesn't support response_format, retry without it
            if use_json_mode:
                return call_llm(client, model, prompt, use_json_mode=False)
        raise LLMError(f"LLM API call failed: {e}")


def generate_cards_for_chunk(
    chunk: str,
    global_context: dict[str, str],
    client: OpenAI,
    model: str,
    template,
    max_retries: int = 3,
    verbose: bool = False,
    parent_chain: Optional[List[str]] = None,
) -> List[Union[BasicCard, ClozeCard]]:
    """
    Generate cards for a single chunk.

    Args:
        chunk: Content chunk
        global_context: Document-level context
        client: OpenAI client
        model: Model name
        template: Jinja2 template
        max_retries: Max retry attempts
        verbose: Verbose output
        parent_chain: Heading hierarchy for this chunk

    Returns:
        List of validated cards

    Raises:
        SystemExit: If all retries fail
    """
    prompt = build_prompt(global_context, chunk, template, parent_chain)

    for attempt in range(max_retries):
        try:
            if verbose:
                console.print(f"  [dim]Attempt {attempt + 1}/{max_retries}...[/dim]")

            response = call_llm(client, model, prompt)
            json_data = extract_json(response)
            output = CardOutput.model_validate(json_data)

            return list(output.cards)

        except (JSONExtractionError, ValidationError, LLMError) as e:
            if verbose:
                console.print(f"  [yellow]Attempt {attempt + 1} failed: {e}[/yellow]")

            if attempt == max_retries - 1:
                console.print(
                    f"[red]Failed to generate valid cards after {max_retries} attempts[/red]"
                )
                console.print(f"[red]Last error: {e}[/red]")
                console.print(f"[yellow]Chunk content:[/yellow]\n{chunk[:500]}...")
                sys.exit(1)

    return []  # Should not reach here


def generate_cards_for_chunks(
    chunks: List[str],
    global_context: dict[str, str],
    provider_config: ProviderConfig,
    prompt_template_path: Optional[Path] = None,
    max_retries: int = 3,
    verbose: bool = False,
) -> List[Union[BasicCard, ClozeCard]]:
    """
    Generate cards for all chunks.

    Args:
        chunks: List of content chunks
        global_context: Document-level context
        provider_config: Provider configuration
        prompt_template_path: Custom template path
        max_retries: Max retry attempts
        verbose: Verbose output

    Returns:
        List of all generated cards
    """
    client = create_client(provider_config)
    template = load_template(prompt_template_path)

    all_cards = []

    for i, chunk in enumerate(chunks):
        if verbose:
            console.print(f"[blue]Processing chunk {i + 1}/{len(chunks)}...[/blue]")

        cards = generate_cards_for_chunk(
            chunk=chunk,
            global_context=global_context,
            client=client,
            model=provider_config.model,
            template=template,
            max_retries=max_retries,
            verbose=verbose,
        )

        all_cards.extend(cards)

        if verbose:
            console.print(f"  [green]Generated {len(cards)} cards[/green]")

    return all_cards
