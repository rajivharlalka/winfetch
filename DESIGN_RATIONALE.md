# Design Rationale: Auto-Detect Source + Explicit Target

## The Design Decision

The tool now requires users to **explicitly specify the target format** while **automatically detecting the source format**.

```bash
# You specify WHAT you want, tool detects WHAT you have
session-convert convert input.jsonl --to codex -o output.jsonl
```

## Why This Design?

### 1. Extensibility 🚀

**The Primary Goal**: Make it easy to add new formats in the future.

With explicit `--to`, adding new formats is trivial:

```python
# Future: Just add to the list!
@click.option('--to', type=click.Choice([
    'claude',
    'codex',
    'cursor',     # Future
    'aider',      # Future
    'markdown',   # Future
    'html',       # Future
]))
```

**Without explicit target**, you'd need complex logic:
- "If source is Claude, convert to... which one? Codex? Cursor? Aider?"
- Ambiguity when multiple target formats exist
- Need default rules that may not match user intent

### 2. Clear Intent 🎯

Users explicitly state what they want:

```bash
# Crystal clear - I want Codex output
session-convert convert input.jsonl --to codex -o output.jsonl

# Crystal clear - I want Claude output  
session-convert convert input.jsonl --to claude -o output.jsonl
```

**No guessing, no ambiguity, no surprises.**

### 3. Future Scenarios

#### Scenario 1: Multiple Target Formats

When we add Cursor format:

```bash
# User decides which format they want
session-convert convert claude-session.jsonl --to cursor -o output.jsonl
session-convert convert claude-session.jsonl --to codex -o output.jsonl
session-convert convert claude-session.jsonl --to aider -o output.jsonl
```

Without explicit target, how would the tool know which one to choose?

#### Scenario 2: Export Formats

When we add export formats:

```bash
# Export to markdown report
session-convert convert session.jsonl --to markdown -o report.md

# Export to HTML
session-convert convert session.jsonl --to html -o report.html

# Export to JSON (generic)
session-convert convert session.jsonl --to json -o generic.json
```

Explicit `--to` makes all this possible without complex guessing logic.

## What We Gain

### ✅ Convenience (Auto-Detect Source)

Users don't need to know their input format:

```bash
# Is it Claude or Codex? Don't know? Don't care!
session-convert convert mystery-session.jsonl --to codex -o output.jsonl
```

The tool figures it out automatically. ✨

### ✅ Clarity (Explicit Target)

Users always know what they'll get:

```bash
# I want Codex → I get Codex
session-convert convert input.jsonl --to codex -o output.jsonl

# I want Claude → I get Claude
session-convert convert input.jsonl --to claude -o output.jsonl
```

### ✅ Extensibility (Ready for More)

Adding new formats is straightforward:

1. Add format to `--to` choices
2. Implement emitter for new format
3. Done!

No need to modify auto-selection logic or add complex rules.

### ✅ Safety (No Accidents)

Can't accidentally get the wrong output:

```bash
# Explicit: I want Codex, I get Codex
session-convert convert input.jsonl --to codex -o output.jsonl

# No auto-guessing that might be wrong
```

## Alternative Designs Considered

### Alternative 1: Auto-Detect Both

```bash
# Auto-detect source AND target
session-convert convert input.jsonl -o output.jsonl
```

**Problems:**
- ❌ Ambiguous when >2 formats exist
- ❌ User doesn't control output format
- ❌ Not extensible (how to choose among Cursor, Aider, Codex?)
- ❌ Need complex default rules

### Alternative 2: Explicit Both

```bash
# Explicit source AND target
session-convert convert input.jsonl --from claude --to codex -o output.jsonl
```

**Problems:**
- ❌ More typing required
- ❌ User must know source format (inconvenient)
- ❌ Defeats the purpose of smart detection

### Our Design: Auto Source + Explicit Target ✅

```bash
# Best of both worlds
session-convert convert input.jsonl --to codex -o output.jsonl
```

**Advantages:**
- ✅ Convenient (auto-detect source)
- ✅ Clear (explicit target)
- ✅ Extensible (ready for new formats)
- ✅ Safe (no ambiguity)

## Real-World Usage Examples

### Example 1: Don't Know Source Format

```bash
# Found an old session file, not sure if it's Claude or Codex
session-convert convert old-session.jsonl --to codex -o converted.jsonl

# Tool detects source automatically, converts to Codex as requested
```

### Example 2: Multiple Conversions

```bash
# Convert same source to different targets (future)
session-convert convert session.jsonl --to codex -o session-codex.jsonl
session-convert convert session.jsonl --to cursor -o session-cursor.jsonl
session-convert convert session.jsonl --to markdown -o session-report.md
```

Clear which output you get from each command!

### Example 3: Batch Processing

```bash
# Process directory, explicit target
session-convert batch ~/sessions/ ~/converted/ \
  --from claude \
  --to codex
```

Clear intent: converting TO Codex.

## Implementation Benefits

### For Developers

Adding new formats is straightforward:

```python
# 1. Add to CLI choices
@click.option('--to', type=click.Choice(['claude', 'codex', 'cursor']))

# 2. Add emitter
class CursorEmitter:
    def emit(self, session: Session) -> List[Dict]:
        # Convert to Cursor format
        pass

# 3. Add to conversion logic
if target_format == 'cursor':
    emitter = CursorEmitter()

# Done!
```

### For Users

Clear and predictable:

```bash
# What I specify is what I get
session-convert convert input.jsonl --to <what-I-want> -o output.jsonl
```

### For Maintenance

- No complex auto-selection logic to maintain
- Each format addition is isolated
- Easy to test (explicit inputs/outputs)
- Clear error messages

## Comparison Table

| Aspect | Auto Both | Explicit Both | **Auto Source + Explicit Target** |
|--------|-----------|---------------|-----------------------------------|
| **Convenience** | ✅ High | ❌ Low | ✅ High |
| **Clarity** | ❌ Low | ✅ High | ✅ High |
| **Extensibility** | ❌ Poor | ⚠️ OK | ✅ Excellent |
| **User Control** | ❌ Low | ✅ High | ✅ High |
| **Typing Required** | ✅ Minimal | ❌ Maximum | ✅ Minimal |
| **Ambiguity** | ❌ High | ✅ None | ✅ None |
| **Future-Proof** | ❌ No | ⚠️ OK | ✅ Yes |

## User Feedback Incorporated

> "The tool should be able to understand the underlying agent codex or claude code by itself."

✅ **Implemented**: Tool auto-detects source format.

> "But output format should always be specified. This enables extension to different more tools."

✅ **Implemented**: User must explicitly specify `--to` parameter.

**Perfect balance achieved!**

## Future Vision

With this design, future additions are straightforward:

```bash
# Today
session-convert convert input.jsonl --to codex -o output.jsonl
session-convert convert input.jsonl --to claude -o output.jsonl

# Tomorrow (future formats)
session-convert convert input.jsonl --to cursor -o output.jsonl
session-convert convert input.jsonl --to aider -o output.jsonl
session-convert convert input.jsonl --to markdown -o report.md
session-convert convert input.jsonl --to html -o report.html
session-convert convert input.jsonl --to json -o generic.json

# Even export to diagrams!
session-convert convert input.jsonl --to mermaid -o diagram.mmd
session-convert convert input.jsonl --to graphviz -o flow.dot
```

All possible with the same clean interface!

## Summary

**Design principle:**
- **Auto-detect source** = User convenience (don't need to know what you have)
- **Explicit target** = User control + Extensibility (specify what you want)

**Usage:**
```bash
session-convert convert input.jsonl --to <target-format> -o output.jsonl
```

**Result:**
- ✅ Convenient to use
- ✅ Clear about output
- ✅ Easy to extend
- ✅ Future-proof design

**This design makes the tool both user-friendly AND maintainable for future growth!** 🎉
