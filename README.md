# Session Converter

A powerful CLI tool to convert AI assistant sessions between multiple formats: Claude Code, Codex CLI, Cursor IDE, Pi AI, and OpenCode.

## Features

- 🤖 **Auto-Detection**: Automatically detects source format from 5 supported formats
- 🎯 **Explicit Target**: Specify output format for clarity and extensibility
- 🔄 **Multi-Format Support**: Convert between Claude, Codex, Cursor, Pi, and OpenCode
- ✅ **Validation**: Validate session file formats
- 📊 **Statistics**: View detailed session information and conversion stats
- 🚀 **Batch Processing**: Convert entire directories of session files
- 🎯 **High Fidelity**: Preserves tool calls, thinking blocks, and metadata
- 🛡️ **Type Safe**: Built with Pydantic for robust schema validation
- 🔮 **Extensible**: Easily add new formats to the converter

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
# Convert session (auto-detects source, specify target) - RECOMMENDED
session-convert convert input.jsonl --to codex -o output.jsonl
session-convert convert input.jsonl --to claude -o output.jsonl
session-convert convert input.jsonl --to cursor -o output.jsonl
session-convert convert input.jsonl --to pi -o output.jsonl
session-convert convert input.jsonl --to opencode -o output.jsonl

# Show session information
session-convert info input.jsonl

# Validate a session file
session-convert validate input.jsonl

# Batch convert a directory
session-convert batch ~/sessions/claude ~/sessions/codex --from claude --to codex

# Explicit format conversion (if you prefer)
session-convert claude-to-codex input.jsonl -o output.jsonl
session-convert codex-to-claude input.jsonl -o output.jsonl
```

**Supported formats:** `claude`, `codex`, `cursor`, `pi`, `opencode`

## Usage

### Commands

#### `convert` (Recommended)
**Auto-detects source format** and converts to your specified target format.

```bash
session-convert convert <input.jsonl> --to <target-format> [OPTIONS]

Options:
  -o, --output PATH                              Output file path (default: stdout)
  --to [claude|codex|cursor|pi|opencode]        Target format (REQUIRED)
  --pretty                                       Pretty-print JSON output
  --validate                                     Validate output after conversion
  --stats                                        Show conversion statistics
  -v, --verbose                                  Verbose logging
```

**Examples:**
```bash
# Auto-detect source, convert to Codex
session-convert convert my-session.jsonl --to codex -o output.jsonl

# Auto-detect source, convert to Claude
session-convert convert my-session.jsonl --to claude -o output.jsonl

# Convert to Cursor IDE format
session-convert convert my-session.jsonl --to cursor -o output.jsonl

# Convert to Pi AI format
session-convert convert my-session.jsonl --to pi -o output.jsonl

# Convert to OpenCode format
session-convert convert my-session.jsonl --to opencode -o output.jsonl

# With verbose output showing detection
session-convert convert my-session.jsonl --to codex -o output.jsonl --stats -v
```

**Why this design?**
- 🔍 **Auto-detects source**: Supports Claude, Codex, Cursor, Pi, and OpenCode
- 🎯 **Explicit target**: Clear about what you want as output
- 🚀 **Extensible**: Easy to add new formats in the future

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
session-convert validate <input.jsonl> --format <claude|codex|cursor|pi|opencode>

# Or let it auto-detect
session-convert validate <input.jsonl>
```

#### `batch`
Batch convert multiple session files.

```bash
session-convert batch <input-dir> <output-dir> --from <format> --to <format>

Options:
  --from [claude|codex|cursor|pi|opencode]   Source format
  --to [claude|codex|cursor|pi|opencode]     Target format
  --pattern TEXT                             Glob pattern for input files (default: *.jsonl)
  --recursive                                Search subdirectories
  --continue-on-error                        Continue processing if a file fails

Examples:
  # Convert all Claude sessions to Pi format
  session-convert batch ~/sessions/claude ~/sessions/pi --from claude --to pi
  
  # Convert Cursor sessions to OpenCode
  session-convert batch ~/cursor-exports ~/opencode --from cursor --to opencode --recursive
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

### Cursor IDE Format
- **Location**: SQLite database `state.vscdb` (also supports JSONL exports)
- **Structure**: Bubble-based messages with types (1=user, 2=assistant)
- **Features**: Composer tracking, code block metadata, version tracking
- **Note**: Parser works with JSONL exports

### Pi AI Format
- **Location**: `~/.pi/agent/sessions/<project>/YYYY-MM-DDTHH-MM-SS.sssZ_id.jsonl`
- **Structure**: Tree-based JSONL with id/parentId relationships
- **Entry Types**: header, message, compaction, branch_summary, custom
- **Features**: Non-destructive branching, conversation forking, compaction

### OpenCode Format
- **Location**: SQLite database (also supports JSONL exports)
- **Structure**: Session with hierarchical parent-child relationships
- **Roles**: user, assistant, tool
- **Features**: Token tracking, cost calculation, session hierarchy
- **Note**: Parser works with JSONL exports

For detailed format specifications, see [FORMATS.md](FORMATS.md)

## Architecture

The converter uses an intermediate representation model to handle conversions between all supported formats:

```
Claude ──┐
Codex ───┤
Cursor ──┼──► Intermediate Model ──┬──► Claude
Pi ──────┤                          ├──► Codex
OpenCode ┘                          ├──► Cursor
                                    ├──► Pi
                                    └──► OpenCode
         
         All-to-all conversion (25 paths)
```

### Data Flow
```
Input JSONL → Parser → Intermediate Model → Emitter → Output JSONL
```

### Components

1. **Parsers** (`session_converter/parsers/`)
   - `claude.py`: Parse Claude Code format
   - `codex.py`: Parse Codex CLI format
   - `cursor.py`: Parse Cursor IDE format (JSONL export)
   - `pi.py`: Parse Pi AI format (tree structure)
   - `opencode.py`: Parse OpenCode format (JSONL export)

2. **Intermediate Model** (`session_converter/models.py`)
   - Format-agnostic data structures
   - Pydantic models for validation
   - Common representation for all formats

3. **Emitters** (`session_converter/emitters/`)
   - `claude.py`: Generate Claude Code format
   - `codex.py`: Generate Codex CLI format
   - `cursor.py`: Generate Cursor IDE format
   - `pi.py`: Generate Pi AI format
   - `opencode.py`: Generate OpenCode format

4. **CLI** (`session_converter/cli.py`)
   - Command-line interface
   - Format detection (supports 5 formats)
   - Conversion orchestration

5. **Utilities** (`session_converter/utils.py`)
   - JSONL reading/writing
   - Timestamp handling
   - Multi-format detection
   - UUID generation

### Intermediate Model
- **Session**: Top-level container with metadata (ID, timestamp, CWD, git info)
- **Turn**: Conversation turns with user/assistant messages
- **Message**: Content blocks (text, thinking, tool calls)
- **ToolCall**: Tool invocations with inputs/outputs

See [DESIGN.md](DESIGN.md) for detailed architecture and [FORMATS.md](FORMATS.md) for format specifications.

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
│   │   ├── __init__.py
│   │   ├── claude.py       # Claude format parser
│   │   ├── codex.py        # Codex format parser
│   │   ├── cursor.py       # Cursor format parser
│   │   ├── pi.py           # Pi format parser
│   │   └── opencode.py     # OpenCode format parser
│   ├── emitters/
│   │   ├── __init__.py
│   │   ├── claude.py       # Claude format emitter
│   │   ├── codex.py        # Codex format emitter
│   │   ├── cursor.py       # Cursor format emitter
│   │   ├── pi.py           # Pi format emitter
│   │   └── opencode.py     # OpenCode format emitter
│   └── utils.py            # Utilities + format detection
├── tests/
│   ├── test_conversions.py
│   ├── test_edge_cases.py
│   ├── test_auto_detection.py
│   ├── test_new_formats.py
│   └── fixtures/           # Example session files
├── examples/
│   ├── claude_session.jsonl
│   ├── codex_session.jsonl
│   ├── cursor_session.jsonl
│   ├── pi_session.jsonl
│   └── opencode_session.jsonl
├── DESIGN.md               # Architecture & design decisions
├── FORMATS.md              # Format specifications
├── QUICKSTART.md           # Quick start guide
├── CHANGELOG.md            # Change history
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
└── pyproject.toml
```

## Examples

### Example 1: Basic Conversion

```bash
# Convert any format to Codex (auto-detects source)
session-convert convert my-session.jsonl --to codex -o output.jsonl --stats

Output:
  Detected source format: Claude
  Converting to: Codex
  
  ✓ Parsed Claude format
    Session ID: abc-123
    Turns: 8
    Tool calls: 15
  
  ✓ Converted to Codex format
    Output events: 68
  
  ✓ Wrote output to output.jsonl

  Conversion Statistics:
    Duration: 0.12s
    Warnings: 0
    Errors: 0
```

### Example 2: Cross-Format Migration

```bash
# Migrate from Cursor to Pi AI format
session-convert convert cursor-session.jsonl --to pi -o pi-session.jsonl --stats

# Migrate from Pi to OpenCode format
session-convert convert pi-session.jsonl --to opencode -o opencode-session.jsonl

# View information about any format
session-convert info opencode-session.jsonl
```

### Example 3: Batch Processing

```bash
# Convert all Claude sessions to Pi format
session-convert batch \
  ~/.claude/projects/my-project/ \
  ~/converted/pi/ \
  --from claude \
  --to pi \
  --pattern "*.jsonl" \
  --recursive

# Convert Cursor exports to OpenCode
session-convert batch \
  ~/cursor-exports/ \
  ~/opencode-sessions/ \
  --from cursor \
  --to opencode \
  --continue-on-error
```

## Known Limitations

1. **Native Database Support**: Cursor and OpenCode parsers currently work with JSONL exports. Direct SQLite database parsing support is planned for future versions.

2. **Tree Structure Flattening**: When converting from Pi's tree-based format to linear formats (Claude, Codex, etc.), the tree structure and branching information is flattened into a linear sequence of turns.

3. **Format-Specific Features**: Some features may not translate between formats:
   - Pi branching information → Not preserved in linear formats
   - Cursor code blocks → Extracted as text
   - OpenCode cost tracking → Not preserved in other formats
   - Claude compaction boundaries → Preserved as metadata where possible

4. **Round-Trip Fidelity**: Approximately 95% fidelity for standard fields. Format-specific metadata may be lost in cross-format conversions.

5. **Schema Evolution**: All formats are subject to change. The converter handles common fields but may not support all edge cases in future format versions.

For detailed format limitations, see [FORMATS.md](FORMATS.md).

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
- [Cursor IDE](https://cursor.com/) - AI-first code editor
- [Pi AI](https://pi.dev/) - Pi AI assistant for coding
- [OpenCode](https://opencode.ai/) - OpenCode AI coding platform
- [MCP](https://github.com/anthropics/mcp) - Model Context Protocol

## Support

- 📖 [Documentation](https://github.com/yourusername/session-converter/wiki)
- 🐛 [Issue Tracker](https://github.com/yourusername/session-converter/issues)
- 💬 [Discussions](https://github.com/yourusername/session-converter/discussions)
