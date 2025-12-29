"""CLI interface for doc2anki."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import (
    ConfigError,
    get_provider_config,
    list_providers,
    fatal_exit,
)

app = typer.Typer(
    name="doc2anki",
    help="Convert knowledge base documents to Anki flashcards",
    no_args_is_help=True,
)
console = Console()

# Config file name
CONFIG_FILENAME = "ai_providers.toml"


def resolve_config_path(user_config: Optional[Path] = None) -> Path:
    """
    Resolve configuration file path with fallback chain.

    Resolution order:
    1. User-provided path (if specified and exists)
    2. ./config/ai_providers.toml (current directory)
    3. ~/.config/doc2anki/ai_providers.toml (XDG config)

    Args:
        user_config: User-provided config path (from --config option)

    Returns:
        Resolved config path

    Raises:
        ConfigError: If no config file is found
    """
    # 1. User-provided path
    if user_config and user_config.exists():
        return user_config

    # 2. Current directory
    local_config = Path("config") / CONFIG_FILENAME
    if local_config.exists():
        return local_config

    # 3. XDG config directory
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    xdg_config = Path(xdg_config_home) / "doc2anki" / CONFIG_FILENAME
    if xdg_config.exists():
        return xdg_config

    # No config found - return the user path or local path for error message
    if user_config:
        return user_config
    return local_config


# Default is None - will be resolved by resolve_config_path()
DEFAULT_CONFIG_PATH = None


@app.command("list")
def list_cmd(
    config: Optional[Path] = typer.Option(
        None,
        "-c",
        "--config",
        help="Path to AI provider configuration file",
    ),
    all_providers: bool = typer.Option(
        False,
        "--all",
        help="Show all providers including disabled ones",
    ),
) -> None:
    """List available AI providers."""
    resolved_config = resolve_config_path(config)
    try:
        providers = list_providers(resolved_config, show_all=all_providers)
    except ConfigError as e:
        fatal_exit(str(e))
        return

    if not providers:
        if all_providers:
            console.print("[yellow]No providers found in configuration file.[/yellow]")
        else:
            console.print(
                "[yellow]No enabled providers found. "
                "Use --all to see all providers.[/yellow]"
            )
        return

    table = Table(title="AI Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Auth Type", style="yellow")
    table.add_column("Model", style="magenta")
    table.add_column("Base URL", style="blue")

    for provider in providers:
        status = "[green]enabled[/green]" if provider.enabled else "[red]disabled[/red]"
        table.add_row(
            provider.name,
            status,
            provider.auth_type,
            provider.model or "-",
            provider.base_url or "-",
        )

    console.print(table)


@app.command("validate")
def validate_cmd(
    config: Optional[Path] = typer.Option(
        None,
        "-c",
        "--config",
        help="Path to AI provider configuration file",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "-p",
        "--provider",
        help="Validate specific provider configuration",
    ),
) -> None:
    """Validate configuration file."""
    resolved_config = resolve_config_path(config)
    try:
        providers = list_providers(resolved_config, show_all=True)
    except ConfigError as e:
        fatal_exit(str(e))
        return

    if provider:
        # Validate specific provider
        try:
            resolved = get_provider_config(resolved_config, provider)
            console.print(f"[green]Provider '{provider}' configuration is valid.[/green]")
            console.print(f"  Base URL: {resolved.base_url}")
            console.print(f"  Model: {resolved.model}")
            console.print(f"  API Key: {'*' * 8}...{resolved.api_key[-4:]}")
        except ConfigError as e:
            fatal_exit(str(e))
    else:
        # Validate all enabled providers
        console.print(f"[blue]Found {len(providers)} provider(s) in configuration.[/blue]")

        enabled_count = 0
        valid_count = 0

        for p in providers:
            if not p.enabled:
                continue

            enabled_count += 1
            try:
                get_provider_config(resolved_config, p.name)
                console.print(f"  [green]✓[/green] {p.name}")
                valid_count += 1
            except ConfigError as e:
                console.print(f"  [red]✗[/red] {p.name}: {e}")

        if enabled_count == 0:
            console.print("[yellow]No enabled providers to validate.[/yellow]")
        elif valid_count == enabled_count:
            console.print(f"[green]All {valid_count} enabled provider(s) are valid.[/green]")
        else:
            console.print(
                f"[yellow]{valid_count}/{enabled_count} enabled provider(s) are valid.[/yellow]"
            )


@app.command("generate")
def generate_cmd(
    input_path: Path = typer.Argument(
        ...,
        help="Input file or directory path",
    ),
    output: Path = typer.Option(
        Path("outputs/output.apkg"),
        "-o",
        "--output",
        help="Output APKG file path",
    ),
    provider: str = typer.Option(
        ...,
        "-p",
        "--provider",
        help="AI provider name to use",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "-c",
        "--config",
        help="Path to AI provider configuration file",
    ),
    prompt_template: Optional[Path] = typer.Option(
        None,
        "--prompt-template",
        help="Custom prompt template path",
    ),
    max_tokens: int = typer.Option(
        3000,
        "--max-tokens",
        help="Maximum tokens per chunk",
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        help="Maximum LLM call retries",
    ),
    deck_depth: int = typer.Option(
        2,
        "--deck-depth",
        help="Deck hierarchy depth from file path",
    ),
    extra_tags: Optional[str] = typer.Option(
        None,
        "--extra-tags",
        help="Additional tags (comma-separated)",
    ),
    chunk_level: Optional[int] = typer.Option(
        None,
        "--chunk-level",
        help="Heading level to chunk at (1-6, default: auto)",
    ),
    include_parent_chain: bool = typer.Option(
        True,
        "--include-parent-chain/--no-parent-chain",
        help="Include heading hierarchy as context",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Parse and chunk only, don't call LLM",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Verbose output",
    ),
) -> None:
    """Generate Anki cards from documents."""
    # Import parser here to avoid circular imports and speed up CLI startup
    from .parser import parse_document, build_document_tree, detect_format
    from .pipeline import process_pipeline, auto_detect_level

    # Validate input path
    if not input_path.exists():
        fatal_exit(f"Input path does not exist: {input_path}")
        return

    # Resolve config path
    resolved_config = resolve_config_path(config)

    # Load provider config (unless dry-run)
    provider_config = None
    if not dry_run:
        try:
            provider_config = get_provider_config(resolved_config, provider)
        except ConfigError as e:
            fatal_exit(str(e))
            return

        if verbose:
            console.print(f"[blue]Using provider:[/blue] {provider}")
            console.print(f"[blue]Model:[/blue] {provider_config.model}")
            console.print(f"[blue]Base URL:[/blue] {provider_config.base_url}")

    # Collect input files
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob("**/*.md")) + list(input_path.glob("**/*.org"))
        if not files:
            fatal_exit(f"No .md or .org files found in {input_path}")
            return

    if verbose:
        console.print(f"[blue]Found {len(files)} file(s) to process[/blue]")

    all_cards = []

    for file_path in files:
        if verbose:
            console.print(f"\n[blue]Processing:[/blue] {file_path}")

        # Parse document
        try:
            global_context, content = parse_document(file_path)
        except Exception as e:
            fatal_exit(f"Failed to parse {file_path}: {e}")
            return

        if verbose and global_context:
            console.print(f"[blue]Global context:[/blue] {len(global_context)} items")
            for term, definition in global_context.items():
                console.print(f"  - {term}: {definition}")

        # Build document tree
        try:
            doc_format = "org" if file_path.suffix.lower() == ".org" else "markdown"
            tree = build_document_tree(content, doc_format)
        except Exception as e:
            fatal_exit(f"Failed to build document tree for {file_path}: {e}")
            return

        # Determine chunk level
        actual_level = chunk_level
        if actual_level is None:
            actual_level = auto_detect_level(tree, max_tokens)

        if verbose:
            console.print(f"[blue]Document tree:[/blue] {tree}")
            console.print(f"[blue]Chunk level:[/blue] {actual_level}")

        # Process through pipeline
        try:
            chunk_contexts = process_pipeline(
                tree=tree,
                chunk_level=actual_level,
                max_tokens=max_tokens,
                global_context=global_context,
                include_parent_chain=include_parent_chain,
            )
        except Exception as e:
            fatal_exit(f"Failed to process pipeline for {file_path}: {e}")
            return

        if verbose:
            console.print(f"[blue]Chunks:[/blue] {len(chunk_contexts)}")
            for i, ctx in enumerate(chunk_contexts):
                preview = ctx.chunk_content[:100].replace("\n", " ")
                chain_str = " > ".join(ctx.parent_chain) if ctx.parent_chain else "(root)"
                console.print(f"  [{i+1}] {chain_str}")
                console.print(f"      {preview}...")

        if dry_run:
            console.print(f"\n[green]Dry run complete for {file_path}[/green]")
            console.print(f"  Global context items: {len(global_context)}")
            console.print(f"  Chunks: {len(chunk_contexts)}")
            continue

        # Import LLM module only when needed
        from .llm import generate_cards_for_chunk, create_client, load_template

        # Create client and load template
        client = create_client(provider_config)
        template = load_template(prompt_template)

        # Generate cards for each chunk
        try:
            cards = []
            for i, ctx in enumerate(chunk_contexts):
                if verbose:
                    console.print(f"[blue]Processing chunk {i + 1}/{len(chunk_contexts)}...[/blue]")

                chunk_cards = generate_cards_for_chunk(
                    chunk=ctx.chunk_content,
                    global_context=ctx.global_context,
                    client=client,
                    model=provider_config.model,
                    template=template,
                    max_retries=max_retries,
                    verbose=verbose,
                    parent_chain=ctx.parent_chain if include_parent_chain else None,
                )
                cards.extend(chunk_cards)

                if verbose:
                    console.print(f"  [green]Generated {len(chunk_cards)} cards[/green]")

        except Exception as e:
            fatal_exit(f"Failed to generate cards for {file_path}: {e}")
            return

        # Add file-based tags
        extra_tag_list = []
        if extra_tags:
            extra_tag_list = [t.strip() for t in extra_tags.split(",") if t.strip()]

        for card in cards:
            card.file_path = str(file_path)
            card.extra_tags = extra_tag_list

        all_cards.extend(cards)

        if verbose:
            console.print(f"[green]Generated {len(cards)} cards from {file_path}[/green]")

    if dry_run:
        return

    if not all_cards:
        console.print("[yellow]No cards generated.[/yellow]")
        return

    # Import output module only when needed
    from .output import create_apkg

    # Create APKG
    try:
        create_apkg(
            cards=all_cards,
            output_path=output,
            deck_depth=deck_depth,
            verbose=verbose,
        )
    except Exception as e:
        fatal_exit(f"Failed to create APKG: {e}")
        return

    console.print(f"\n[green]Successfully created {output} with {len(all_cards)} cards[/green]")


if __name__ == "__main__":
    app()
