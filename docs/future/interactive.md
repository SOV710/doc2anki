# Interactive Mode

Interactive mode provides fine-grained control over how doc2anki processes each section of your document.

## Overview

By default, doc2anki treats all document sections as independent knowledge points (`CARD_ONLY`). Interactive mode lets you classify each section individually, controlling whether it generates cards, contributes to context for subsequent sections, or both.

## Usage

Enable interactive mode with the `-I` or `--interactive` flag:

```sh
doc2anki generate input.md -p provider --interactive
```

## Classification Types

| Type | Generate Cards | Add to Context | Use Case |
|------|----------------|----------------|----------|
| `FULL` | Yes | Yes | Fundamental concepts (definitions, axioms) |
| `CARD_ONLY` | Yes | No | Independent knowledge points (default) |
| `CONTEXT_ONLY` | No | Yes | Background info (history, motivation) |
| `SKIP` | No | No | Irrelevant content (filler text) |

## Session Interface

When you run interactive mode, doc2anki displays a section overview:

```
Processing: input.md

Found 5 sections at level 2:
┌───┬──────────────────────────┬────────┐
│ # │ Section                  │ Tokens │
├───┼──────────────────────────┼────────┤
│ 1 │ ## TCP Basics            │ 1200   │
│ 2 │ ## UDP Overview          │ 800    │
│ 3 │ ## Network Layers        │ 2000   │
│ 4 │ ## History and Motivation│ 500    │
│ 5 │ ## Summary               │ 200    │
└───┴──────────────────────────┴────────┘

⚠ Warning: Section 3 exceeds 2000 tokens

Classification options:
  [F] Full - Generate cards + add to context
  [C] Card only - Generate cards (default)
  [X] Context only - Add to context, skip cards
  [S] Skip - Ignore completely

Section 1 "TCP Basics" [F/C/X/S] (default: C): _
```

## Commands

### Single Section Classification

| Command | Description |
|---------|-------------|
| `f` | Classify current section as Full |
| `c` | Classify current section as Card-only |
| `x` | Classify current section as Context-only |
| `s` | Classify current section as Skip |

### Batch Commands

| Command | Description |
|---------|-------------|
| `all:F` | Classify all remaining as Full |
| `all:C` | Classify all remaining as Card-only |
| `all:X` | Classify all remaining as Context-only |
| `all:S` | Skip all remaining sections |

### Navigation Commands

| Command | Description |
|---------|-------------|
| `p` or `preview` | Preview current section content |
| `reset` | Reset all classifications and start over |
| `done` | Finish (remaining sections use default Card-only) |

## Context Accumulation Warning

**"Add to Context" means:** Appending the current section's raw text to all subsequent API calls.

### Risks

- **Token cost explosion**: For N chunks, total consumption becomes O(N²) instead of O(N)
- **Effectiveness degradation**: Longer context reduces LLM attention on current content
- **Context window limits**: May exceed limits for documents with 10+ sections

### Cost Display

When you classify a section as `FULL` or `CONTEXT_ONLY`, the session displays token information:

```
Section 1 "TCP Basics" [F/C/X/S] (default: C): f
✓ Classified as FULL (1200 tokens added to context)
Accumulated context: 1200 tokens

Section 2 "UDP Overview" [F/C/X/S] (default: C): _
```

### Design Decision

- `FULL` and `CONTEXT_ONLY` are **not defaults** by design
- Users selecting these types explicitly accept the associated costs
- For most use cases, `CARD_ONLY` (default) produces better results

## Best Practices

### When to Use FULL

- Definitions that subsequent sections reference
- Core concepts that provide necessary context
- Axioms or premises that later content builds upon

### When to Use CONTEXT_ONLY

- Historical background that provides motivation
- Prerequisites readers need to understand
- Setup or configuration sections

### When to Use SKIP

- Table of contents or navigation sections
- Appendices or references
- Auto-generated content

## Implementation Details

### Data Flow

```python
@dataclass
class InteractiveSession:
    tree: DocumentTree
    nodes: list[HeadingNode]
    classified: list[ClassifiedNode]
    current_index: int
    accumulated_tokens: int

    def classify_current(self, chunk_type: ChunkType) -> int:
        """Returns token count added to context."""

    def is_complete(self) -> bool:
        return self.current_index >= len(self.nodes)
```

### Processing Flow

1. Build document tree from input
2. Detect optimal heading level for chunking
3. Present sections to user for classification
4. Process classified sections through pipeline
5. Generate cards only for `FULL`/`CARD_ONLY` sections
6. Accumulate context only from `FULL`/`CONTEXT_ONLY` sections

## Future Enhancements

The following enhancements are planned for future versions:

1. **Configuration Presets**: Save classification patterns for reuse across similar documents
2. **Pattern Matching**: Classify by heading pattern (e.g., "skip all 'Summary' sections")
3. **LLM-Assisted Classification**: Use LLM to suggest chunk types based on content analysis
4. **Undo/Redo**: Allow correcting previous classifications during the session
5. **Export Classifications**: Save classification decisions to a file for reproducibility
