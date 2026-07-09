# Session Converter

A powerful CLI tool to convert AI assistant sessions between Claude Code and OpenAI Codex CLI formats.

## Features

- 🤖 **Auto-Detection**: Automatically detects whether your session is Claude Code or Codex CLI format
- 🔄 **Bidirectional Conversion**: Convert sessions between Claude Code ↔ Codex CLI formats
- ✅ **Validation**: Validate session file formats
- 📊 **Statistics**: View detailed session information and conversion stats
- 🚀 **Batch Processing**: Convert entire directories of session files
- 🎯 **High Fidelity**: Preserves tool calls, thinking blocks, and metadata
- 🛡️ **Type Safe**: Built with Pydantic for robust schema validation

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/session-converter.git
cd session-converter

# Install dependencies
pip install -r requirements.txt

# Install the CLI tool
pip install -e .
```

## Quick Start

```bash
# Convert session (auto-detects format) - RECOMMENDED
session-convert convert input.jsonl -o output.jsonl

# Show session information
session-convert info input.jsonl

# Validate a session file
session-convert validate input.jsonl

# Batch convert a directory
session-convert batch ~/sessions/claude ~/sessions/codex --from claude --to codex

# Explicit format conversion (if needed)
session-convert claude-to-codex input.jsonl -o output.jsonl
session-convert codex-to-claude input.jsonl -o output.jsonl
```

## Usage

### Commands

#### `convert` (Recommended)
**Auto-detects format** and converts to the opposite format or specified target.

```bash
session-convert convert <input.jsonl> [OPTIONS]

Options:
  -o, --output PATH       Output file path (default: stdout)
  --to [claude|codex]    Target format (auto-detected if not specified)
  --pretty               Pretty-print JSON output
  --validate            Validate output after conversion
  --stats               Show conversion statistics
  -v, --verbose         Verbose logging
```

**Examples:**
```bash
# Auto-detect and convert (easiest way!)
session-convert convert my-session.jsonl -o converted.jsonl

# Auto-detect source, specify target
session-convert convert my-session.jsonl --to codex -o output.jsonl

# With verbose output showing detection
session-convert convert my-session.jsonl -o output.jsonl --stats -v
```

#### `claude-to-codex`
Explicitly convert Claude Code session to Codex CLI format.

```bash
session-convert claude-to-codex <input.jsonl> [OPTIONS]

Options:
  -o, --output PATH       Output file path (default: stdout)
  --pretty               Pretty-print JSON output
  --preserve-unknown     Keep unknown fields in output
  --validate            Validate output after conversion
  --stats               Show conversion statistics
  -v, --verbose         Verbose logging
```

#### `codex-to-claude`
Explicitly convert Codex CLI session to Claude Code format.

```bash
session-convert codex-to-claude <input.jsonl> [OPTIONS]
```

**Note:** Consider using `session-convert convert` for automatic format detection.

#### `info`
Display information about a session file.

```bash
session-convert info <input.jsonl>

Example output:
  Format: Claude Code
  Session ID: abc-123-def-456
  Turns: 15
  Tool calls: 42
  Events: 156
  Duration: 45m 23s
  Model: claude-sonnet-4.5
  CWD: /home/user/project
  Git Branch: main
```

#### `validate`
Validate a session file format.

```bash
session-convert validate <input.jsonl> --format <claude|codex>
```

#### `batch`
Batch convert multiple session files.

```bash
session-convert batch <input-dir> <output-dir> --from <claude|codex> --to <codex|claude>

Options:
  --pattern TEXT         Glob pattern for input files (default: *.jsonl)
  --recursive           Search subdirectories
  --continue-on-error   Continue processing if a file fails
```

## Session Format Details

### Claude Code Format
- **Location**: `~/.claude/projects/<encoded-path>/<session-uuid>.jsonl`
- **Structure**: JSONL with event types (user, assistant, system, progress)
- **Content Blocks**: text, tool_use, tool_result, thinking
- **Features**: UUID chains, compaction boundaries, git snapshots

### Codex CLI Format
- **Location**: `~/.codex/sessions/YYYY/MM/DD/rollout-{timestamp}-{uuid}.jsonl`
- **Structure**: JSONL with event types (session_meta, turn_context, response_item, event_msg)
- **Items**: Roles (system, developer, user, assistant)
- **Features**: Date partitioning, turn context, function calls

## Architecture

The converter uses an intermediate representation model to handle conversions:

```
Claude Format ──► Intermediate Model ──► Codex Format
     ▲                                         │
     └─────────────────────────────────────────┘
              (Round-trip capable)
```

### Intermediate Model
- **Session**: Top-level container with metadata
- **Turn**: Conversation turns with user/assistant messages
- **Message**: Content blocks (text, thinking, tool calls)
- **ToolCall**: Tool invocations with inputs/outputs

See [DESIGN.md](DESIGN.md) for detailed architecture and design decisions.

## Development

### Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linter
flake8 session_converter

# Type checking
mypy session_converter
```

### Project Structure

```
session-converter/
├── session_converter/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── models.py           # Intermediate data models
│   ├── parsers/
│   │   ├── claude.py       # Claude format parser
│   │   └── codex.py        # Codex format parser
│   ├── emitters/
│   │   ├── claude.py       # Claude format emitter
│   │   └── codex.py        # Codex format emitter
│   └── utils.py            # Utilities
├── tests/
│   ├── test_claude_parser.py
│   ├── test_codex_parser.py
│   ├── test_conversions.py
│   └── fixtures/           # Example session files
├── examples/
│   ├── claude_session.jsonl
│   └── codex_session.jsonl
├── DESIGN.md
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
└── pyproject.toml
```

## Examples

### Example 1: Basic Conversion

```bash
# Convert a Claude session to Codex
session-convert claude-to-codex ~/.claude/projects/my-project/session-123.jsonl \
  -o ~/converted/session-123-codex.jsonl \
  --stats

Output:
  Converting: session-123.jsonl (Claude Code format)
    - Session ID: abc-123
    - Turns: 8
    - Tool calls: 15
    - Events: 67
  
  Conversion complete: session-123-codex.jsonl (Codex format)
    - Duration: 0.12s
    - Output events: 68
    - Warnings: 0
```

### Example 2: Validation

```bash
# Validate before and after conversion
session-convert validate input.jsonl --format claude
session-convert claude-to-codex input.jsonl -o output.jsonl --validate
session-convert validate output.jsonl --format codex
```

### Example 3: Batch Processing

```bash
# Convert all Claude sessions in a directory
session-convert batch \
  ~/.claude/projects/my-project/ \
  ~/converted/codex/ \
  --from claude \
  --to codex \
  --pattern "*.jsonl" \
  --stats
```

## Known Limitations

1. **Compaction Handling**: Claude's `compact_boundary` events are preserved as metadata in Codex format since Codex handles compaction at the API level.

2. **Schema Evolution**: Both formats are subject to change. The converter handles common fields but may not support all edge cases in future versions.

3. **Partial Information Loss**: Some format-specific metadata may be lost in conversion. Round-trip fidelity is approximately 95% for standard fields.

4. **Custom Extensions**: Custom fields not in the standard schema are preserved in a metadata object when possible.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Claude Code](https://code.claude.com/) - Anthropic's AI coding assistant
- [OpenAI Codex CLI](https://github.com/openai/codex) - OpenAI's command-line coding agent
- [MCP](https://github.com/anthropics/mcp) - Model Context Protocol

## Support

- 📖 [Documentation](https://github.com/yourusername/session-converter/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/session-converter/issues)
- 💬 [Discussions](https://github.com/yourusername/session-converter/discussions)
