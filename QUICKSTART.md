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
# Inspect a Claude Code session
session-convert info examples/claude_session.jsonl

# Inspect a Codex CLI session  
session-convert info examples/codex_session.jsonl
```

### 2. Validate Sessions

```bash
# Validate a Claude session
session-convert validate examples/claude_session.jsonl --format claude

# Validate a Codex session
session-convert validate examples/codex_session.jsonl --format codex

# Auto-detect format
session-convert validate examples/claude_session.jsonl
```

### 3. Convert Sessions

#### Claude → Codex

```bash
session-convert claude-to-codex \
  examples/claude_session.jsonl \
  -o output_codex.jsonl \
  --stats
```

#### Codex → Claude

```bash
session-convert codex-to-claude \
  examples/codex_session.jsonl \
  -o output_claude.jsonl \
  --stats
```

### 4. Batch Convert

```bash
# Convert all Claude sessions in a directory
session-convert batch \
  ~/my-claude-sessions/ \
  ~/converted-to-codex/ \
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

# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=session_converter --cov-report=html
```

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

## Working with Real Sessions

### Your Claude Code Sessions

Claude Code stores sessions at:
```
~/.claude/projects/<encoded-path>/<session-uuid>.jsonl
```

Example:
```bash
# Find your sessions
ls ~/.claude/projects/

# Convert one
session-convert claude-to-codex \
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
# Find recent sessions
ls ~/.codex/sessions/2026/07/

# Convert one
session-convert codex-to-claude \
  ~/.codex/sessions/2026/07/09/rollout-*.jsonl \
  -o ~/converted/my-session.jsonl \
  --stats
```

## Common Tasks

### Validate Before Converting

```bash
# Always validate first
session-convert validate my-session.jsonl --format claude

# Then convert
session-convert claude-to-codex my-session.jsonl -o output.jsonl
```

### Pretty Print Output

```bash
# Use --pretty for human-readable output
session-convert claude-to-codex input.jsonl -o output.jsonl --pretty
```

### View Detailed Statistics

```bash
# Use --stats to see conversion details
session-convert claude-to-codex input.jsonl -o output.jsonl --stats
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

## Round-Trip Validation

Verify data integrity with round-trip conversion:

```bash
# Original
session-convert info examples/claude_session.jsonl

# Convert: Claude → Codex
session-convert claude-to-codex examples/claude_session.jsonl -o step1.jsonl

# Convert back: Codex → Claude
session-convert codex-to-claude step1.jsonl -o step2.jsonl

# Compare
session-convert info step2.jsonl

# Session ID should match the original
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

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -e .
```

### Invalid Session Format

```bash
# Check the format
file my-session.jsonl

# Validate with explicit format
session-convert validate my-session.jsonl --format claude
```

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Check [VALIDATION.md](VALIDATION.md) for detailed validation strategies
- Review [DESIGN.md](DESIGN.md) to understand the architecture
- Run `session-convert --help` for all command options

## Need Help?

- 📖 [Full Documentation](README.md)
- 🧪 [Validation Guide](VALIDATION.md)
- 🏗️ [Architecture Details](DESIGN.md)
- 🐛 [Report Issues](https://github.com/yourusername/session-converter/issues)
