"""APKG file generation using genanki."""

import re
from pathlib import Path
from typing import List, Union

import genanki
from rich.console import Console

from ..models import BasicCard, ClozeCard

console = Console()

# Fixed model IDs for consistency
BASIC_MODEL_ID = 1607392319
CLOZE_MODEL_ID = 1607392320

# Pre-defined Anki models
BASIC_MODEL = genanki.Model(
    BASIC_MODEL_ID,
    "doc2anki Basic",
    fields=[
        {"name": "Front"},
        {"name": "Back"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
        },
    ],
)

CLOZE_MODEL = genanki.Model(
    CLOZE_MODEL_ID,
    "doc2anki Cloze",
    fields=[
        {"name": "Text"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "{{cloze:Text}}",
            "afmt": "{{cloze:Text}}<br>{{Extra}}",
        },
    ],
    model_type=genanki.Model.CLOZE,
)


def normalize_tag(tag: str) -> str:
    """
    Normalize tag for Anki compatibility.

    Removes special characters that Anki doesn't handle well.
    """
    return re.sub(r'[&/\\:*?"<>|\s]', "_", tag.lower().strip())


def path_to_deck_and_tags(
    file_path: str, deck_depth: int = 2
) -> tuple[str, list[str]]:
    """
    Generate deck name and tags from file path.

    Args:
        file_path: Path to the source file
        deck_depth: How many path components to use for deck name

    Returns:
        Tuple of (deck_name, tags_list)

    Example:
        file_path = "computing/pl/c_cpp/gcc/linker.md"
        deck_depth = 2

        Returns:
        deck_name = "computing::pl"
        tags = ["computing", "pl", "c_cpp", "gcc", "linker"]
    """
    parts = Path(file_path).with_suffix("").parts

    # Filter out common directory names that shouldn't be in deck/tags
    filtered_parts = [p for p in parts if p not in (".", "..", "tests", "fixtures")]

    if not filtered_parts:
        return "doc2anki", []

    # Deck: take first N levels
    deck_parts = filtered_parts[:deck_depth]
    deck_name = "::".join(normalize_tag(p) for p in deck_parts)

    # Tags: all levels (normalized)
    tags = [normalize_tag(p) for p in filtered_parts]

    return deck_name, tags


def create_note(
    card: Union[BasicCard, ClozeCard],
    deck_depth: int,
) -> tuple[genanki.Note, str]:
    """
    Create a genanki Note from a card.

    Args:
        card: BasicCard or ClozeCard
        deck_depth: Depth for deck naming

    Returns:
        Tuple of (Note, deck_name)
    """
    # Get deck name and path-based tags
    deck_name = "doc2anki"
    path_tags = []

    if card.file_path:
        deck_name, path_tags = path_to_deck_and_tags(card.file_path, deck_depth)

    # Combine all tags
    all_tags = list(card.tags) + path_tags + list(card.extra_tags)
    all_tags = list(dict.fromkeys(all_tags))  # Remove duplicates, preserve order

    if isinstance(card, BasicCard):
        note = genanki.Note(
            model=BASIC_MODEL,
            fields=[card.front, card.back],
            tags=all_tags,
        )
    else:  # ClozeCard
        note = genanki.Note(
            model=CLOZE_MODEL,
            fields=[card.text, ""],  # Extra field empty
            tags=all_tags,
        )

    return note, deck_name


def create_apkg(
    cards: List[Union[BasicCard, ClozeCard]],
    output_path: Path,
    deck_depth: int = 2,
    verbose: bool = False,
) -> None:
    """
    Create APKG file from cards.

    Args:
        cards: List of cards to include
        output_path: Path for output APKG file
        deck_depth: Depth for deck naming from file paths
        verbose: Verbose output
    """
    # Group cards by deck name
    decks: dict[str, genanki.Deck] = {}

    for card in cards:
        note, deck_name = create_note(card, deck_depth)

        if deck_name not in decks:
            # Generate a consistent deck ID from the name
            deck_id = abs(hash(deck_name)) % (10**10)
            decks[deck_name] = genanki.Deck(deck_id, deck_name)

        decks[deck_name].add_note(note)

    if verbose:
        console.print(f"[blue]Creating {len(decks)} deck(s):[/blue]")
        for name, deck in decks.items():
            console.print(f"  - {name}: {len(deck.notes)} notes")

    # Create package with all decks
    package = genanki.Package(list(decks.values()))
    package.write_to_file(str(output_path))

    if verbose:
        console.print(f"[green]Written to {output_path}[/green]")
