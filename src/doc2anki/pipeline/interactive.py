"""Interactive chunk classification for the processing pipeline."""

from dataclasses import dataclass, field

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from doc2anki.parser.tree import DocumentTree, HeadingNode
from doc2anki.parser.chunker import count_tokens

from .classifier import ChunkType, ClassifiedNode


# Mapping from user input to ChunkType
INPUT_MAP: dict[str, ChunkType] = {
    "f": ChunkType.FULL,
    "c": ChunkType.CARD_ONLY,
    "x": ChunkType.CONTEXT_ONLY,
    "s": ChunkType.SKIP,
}


@dataclass
class InteractiveSession:
    """Manages interactive chunk classification."""

    tree: DocumentTree
    nodes: list[HeadingNode] = field(default_factory=list)
    classified: list[ClassifiedNode] = field(default_factory=list)
    current_index: int = 0
    accumulated_tokens: int = 0

    def __post_init__(self) -> None:
        """Initialize nodes and classified list from tree."""
        # Traverse all nodes in document order (depth-first)
        self.nodes = list(self.tree.iter_all_nodes())
        # Initialize all as CARD_ONLY (default)
        self.classified = [
            ClassifiedNode(node=n, chunk_type=ChunkType.CARD_ONLY)
            for n in self.nodes
        ]

    @property
    def total(self) -> int:
        """Total number of nodes to classify."""
        return len(self.nodes)

    @property
    def is_complete(self) -> bool:
        """Check if all nodes have been classified."""
        return self.current_index >= self.total

    @property
    def remaining(self) -> int:
        """Number of remaining nodes to classify."""
        return self.total - self.current_index

    def classify_current(self, chunk_type: ChunkType) -> int:
        """
        Classify the current node and advance.

        Returns the token count of the classified chunk.
        Uses own_text (not full_content) for independent classification.
        """
        if self.is_complete:
            return 0

        node = self.nodes[self.current_index]
        # Use own_text for independent classification semantics
        tokens = count_tokens(node.own_text)

        self.classified[self.current_index].chunk_type = chunk_type

        # Track accumulated context tokens
        if chunk_type in (ChunkType.FULL, ChunkType.CONTEXT_ONLY):
            self.accumulated_tokens += tokens

        self.current_index += 1
        return tokens

    def classify_all_remaining(self, chunk_type: ChunkType) -> None:
        """Classify all remaining nodes with the same type."""
        while not self.is_complete:
            self.classify_current(chunk_type)

    def reset(self) -> None:
        """Reset classification to start over."""
        self.current_index = 0
        self.accumulated_tokens = 0
        for cn in self.classified:
            cn.chunk_type = ChunkType.CARD_ONLY

    def get_current_node(self) -> HeadingNode | None:
        """Get the current node being classified."""
        if self.is_complete:
            return None
        return self.nodes[self.current_index]


def display_section_summary(
    console: Console,
    nodes: list[HeadingNode],
    filename: str,
    max_tokens: int,
) -> list[tuple[str, int]]:
    """
    Display a summary table of all sections.

    Args:
        console: Rich console for output
        nodes: List of HeadingNode to display
        filename: Source filename for display
        max_tokens: Maximum tokens per chunk (for oversized warning)

    Returns:
        List of (breadcrumb, tokens) tuples for oversized nodes
    """
    console.print()
    console.print(
        Panel(
            f"Found [cyan]{len(nodes)}[/cyan] sections",
            title=f"[bold]Processing: {filename}[/bold]",
            border_style="blue",
        )
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Section", style="cyan")
    table.add_column("Tokens", justify="right")

    oversized: list[tuple[str, int]] = []

    for i, node in enumerate(nodes, 1):
        # Use own_text for independent classification semantics
        tokens = count_tokens(node.own_text)
        breadcrumb = " > ".join(node.path)

        if tokens > max_tokens:
            oversized.append((breadcrumb, tokens))
            token_str = f"[yellow]{tokens:,}[/yellow] [yellow]![/yellow]"
            style = "yellow"
        else:
            token_str = f"{tokens:,}"
            style = None

        table.add_row(str(i), breadcrumb, token_str, style=style)

    console.print(table)
    console.print()

    return oversized


def display_classification_help(console: Console) -> None:
    """Display classification options."""
    console.print(
        "[bold]Classification:[/bold] "
        "[green][F]ull[/green]  "
        "[blue][C]ard only[/blue]  "
        "[yellow]conte[X]t only[/yellow]  "
        "[red][S]kip[/red]"
    )
    console.print()


def preview_chunk(console: Console, node: HeadingNode) -> None:
    """Display a preview of the chunk content."""
    # Use own_text for independent classification semantics
    content = node.own_text
    # Truncate if too long
    max_preview = 2000
    if len(content) > max_preview:
        content = content[:max_preview] + "\n... [dim](truncated)[/dim]"

    # Use breadcrumb as title
    breadcrumb = " > ".join(node.path)
    syntax = Syntax(content, "markdown", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"[bold]{breadcrumb}[/bold]", border_style="cyan"))


def prompt_classification(
    console: Console,
    session: InteractiveSession,
) -> ChunkType | str:
    """
    Prompt user for classification of current node.

    Returns:
        ChunkType if valid classification, or str for special commands.
    """
    node = session.get_current_node()
    if node is None:
        return "done"

    # Use own_text for independent classification semantics
    tokens = count_tokens(node.own_text)
    idx = session.current_index + 1
    total = session.total

    # Build breadcrumb display
    breadcrumb = " > ".join(node.path)

    # Build prompt with token info
    token_info = f"[dim]({tokens:,} tokens)[/dim]"

    console.print(
        f"Section [bold]{idx}/{total}[/bold] "
        f"[cyan]{breadcrumb}[/cyan] {token_info}"
    )

    try:
        response = console.input(
            "[dim][F/C/X/S/preview/all:?/done][/dim] (default: C): "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Interrupted. Exiting...[/yellow]")
        raise SystemExit(1)

    if not response:
        return ChunkType.CARD_ONLY

    # Check for single-letter classification
    if response in INPUT_MAP:
        return INPUT_MAP[response]

    # Check for special commands
    if response in ("p", "preview"):
        return "preview"
    if response == "reset":
        return "reset"
    if response == "done":
        return "done"
    if response.startswith("all:"):
        return response  # Pass through for batch handling

    # Invalid input, default to CARD_ONLY
    console.print(f"[dim]Unknown input '{response}', using Card only[/dim]")
    return ChunkType.CARD_ONLY


def handle_batch_command(command: str) -> ChunkType | None:
    """
    Parse batch command like 'all:C'.

    Returns ChunkType if valid, None otherwise.
    """
    if not command.startswith("all:"):
        return None

    type_char = command[4:].lower()
    return INPUT_MAP.get(type_char)


def show_token_info(
    console: Console,
    chunk_tokens: int,
    accumulated_tokens: int,
) -> None:
    """Show token info after adding to context."""
    console.print(
        f"  [dim]This chunk:[/dim] {chunk_tokens:,} tokens\n"
        f"  [dim]Accumulated context:[/dim] {accumulated_tokens:,} tokens"
    )


def run_interactive_session(
    tree: DocumentTree,
    console: Console,
    filename: str = "",
    max_tokens: int = 3000,
) -> list[ClassifiedNode]:
    """
    Run an interactive classification session.

    Args:
        tree: DocumentTree to classify
        console: Rich console for output
        filename: Source filename for display
        max_tokens: Maximum tokens per chunk (for oversized warnings)

    Returns:
        List of ClassifiedNode with user classifications
    """
    session = InteractiveSession(tree=tree)

    if session.total == 0:
        console.print("[yellow]No sections found.[/yellow]")
        return []

    # Display summary and get oversized nodes
    oversized = display_section_summary(console, session.nodes, filename, max_tokens)

    # Display oversized warnings
    if oversized:
        console.print(f"[yellow]Warning: {len(oversized)} section(s) exceed max_tokens ({max_tokens}):[/yellow]")
        for breadcrumb, tokens in oversized:
            console.print(f"  [yellow]- {breadcrumb}: {tokens} tokens[/yellow]")
        console.print()

    display_classification_help(console)

    # Classification loop
    while not session.is_complete:
        result = prompt_classification(console, session)

        if isinstance(result, ChunkType):
            chunk_tokens = session.classify_current(result)
            # Show token info if adding to context
            if result in (ChunkType.FULL, ChunkType.CONTEXT_ONLY):
                show_token_info(console, chunk_tokens, session.accumulated_tokens)
            console.print()

        elif result == "preview":
            node = session.get_current_node()
            if node:
                preview_chunk(console, node)

        elif result == "reset":
            session.reset()
            console.print("[yellow]Reset. Starting over...[/yellow]\n")
            display_section_summary(console, session.nodes, filename, max_tokens)
            display_classification_help(console)

        elif result == "done":
            # Mark all remaining as default (CARD_ONLY)
            console.print(
                f"[dim]Marking remaining {session.remaining} sections as Card only[/dim]"
            )
            session.classify_all_remaining(ChunkType.CARD_ONLY)

        elif result.startswith("all:"):
            chunk_type = handle_batch_command(result)
            if chunk_type:
                console.print(
                    f"[dim]Classifying remaining {session.remaining} sections as {chunk_type.value}[/dim]"
                )
                session.classify_all_remaining(chunk_type)
            else:
                console.print(f"[red]Invalid batch command: {result}[/red]")

    # Summary
    console.print(Panel("[green]Classification complete![/green]", border_style="green"))

    # Count classifications
    counts = {t: 0 for t in ChunkType}
    for cn in session.classified:
        counts[cn.chunk_type] += 1

    console.print(
        f"  [green]Full:[/green] {counts[ChunkType.FULL]}  "
        f"[blue]Card only:[/blue] {counts[ChunkType.CARD_ONLY]}  "
        f"[yellow]Context only:[/yellow] {counts[ChunkType.CONTEXT_ONLY]}  "
        f"[red]Skip:[/red] {counts[ChunkType.SKIP]}"
    )
    console.print()

    return session.classified
