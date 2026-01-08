# CLI Reference

## Installation

### Global Installation

```sh
# Using pipx (recommended)
pipx install doc2anki

# Or using uv
uv tool install doc2anki
```

### Development Mode

```sh
git clone https://github.com/SOV710/doc2anki
cd doc2anki
uv sync
uv run doc2anki --help
```

## Command Overview

```
doc2anki [OPTIONS] COMMAND [ARGS]

Options:
  -v, --version  Show version and exit

Commands:
  list      List available AI providers
  validate  Validate configuration file
  generate  Generate Anki cards from documents
```

---

## Global Options

| Option | Description |
|--------|-------------|
| `-v, --version` | Show version number and exit |

### Example

```sh
doc2anki --version
doc2anki -v
```

---

## doc2anki list

List AI providers from the configuration file.

### Syntax

```sh
doc2anki list [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `-c, --config PATH` | Configuration file path |
| `--all` | Show all providers (including disabled) |

### Output

Displays a rich table with:
- Name
- Status (enabled/disabled)
- Auth Type
- Model
- Base URL

### Examples

```sh
# List enabled providers
doc2anki list

# List all providers
doc2anki list --all

# Use specific config file
doc2anki list -c /path/to/config.toml
```

---

## doc2anki validate

Validate configuration file correctness and test provider connectivity.

### Syntax

```sh
doc2anki validate [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `-c, --config PATH` | Configuration file path |
| `-p, --provider NAME` | Validate specific provider only |

### Examples

```sh
# Validate all enabled providers
doc2anki validate

# Validate specific provider
doc2anki validate -p openai

# Use specific config file
doc2anki validate -c ~/.config/doc2anki/ai_providers.toml
```

---

## doc2anki generate

Generate Anki flashcards from documents.

### Syntax

```sh
doc2anki generate INPUT_PATH [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INPUT_PATH` | Input file or directory path |

### Basic Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output PATH` | `outputs/output.apkg` | Output .apkg file path |
| `-p, --provider NAME` | (required) | AI provider name |
| `-c, --config PATH` | (auto-detect) | Configuration file path |
| `--prompt-template PATH` | (built-in) | Custom Jinja2 prompt template path |
| `--dry-run` | false | Parse and chunk only, skip LLM calls |
| `--verbose` | false | Show detailed output |

### Chunking Options

| Option | Default | Description |
|--------|---------|-------------|
| `--max-tokens N` | 3000 | Maximum tokens per chunk |
| `--max-retries N` | 3 | LLM API max retry attempts |
| `--include-parent-chain` | true | Include heading hierarchy in prompts |
| `--no-parent-chain` | - | Disable heading hierarchy (negates above) |

### Interactive Mode Options

| Option | Default | Description |
|--------|---------|-------------|
| `-I, --interactive` | false | Enable interactive chunk classification |

### Card Organization Options

| Option | Default | Description |
|--------|---------|-------------|
| `--deck-depth N` | 2 | Deck hierarchy depth from file path |
| `--extra-tags TAGS` | (none) | Additional tags, comma-separated |

### Examples

**Basic usage:**

```sh
# Process single file
doc2anki generate notes.md -p deepseek

# Process directory
doc2anki generate knowledge/ -p openai -o my_cards.apkg
```

**Chunking control:**

```sh
# Increase token limit per chunk
doc2anki generate notes.md -p deepseek --max-tokens 4000

# Disable heading hierarchy context
doc2anki generate notes.md -p deepseek --no-parent-chain
```

**Interactive mode:**

```sh
# Classify each section interactively
doc2anki generate notes.md -p openai --interactive
```

**Debugging and testing:**

```sh
# Dry run - parse only, no LLM calls
doc2anki generate notes.md --dry-run

# Verbose output
doc2anki generate notes.md -p deepseek --verbose

# Combine both
doc2anki generate notes.md --dry-run --verbose
```

**Card organization:**

```sh
# Set deck hierarchy depth to 3
doc2anki generate knowledge/ -p openai --deck-depth 3

# Add extra tags
doc2anki generate notes.md -p deepseek --extra-tags "study,exam,2024"
```

**Custom prompt template:**

```sh
doc2anki generate notes.md -p openai --prompt-template ./my_template.j2
```

---

## Interactive Mode

When using `-I` or `--interactive`, doc2anki presents an interactive session for classifying document sections.

### Session Overview

```
Processing: input.md

Found 5 sections at level 2:
┌───┬──────────────────────────┬────────┐
│ # │ Section                  │ Tokens │
├───┼──────────────────────────┼────────┤
│ 1 │ ## TCP Basics            │ 1200   │
│ 2 │ ## UDP Overview          │ 800    │
│ 3 │ ## Network Layers        │ 2000   │
│ 4 │ ## History               │ 500    │
│ 5 │ ## Summary               │ 200    │
└───┴──────────────────────────┴────────┘

Classification options:
  [F] Full - Generate cards + add to context
  [C] Card only - Generate cards (default)
  [X] Context only - Add to context, skip cards
  [S] Skip - Ignore completely

Section 1 "TCP Basics" [F/C/X/S] (default: C): _
```

### Classification Types

| Type | Cards | Context | Use Case |
|------|-------|---------|----------|
| **F** (Full) | Yes | Yes | Fundamental concepts, definitions |
| **C** (Card-only) | Yes | No | Independent knowledge points |
| **X** (Context-only) | No | Yes | Background info, prerequisites |
| **S** (Skip) | No | No | Irrelevant content |

### Interactive Commands

| Command | Description |
|---------|-------------|
| `f` | Classify current section as Full |
| `c` | Classify current section as Card-only |
| `x` | Classify current section as Context-only |
| `s` | Classify current section as Skip |
| `p` or `preview` | Preview current section content |
| `all:F` | Classify all remaining as Full |
| `all:C` | Classify all remaining as Card-only |
| `all:X` | Classify all remaining as Context-only |
| `all:S` | Skip all remaining sections |
| `reset` | Reset all classifications |
| `done` | Finish (remaining sections use default) |

### Context Accumulation Warning

Selecting **Full** or **Context-only** adds content to subsequent LLM calls, which:
- Increases token consumption (potentially O(N²) for N chunks)
- May reduce card quality as context grows
- Can hit context window limits

The interactive session displays accumulated token count when using these options.

---

## Automatic Chunk Level Detection

When no `--chunk-level` is specified, doc2anki automatically selects the optimal heading level:

1. Iterates through heading levels 1-6
2. Calculates average chunk size and variance for each level
3. Selects level satisfying:
   - At least 2 chunks produced
   - Average chunk size between 500-2500 tokens
   - Size distribution is uniform (std_dev < 50% of mean)

Use `--verbose` to see the selected level:

```sh
doc2anki generate notes.md -p deepseek --dry-run --verbose
```

---

## Heading Hierarchy Context

By default (`--include-parent-chain`), each chunk's prompt includes its document location:

```markdown
## Content Location
Current content's position in document: Network Basics > TCP/IP > Three-Way Handshake
```

This helps the LLM understand context and generate more accurate cards.

Disable with `--no-parent-chain` for flat documents or when headings lack hierarchical meaning:

```sh
doc2anki generate notes.md -p deepseek --no-parent-chain
```

---

## Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Error (configuration, parsing, LLM call failure, etc.) |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `XDG_CONFIG_HOME` | User config directory (default: `~/.config`) |
| Provider API key variables | e.g., `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` |

---

## Configuration File Resolution

doc2anki searches for `ai_providers.toml` in order:

1. Path specified via `--config`
2. `./config/ai_providers.toml` (current directory)
3. `~/.config/doc2anki/ai_providers.toml` (XDG config)

See [configuration.md](configuration.md) for detailed configuration options.
