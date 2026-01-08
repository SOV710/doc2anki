# doc2anki

Convert knowledge base documents into Anki flashcards using LLM-powered card generation.

中文版: ![zh_CN](README_zh.md)

## Overview

doc2anki is a CLI tool that transforms Markdown and Org-mode documents into Anki-compatible flashcard packages (`.apkg`). It leverages Large Language Models through OpenAI-compatible APIs to intelligently extract knowledge points and generate both basic Q&A cards and cloze deletion cards.

### Key Features

- **Smart Document Parsing**: Parses Markdown and Org-mode with full AST support via tree-sitter
- **Intelligent Chunking**: Auto-detects optimal heading level for document segmentation
- **Context-Aware Generation**: Preserves heading hierarchy and document metadata for better card quality
- **Interactive Classification**: Fine-grained control over which sections generate cards
- **Flexible Output**: Automatic deck hierarchy and tag generation from file paths

## Requirements

- Python 3.12 or higher
- An OpenAI-compatible LLM API service

## Installation

### Global Installation (Recommended)

```sh
# Using pipx
pipx install doc2anki

# Or using uv
uv tool install doc2anki
```

### Development Setup

```sh
git clone https://github.com/SOV710/doc2anki
cd doc2anki
uv sync
```

## Quick Start

1. **Create a configuration file** at `~/.config/doc2anki/ai_providers.toml`:

```toml
[openai]
enable = true
auth_type = "env"
api_key = "OPENAI_API_KEY"
default_base_url = "https://api.openai.com/v1"
default_model = "gpt-4o"
```

2. **Set your API key**:

```sh
export OPENAI_API_KEY="sk-..."
```

3. **Generate flashcards**:

```sh
doc2anki generate notes.md -p openai -o flashcards.apkg
```

## Configuration

doc2anki searches for configuration files in this order:

1. Path specified via `--config`
2. `./config/ai_providers.toml`
3. `~/.config/doc2anki/ai_providers.toml`

### Authentication Methods

| Auth Type | Description | `api_key` Field |
|-----------|-------------|-----------------|
| `direct` | Credentials in config file | The API key itself |
| `env` | Read from environment variable | Environment variable name |
| `dotenv` | Load from `.env` file | Key name in `.env` file |

### Example: Environment Variable Authentication

```toml
[deepseek]
enable = true
auth_type = "env"
api_key = "DEEPSEEK_API_KEY"
default_base_url = "https://api.deepseek.com"
default_model = "deepseek-chat"
```

### Example: Direct Authentication (Local LLM)

```toml
[ollama]
enable = true
auth_type = "direct"
api_key = "ollama"
default_base_url = "http://localhost:11434/v1"
default_model = "qwen2.5:14b"
```

See [docs/configuration.md](docs/configuration.md) for detailed configuration options.

## Usage

### List Available Providers

```sh
doc2anki list
doc2anki list --all  # Include disabled providers
```

### Validate Configuration

```sh
doc2anki validate
doc2anki validate -p openai
```

### Generate Flashcards

```sh
# Single file
doc2anki generate input.md -p openai -o output.apkg

# Entire directory (recursive)
doc2anki generate docs/ -p openai -o knowledge.apkg
```

### CLI Options

**Basic Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `outputs/output.apkg` | Output file path |
| `-p, --provider` | (required) | AI provider name |
| `-c, --config` | (auto-detect) | Configuration file path |
| `--prompt-template` | (built-in) | Custom Jinja2 prompt template |
| `--dry-run` | false | Parse and chunk only, skip LLM calls |
| `-I, --interactive` | false | Interactively classify each section |
| `--verbose` | false | Show detailed output |

**Chunking Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--max-tokens` | 3000 | Maximum tokens per chunk |
| `--max-retries` | 3 | LLM API retry attempts |
| `--include-parent-chain` | true | Include heading hierarchy in prompts |

**Card Organization:**

| Option | Default | Description |
|--------|---------|-------------|
| `--deck-depth` | 2 | Deck hierarchy depth from file path |
| `--extra-tags` | (none) | Additional tags (comma-separated) |

### Interactive Mode

Use `-I` or `--interactive` for fine-grained control over card generation:

```sh
doc2anki generate notes.md -p openai --interactive
```

Interactive mode allows you to classify each section as:

| Type | Cards | Context | Use Case |
|------|-------|---------|----------|
| **Full** | Yes | Yes | Fundamental concepts, definitions |
| **Card-only** | Yes | No | Independent knowledge points (default) |
| **Context-only** | No | Yes | Background information, prerequisites |
| **Skip** | No | No | Irrelevant content |

### Automatic Chunking

When no specific chunking level is specified, doc2anki automatically selects the optimal heading level by analyzing:

- Number of resulting chunks (minimum 2)
- Average chunk size (target: 500-2500 tokens)
- Size distribution uniformity (standard deviation < 50% of mean)

## Document Formats

### Markdown

doc2anki parses Markdown documents with:
- YAML frontmatter for metadata
- ATX and Setext heading styles
- Code blocks, lists, tables, and quotes

### Org-mode

doc2anki supports Org-mode with:
- File-level keywords (`#+TITLE`, `#+AUTHOR`, `#+FILETAGS`)
- Property drawers
- All standard Org heading levels

### File Path to Deck Mapping

File paths are automatically converted to Anki deck hierarchies and tags:

```
computing/network/tcp_ip.md
├── Deck: computing::network (with deck_depth=2)
└── Tags: computing, network, tcp_ip
```

## Project Structure

```
src/doc2anki/
├── cli.py              # CLI entry point (Typer-based)
├── config/             # Configuration loading and validation
├── parser/             # Document parsing (Markdown, Org-mode)
│   ├── tree.py         # Immutable AST data structures
│   ├── markdown.py     # tree-sitter Markdown parser
│   ├── orgmode.py      # orgparse-based Org parser
│   └── chunker.py      # Token-aware document chunking
├── pipeline/           # Processing pipeline
│   ├── classifier.py   # Chunk type classification
│   ├── context.py      # Context management
│   ├── processor.py    # Main pipeline orchestration
│   └── interactive.py  # Interactive classification session
├── llm/                # LLM integration
│   ├── client.py       # OpenAI-compatible API client
│   ├── prompt.py       # Jinja2 template rendering
│   └── extractor.py    # JSON response extraction
├── models/             # Pydantic data models
│   └── cards.py        # BasicCard, ClozeCard definitions
├── output/             # Output generation
│   └── apkg.py         # genanki-based APKG creation
└── templates/          # Prompt templates
    └── generate_cards.j2
```

## Roadmap

- **Async Support**: Add threading/asyncio for concurrent LLM calls
- **Decoupled Styling**: LLM returns Markdown IR, doc2anki converts to styled HTML templates
- **Built-in Themes**: Multiple card styling templates out of the box
- **Extended API Support**: Native support for Anthropic and Google APIs
- **Interactive TUI**: Replace Rich-based output with a Textual-based interactive terminal UI
- **Improved Non-Interactive Workflow**: Use LLM calls to summarize context pipeline, making doc2anki more plug-and-play

## Documentation

- [Architecture Overview](docs/architecture.md)
- [CLI Reference](docs/cli-reference.md)
- [Configuration Guide](docs/configuration.md)

## License

MIT License
