"""Prompt template rendering."""

import importlib.resources
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Template, BaseLoader, TemplateNotFound


class PackageLoader(BaseLoader):
    """Jinja2 loader that loads templates from package resources."""

    def __init__(self, package: str, path: str = ""):
        self.package = package
        self.path = path

    def get_source(self, environment, template):
        try:
            package_path = f"{self.package}.{self.path}" if self.path else self.package
            files = importlib.resources.files(package_path)
            source = (files / template).read_text(encoding="utf-8")
            return source, template, lambda: True
        except (FileNotFoundError, ModuleNotFoundError) as e:
            raise TemplateNotFound(template) from e


DEFAULT_TEMPLATE_NAME = "generate_cards.j2"


def load_template(template_path: Optional[Path] = None) -> Template:
    """
    Load Jinja2 template for card generation.

    Args:
        template_path: Custom template path, or None for default (from package)

    Returns:
        Jinja2 Template object
    """
    if template_path:
        # Custom template: use FileSystemLoader
        template_dir = template_path.parent
        template_name = template_path.name
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
        )
    else:
        # Default template: load from package resources
        env = Environment(
            loader=PackageLoader("doc2anki", "templates"),
            autoescape=False,
        )
        template_name = DEFAULT_TEMPLATE_NAME

    return env.get_template(template_name)


def build_prompt(
    global_context: dict[str, str],
    chunk: str,
    template: Template,
    parent_chain: Optional[list[str]] = None,
) -> str:
    """
    Build prompt for LLM from template.

    Args:
        global_context: Document-level context dict
        chunk: Content chunk to process
        template: Jinja2 template
        parent_chain: Heading hierarchy for context (optional)

    Returns:
        Rendered prompt string
    """
    return template.render(
        global_context=global_context,
        chunk_content=chunk,
        parent_chain=parent_chain or [],
    )
