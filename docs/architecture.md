# System Architecture

## Data Flow Overview

```
Input Document (.md/.org)
       │
       ▼
┌─────────────┐
│   Parser    │  Parse document, extract metadata
└─────────────┘
       │
       ▼
┌─────────────┐
│ Tree Builder│  Build immutable AST (HeadingNode tree)
└─────────────┘
       │
       ▼
┌─────────────┐
│  Pipeline   │  Chunking, classification, context management
└─────────────┘
       │
       ▼
┌─────────────┐
│  LLM Client │  Generate cards via AI
└─────────────┘
       │
       ▼
┌─────────────┐
│   Output    │  Create Anki .apkg file
└─────────────┘
```

## Module Responsibilities

### Parser Module (`src/doc2anki/parser/`)

Responsible for parsing Markdown and Org-mode documents into an abstract syntax tree.

**Core Components:**

| File | Responsibility |
|------|----------------|
| `tree.py` | Immutable AST data structures: `HeadingNode`, `DocumentTree`, `DocumentMetadata` |
| `markdown.py` | tree-sitter based Markdown parser with YAML frontmatter support |
| `orgmode.py` | orgparse-based Org-mode parser with keyword/property extraction |
| `chunker.py` | Token-aware chunking logic using tiktoken |

**AST Structure:**

```python
@dataclass(frozen=True)
class HeadingNode:
    level: int                          # Heading level (1-6)
    title: str                          # Heading text
    content: str                        # Direct content (excludes children)
    children: tuple[HeadingNode, ...]   # Child nodes (immutable)
    parent_titles: tuple[str, ...]      # Ancestor titles for context

    @property
    def full_content(self) -> str:
        """Complete content including all descendants."""

    @property
    def own_text(self) -> str:
        """Only this node's heading + content (no children)."""

    @property
    def path(self) -> tuple[str, ...]:
        """Full hierarchy as tuple of titles."""

@dataclass(frozen=True)
class DocumentTree:
    children: tuple[HeadingNode, ...]   # Top-level headings
    preamble: str                       # Content before first heading
    metadata: DocumentMetadata          # Document-level metadata
    source_format: str                  # "markdown" or "org"

    def get_nodes_at_level(self, level: int) -> list[HeadingNode]:
        """Get all nodes at specified heading level."""

    def get_all_levels(self) -> frozenset[int]:
        """Returns all heading levels present in document."""
```

**Immutability & Structural Sharing:**

All AST nodes use frozen dataclasses, enabling:
- Safe concurrent access
- Potential undo/redo functionality
- `with_children()` method for efficient tree modifications

### Pipeline Module (`src/doc2anki/pipeline/`)

Handles document chunking, section classification, and context management.

**Core Components:**

| File | Responsibility |
|------|----------------|
| `classifier.py` | Defines `ChunkType` enum and `ClassifiedNode` dataclass |
| `context.py` | Defines `ChunkWithContext` for LLM prompt building |
| `processor.py` | Main processing logic and auto-detection algorithm |
| `interactive.py` | Interactive classification session handler |

**Chunk Type Classification (2x2 Matrix):**

```
                │ Add to Context │ Don't Add
────────────────┼────────────────┼───────────
Generate Cards  │ FULL           │ CARD_ONLY ← default
Don't Generate  │ CONTEXT_ONLY   │ SKIP
```

| Type | Cards | Context | Use Case |
|------|-------|---------|----------|
| `FULL` | Yes | Yes | Fundamental concepts, definitions, axioms |
| `CARD_ONLY` | Yes | No | Independent knowledge points (v1 default) |
| `CONTEXT_ONLY` | No | Yes | Background info, historical motivation |
| `SKIP` | No | No | Irrelevant content, filler text |

**Auto-Detection Algorithm:**

```python
def auto_detect_level(tree: DocumentTree, max_tokens: int) -> int:
    """
    Pure local heuristic algorithm - zero API cost.

    Strategy:
    1. Iterate through heading levels (1-6)
    2. Calculate node count and average token count per level
    3. Check variance - if too high, go deeper
    4. Select level satisfying:
       - At least 2 chunks
       - Average chunk size between 500-2500 tokens
       - Uniform distribution (std_dev < 50% of mean)
    """
```

**Processing Modes:**

1. **Automatic Mode** (default):
   - Flattens tree to linear sequence of `ContentBlock`
   - Greedily chunks to fit token limits
   - All chunks treated as `CARD_ONLY`

2. **Interactive Mode** (`--interactive`):
   - Uses pre-classified nodes from interactive session
   - Respects user-specified chunk types
   - Uses `own_text` semantics (independent classification)

### LLM Module (`src/doc2anki/llm/`)

Handles interaction with AI services.

**Core Components:**

| File | Responsibility |
|------|----------------|
| `client.py` | OpenAI-compatible client with retry logic |
| `prompt.py` | Jinja2 template rendering |
| `extractor.py` | JSON extraction from LLM responses |

**Client Features:**

- Creates OpenAI SDK client with custom base URLs
- Automatic JSON mode fallback if provider doesn't support `response_format`
- Configurable retry logic with max attempts
- Default max_tokens: 8192

**Template Loading:**

Uses `importlib.resources` for package resource loading, supporting pip-installed usage:

```python
class PackageLoader(BaseLoader):
    """Load templates from Python package resources."""
    def get_source(self, environment, template):
        files = importlib.resources.files(self.package)
        source = (files / template).read_text(encoding="utf-8")
        return source, template, lambda: True
```

**JSON Extraction Strategies:**

1. Direct parse (response is pure JSON)
2. Extract from `` ```json ... ``` `` code block
3. Find content between first `{` and last `}`

### Config Module (`src/doc2anki/config/`)

Manages configuration loading and validation.

**Configuration Resolution Chain:**

1. CLI `--config` parameter
2. `./config/ai_providers.toml`
3. `~/.config/doc2anki/ai_providers.toml`

**Authentication Types:**

| Type | `api_key` Meaning |
|------|-------------------|
| `direct` | The API key itself |
| `env` | Environment variable name |
| `dotenv` | Key name in .env file |

**Provider Config Model:**

```python
class ProviderConfig(BaseModel):
    base_url: str
    model: str
    api_key: str
```

### Models Module (`src/doc2anki/models/`)

Pydantic data models for card validation.

**Card Types:**

```python
class BasicCard(BaseModel):
    type: Literal["basic"]
    front: str              # 5-20000 chars
    back: str               # 1-20000 chars
    tags: List[str]         # Auto-normalized
    file_path: Optional[str]
    extra_tags: List[str]

class ClozeCard(BaseModel):
    type: Literal["cloze"]
    text: str               # 10-20000 chars, must contain {{cN::...}}
    tags: List[str]
    file_path: Optional[str]
    extra_tags: List[str]
```

**Tag Normalization:**

- Special characters `[&/\\:*?"<>|]` replaced with `_`
- All tags lowercased
- Supports comma/whitespace-separated strings or lists

**Cloze Validation:**

- Accepts: `{{cN::...}}` or `[CLOZE:cN:...]` format
- Automatically converts placeholders to Anki format

### Output Module (`src/doc2anki/output/`)

Generates Anki package files.

**Features:**

- Uses `genanki` library for .apkg creation
- Fixed model IDs for consistency: `BASIC_MODEL_ID = 1607392319`, `CLOZE_MODEL_ID = 1607392320`
- Automatic deck/tag generation from file paths
- Supports both basic Q&A and cloze deletion cards

**Path to Deck Conversion:**

```python
def path_to_deck_and_tags(file_path: str, deck_depth: int = 2) -> tuple[str, list[str]]:
    """
    Example:
    file_path = "computing/pl/c_cpp/gcc/linker.md"
    deck_depth = 2

    Returns:
    - deck_name = "computing::pl"
    - tags = ["computing", "pl", "c_cpp", "gcc", "linker"]
    """
```

## Context Accumulation Cost Warning

`FULL` and `CONTEXT_ONLY` types append content to subsequent API calls.

**Risks:**

- **Token cost explosion**: N chunks → O(N²) total consumption instead of O(N)
- **Effectiveness degradation**: Longer context = less attention on current content
- **Context window limits**: Exceeds limits for documents with 10+ chunks

**Design Decision:**

- v1 defaults all chunks to `CARD_ONLY` (independent processing, no accumulation)
- `FULL`/`CONTEXT_ONLY` only available through interactive mode with explicit user selection
- Users opting for context accumulation assume associated costs and effectiveness risks

## Token Counting

- Uses `tiktoken` with `cl100k_base` encoding
- Compatible with GPT-4, Claude, and similar models
- Applied to all content for chunking decisions
- Used in interactive mode to track accumulated context size

## Error Handling

| Error Type | Handling |
|------------|----------|
| Configuration errors | `ConfigError` with `fatal_exit()` |
| Chunking errors | `ChunkingError` for indivisible blocks exceeding limit |
| JSON extraction | `JSONExtractionError` with response preview |
| LLM API errors | Retry loop with configurable max attempts, then fatal exit |

