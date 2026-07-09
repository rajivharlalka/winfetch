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

The easiest way to convert sessions - just use `convert` and let the tool figure out the format!

```bash
# Auto-detect format and convert
session-convert convert my-session.jsonl -o converted.jsonl

# With statistics
session-convert convert my-session.jsonl -o converted.jsonl --stats

# With verbose output (shows detected format)
session-convert convert my-session.jsonl -o converted.jsonl -v
```

The tool will:
1. 🔍 Automatically detect if your input is Claude Code or Codex CLI format
2. 🔄 Convert to the opposite format
3. ✅ Validate the output

### 3. Specify Target Format (Optional)

If you want to explicitly specify the output format:

```bash
# Force conversion to Codex
session-convert convert my-session.jsonl --to codex -o output.jsonl

# Force conversion to Claude
session-convert convert my-session.jsonl --to claude -o output.jsonl
```

### 4. Validate Sessions

```bash
# Validate any session (format auto-detected)
session-convert validate my-session.jsonl

# Or specify format explicitly
session-convert validate my-session.jsonl --format claude
```

### 5. Explicit Format Conversion

If you prefer to be explicit about the conversion direction:

```bash
# Claude → Codex
session-convert claude-to-codex input.jsonl -o output.jsonl

# Codex → Claude
session-convert codex-to-claude input.jsonl -o output.jsonl
```

## Examples

### Example 1: Quick Convert (Auto-Detection)

```bash
# Just convert - the tool figures out the rest!
session-convert convert examples/claude_session.jsonl -o /tmp/output.jsonl --stats
```

Output:
```
Detected format: Claude
Target format: Codex
✓ Conversion complete
  Session ID: session-123
  Turns: 8
  Tool calls: 15
```

### Example 2: Convert Your Own Sessions

```bash
# Find your Claude sessions
ls ~/.claude/projects/

# Convert one (auto-detection)
session-convert convert \
  ~/.claude/projects/my-project/session-abc.jsonl \
  -o ~/converted/session-abc.jsonl \
  --stats
```

### Example 3: Batch Convert with Auto-Detection

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
# Run the demo script
bash scripts/demo_validation.sh
```

### Run Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests (including auto-detection tests)
pytest tests/ -v
```

Expected: **22/22 tests pass** ✅

### Automated Validation

```bash
# Run comprehensive validation
python3 scripts/validate_converter.py
```

Expected output:
```
✓ CLI Help - PASS
✓ Example Files - PASS  
✓ Info Command - PASS
✓ Validate Command - PASS
✓ Claude → Codex - PASS
✓ Codex → Claude - PASS
✓ Round-trip (Claude) - PASS
✓ Round-trip (Codex) - PASS

Pass Rate: 100.0%
```

## How Auto-Detection Works

The tool examines the first few lines of your session file and looks for format-specific indicators:

**Claude Code indicators:**
- `uuid` and `parentUuid` fields
- `sessionId` field
- Event types: `user`, `assistant`, `system`
- `message.content` structure
- `gitBranch` field

**Codex CLI indicators:**
- `session_meta` event type (strong indicator)
- `payload` structure
- Event types: `turn_context`, `response_item`, `input_item`
- `originator` and `cli_version` fields

The detection algorithm uses a confidence scoring system to determine the format.

## Working with Real Sessions

### Your Claude Code Sessions

Claude Code stores sessions at:
```
~/.claude/projects/<encoded-path>/<session-uuid>.jsonl
```

Example:
```bash
# Auto-detect and convert
session-convert convert \
  ~/.claude/projects/my-project/abc-123.jsonl \
  -o ~/converted/my-session.jsonl \
  --stats
```

### Your Codex CLI Sessions

Codex CLI stores sessions at:
```
~/.codex/sessions/YYYY/MM/DD/rollout-{timestamp}-{uuid}.jsonl
```

Example:
```bash
# Auto-detect and convert
session-convert convert \
  ~/.codex/sessions/2026/07/09/rollout-*.jsonl \
  -o ~/converted/my-session.jsonl \
  --stats
```

## Common Tasks

### Validate Before Converting

```bash
# Validate (format auto-detected)
session-convert validate my-session.jsonl

# Then convert (format auto-detected)
session-convert convert my-session.jsonl -o output.jsonl
```

### Pretty Print Output

```bash
# Use --pretty for human-readable output
session-convert convert input.jsonl -o output.jsonl --pretty
```

### View Detailed Statistics

```bash
# Use --stats to see conversion details
session-convert convert input.jsonl -o output.jsonl --stats
```

### Batch Process with Error Handling

```bash
# Continue even if some files fail
session-convert batch \
  input-dir/ \
  output-dir/ \
  --from claude \
  --to codex \
  --continue-on-error
```

## Troubleshooting

### Command Not Found

If `session-convert` command is not found:

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or use python module directly
python3 -m session_converter.cli --help
```

### Format Not Detected

If auto-detection fails:

```bash
# Use explicit conversion commands
session-convert claude-to-codex input.jsonl -o output.jsonl
# or
session-convert codex-to-claude input.jsonl -o output.jsonl
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -e .
```

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Check [VALIDATION.md](VALIDATION.md) for detailed validation strategies
- Review [DESIGN.md](DESIGN.md) to understand the architecture
- Run `session-convert convert --help` for all command options

## Need Help?

- 📖 [Full Documentation](README.md)
- 🧪 [Validation Guide](VALIDATION.md)
- 🏗️ [Architecture Details](DESIGN.md)
- 🐛 [Report Issues](https://github.com/yourusername/session-converter/issues)
