"""Prompt template rendering."""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Template


# Default template path (relative to package)
DEFAULT_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "templates"
DEFAULT_TEMPLATE_NAME = "generate_cards.j2"


def load_template(template_path: Optional[Path] = None) -> Template:
    """
    Load Jinja2 template for card generation.

    Args:
        template_path: Custom template path, or None for default

    Returns:
        Jinja2 Template object
    """
    if template_path:
        template_dir = template_path.parent
        template_name = template_path.name
    else:
        template_dir = DEFAULT_TEMPLATE_DIR
        template_name = DEFAULT_TEMPLATE_NAME

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,  # Don't escape content
    )

    return env.get_template(template_name)


def build_prompt(
    global_context: dict[str, str],
    chunk: str,
    template: Template,
) -> str:
    """
    Build prompt for LLM from template.

    Args:
        global_context: Document-level context dict
        chunk: Content chunk to process
        template: Jinja2 template

    Returns:
        Rendered prompt string
    """
    return template.render(
        global_context=global_context,
        chunk_content=chunk,
    )
