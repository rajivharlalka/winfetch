# Quick Start Guide

Get started with the Session Converter in 5 minutes!

## Installation

```bash
# Clone or navigate to the repository
cd session-converter

# Install the package
pip install -e .

# Verify installation
session-convert --version
```

## Basic Usage

### 1. View Session Information

```bash
# Inspect any session (format auto-detected)
session-convert info examples/claude_session.jsonl
session-convert info examples/codex_session.jsonl
```

### 2. Convert Sessions (Auto-Detection) ⭐ **RECOMMENDED**

The tool **auto-detects your source format** - you just specify where you want it to go!

```bash
# Convert to Codex (source auto-detected)
session-convert convert my-session.jsonl --to codex -o output.jsonl

# Convert to Claude (source auto-detected)
session-convert convert my-session.jsonl --to claude -o output.jsonl

# With statistics
session-convert convert my-session.jsonl --to codex -o output.jsonl --stats

# With verbose output (shows detected source)
session-convert convert my-session.jsonl --to codex -o output.jsonl -v
```

The tool will:
1. 🔍 Automatically detect your source format (Claude or Codex)
2. 🔄 Convert to your specified target format
3. ✅ Validate the output

### 3. Validate Sessions

```bash
# Validate any session (format auto-detected)
session-convert validate my-session.jsonl

# Or specify format explicitly
session-convert validate my-session.jsonl --format claude
```

### 4. Explicit Format Conversion

If you prefer to be explicit about both source and target:

```bash
# Claude → Codex
session-convert claude-to-codex input.jsonl -o output.jsonl

# Codex → Claude
session-convert codex-to-claude input.jsonl -o output.jsonl
```

## Why This Design?

### Smart Source Detection + Explicit Target = Best of Both Worlds

**You don't need to know your source format:**
```bash
# Is it Claude or Codex? Don't know? Don't care!
session-convert convert mystery-session.jsonl --to codex -o output.jsonl
# Tool figures it out automatically ✨
```

**But you must specify what you want:**
```bash
# Clear and explicit about the output
session-convert convert input.jsonl --to codex -o output.jsonl
```

**Benefits:**
- 🎯 **Clear intent**: You explicitly state what you want
- 🔍 **No guessing**: Source format auto-detected
- 🚀 **Extensible**: Ready for future formats (Cursor, Aider, etc.)
- 🛡️ **Safe**: Can't accidentally get the wrong output

## Examples

### Example 1: Quick Convert

```bash
# Convert to Codex (source auto-detected)
session-convert convert examples/claude_session.jsonl --to codex -o output.jsonl --stats
```

Output:
```
Detected source format: Claude
Converting to: Codex
✓ Conversion complete
  Session ID: session-123
  Turns: 8
  Tool calls: 15
```

### Example 2: Convert Your Own Sessions

```bash
# Find your Claude sessions
ls ~/.claude/projects/

# Convert one (source auto-detected, target explicit)
session-convert convert \
  ~/.claude/projects/my-project/session-abc.jsonl \
  --to codex \
  -o ~/converted/session-abc.jsonl \
  --stats
```

### Example 3: Batch Convert

```bash
# Convert all sessions in a directory
session-convert batch \
  ~/my-sessions/ \
  ~/converted/ \
  --from claude \
  --to codex \
  --stats
```

## Testing Your Installation

### Quick Test

```bash
# Test conversions
session-convert convert examples/claude_session.jsonl --to codex -o /tmp/test1.jsonl -v
session-convert convert examples/codex_session.jsonl --to claude -o /tmp/test2.jsonl -v
```

### Run Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/ -v
```

Expected: **22/22 tests pass** ✅

### Automated Validation

```bash
# Run comprehensive validation
python3 scripts/validate_converter.py
```

## How Auto-Detection Works

The tool examines your session file and looks for format-specific indicators:

**Claude Code indicators:**
- `uuid` and `parentUuid` fields
- `sessionId` field
- Event types: `user`, `assistant`, `system`
- `message.content` structure

**Codex CLI indicators:**
- `session_meta` event type (strong indicator)
- `payload` structure
- Event types: `turn_context`, `response_item`
- `originator` and `cli_version` fields

The detection algorithm uses confidence scoring to determine the format accurately.

## Working with Real Sessions

### Your Claude Code Sessions

```bash
# Convert to Codex
session-convert convert \
  ~/.claude/projects/my-project/abc-123.jsonl \
  --to codex \
  -o ~/converted/my-session.jsonl \
  --stats
```

### Your Codex CLI Sessions

```bash
# Convert to Claude
session-convert convert \
  ~/.codex/sessions/2026/07/09/rollout-*.jsonl \
  --to claude \
  -o ~/converted/my-session.jsonl \
  --stats
```

## Common Tasks

### Validate Before Converting

```bash
# Validate (format auto-detected)
session-convert validate my-session.jsonl

# Then convert with explicit target
session-convert convert my-session.jsonl --to codex -o output.jsonl
```

### Pretty Print Output

```bash
# Use --pretty for human-readable output
session-convert convert input.jsonl --to codex -o output.jsonl --pretty
```

### View Detailed Statistics

```bash
# Use --stats to see conversion details
session-convert convert input.jsonl --to codex -o output.jsonl --stats
```

## Future Extensibility

This design makes it easy to add new formats in the future:

```bash
# Future possibilities:
session-convert convert input.jsonl --to cursor -o output.jsonl
session-convert convert input.jsonl --to aider -o output.jsonl
session-convert convert input.jsonl --to markdown -o output.md
```

The `--to` parameter makes your intent explicit and allows unlimited target formats!

## Troubleshooting

### Missing --to Parameter

```bash
$ session-convert convert input.jsonl -o output.jsonl

Error: Missing option '--to'. Choose from: claude, codex
```

**Solution:** Always specify `--to`:
```bash
session-convert convert input.jsonl --to codex -o output.jsonl
```

### Format Not Detected

```bash
Error: Could not detect session format
```

**Solution:** Use explicit commands:
```bash
session-convert claude-to-codex input.jsonl -o output.jsonl
```

### Command Not Found

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Check [AUTO_DETECTION.md](AUTO_DETECTION.md) to understand how detection works
- Review [DESIGN.md](DESIGN.md) to understand the architecture
- Run `session-convert convert --help` for all options

## Command Reference

```bash
# Recommended: Auto-detect source + explicit target ⭐
session-convert convert <input> --to <codex|claude> -o <output>

# Explicit both directions
session-convert claude-to-codex <input> -o <output>
session-convert codex-to-claude <input> -o <output>

# Other commands
session-convert info <input>
session-convert validate <input>
session-convert batch <input-dir> <output-dir> --from <format> --to <format>
```

## Summary

✨ **The tool detects your source format automatically, but you specify the target explicitly.**

This design is:
- 🎯 **Clear**: You always know what you'll get
- 🔍 **Smart**: Source format auto-detected
- 🚀 **Extensible**: Ready for new formats

**Usage:**
```bash
session-convert convert my-session.jsonl --to codex -o output.jsonl
```

Simple, clear, and future-proof! 🎉
