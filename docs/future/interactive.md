# Interactive Mode Specification

This document describes the planned interactive mode for doc2anki, which allows users to classify each chunk individually during the generation process.

## Overview

Currently, all chunks are classified as `CARD_ONLY` (generate cards, no context accumulation). The interactive mode will allow users to classify each chunk as one of four types:

| Type | Generate Cards | Add to Context | Use Case |
|------|----------------|----------------|----------|
| `FULL` | Yes | Yes | Fundamental concepts (definitions, axioms) |
| `CARD_ONLY` | Yes | No | Independent knowledge points (current default) |
| `CONTEXT_ONLY` | No | Yes | Background info (history, motivation) |
| `SKIP` | No | No | Irrelevant content (filler text) |

## Warning: Context Accumulation Cost

**"Add to Context" means:**
Appending the current chunk's raw text to all subsequent API calls (simple string concatenation).

**Drawbacks:**
- **Token cost explosion**: N chunks → O(N²) total token consumption instead of O(N)
- **Effectiveness degradation**: Longer context = less attention on current content
- **Context window limits**: Exceeds limits for documents with 10+ chunks

**Design decision:**
- `FULL` and `CONTEXT_ONLY` are **not defaults**
- Users selecting these types **assume the cost and effectiveness risks**

## CLI Interface

```
doc2anki generate input.md -p provider --interactive
```

### Interactive Session Flow

```
Processing: input.md

Found 5 sections at level 2:
  [1] ## TCP Basics (1200 tokens)
  [2] ## UDP Overview (800 tokens)
  [3] ## Network Layers (2000 tokens)
  [4] ## History and Motivation (500 tokens)
  [5] ## Summary (200 tokens)

Classification options:
  [F] Full - Generate cards + add to context
  [C] Card only - Generate cards (default)
  [X] Context only - Add to context, skip cards
  [S] Skip - Ignore completely

Section 1 "TCP Basics" [F/C/X/S] (default: C): _
```

### Batch Commands

- `all:C` - Classify all remaining as CARD_ONLY
- `all:S` - Skip all remaining
- `reset` - Restart classification
- `preview N` - Preview chunk N content
- `done` - Start generation with current classifications

## Implementation Notes

### Data Flow

```python
@dataclass
class InteractiveSession:
    tree: DocumentTree
    classified: list[ClassifiedNode]
    current_index: int

    def classify_current(self, chunk_type: ChunkType) -> None:
        self.classified[self.current_index].chunk_type = chunk_type
        self.current_index += 1

    def is_complete(self) -> bool:
        return self.current_index >= len(self.classified)
```

### UI Considerations

- Use `rich` for styled terminal output
- Show token count for each section
- Highlight large sections (> 2000 tokens)
- Provide progress indicator
- Support keyboard shortcuts

### Future Enhancements

1. **Config file presets**: Save classification patterns for reuse
2. **Pattern matching**: Classify by heading pattern (e.g., "skip all 'Summary' sections")
3. **LLM-assisted classification**: Use LLM to suggest chunk types based on content
4. **Undo/redo**: Allow correcting previous classifications

## Files to Modify

| File | Changes |
|------|---------|
| `src/doc2anki/cli.py` | Add `--interactive` flag |
| `src/doc2anki/pipeline/interactive.py` | New: Interactive session handler |
| `src/doc2anki/pipeline/processor.py` | Accept pre-classified nodes |

## Priority

Medium - Not required for v1.0, but valuable for power users who want fine-grained control over card generation.
