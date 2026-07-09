# Supported Session Formats

This document describes the session formats supported by Session Converter.

## Overview

Session Converter supports conversion between 5 different AI coding assistant session formats:

1. **Claude Code** - Anthropic's Claude Code format
2. **Codex CLI** - OpenAI's Codex CLI format
3. **Cursor IDE** - Cursor IDE session format
4. **Pi AI** - Pi AI assistant format
5. **OpenCode** - OpenCode format

## Format Details

### 1. Claude Code Format

**Structure**: JSONL with event-based records

**Key Features**:
- UUID-based event tracking
- Parent-child relationships via `parentUuid`
- Git metadata (branch, commit, repository)
- Session-level metadata

**Sample Record**:
```json
{
  "uuid": "abc-123",
  "parentUuid": "parent-uuid",
  "sessionId": "session-123",
  "type": "user",
  "message": {
    "role": "user",
    "content": "Hello"
  },
  "timestamp": "2026-07-09T18:00:00Z"
}
```

### 2. Codex CLI Format

**Structure**: JSONL with typed events

**Key Features**:
- Event types: `session_meta`, `turn_context`, `response_item`, `input_item`
- Payload-based structure
- CLI version tracking
- Originator metadata

**Sample Record**:
```json
{
  "type": "session_meta",
  "payload": {
    "originator": "codex-cli",
    "cli_version": "1.0.0",
    "session_id": "session-456"
  },
  "timestamp": 1720546800
}
```

### 3. Cursor IDE Format

**Structure**: JSONL with bubble-based messages

**Key Features**:
- SQLite database native storage (can be exported to JSONL)
- Bubble types: 1 (user), 2 (assistant)
- Composer-based conversation tracking
- Code block metadata

**Sample Record**:
```json
{
  "bubbleId": "composer-abc-1",
  "type": 1,
  "rawText": "Hello",
  "text": "Hello",
  "timestamp": 1720546800000
}
```

**Note**: This parser works with JSONL exports. For direct SQLite database access, additional tools are needed.

### 4. Pi AI Format

**Structure**: JSONL with tree structure

**Key Features**:
- Tree-based conversation structure via `id`/`parentId`
- Entry types: `header`, `message`, `compaction`, `branch_summary`, `custom`
- Non-destructive branching support
- Working directory tracking

**Sample Record**:
```json
{
  "type": "message",
  "id": "msg-1",
  "parentId": null,
  "message": {
    "role": "user",
    "content": [{"type": "text", "text": "Hello"}],
    "timestamp": 1720546800000
  }
}
```

**Unique Features**:
- Conversation branching and forking
- Compaction for context management
- Branch summaries for context preservation

### 5. OpenCode Format

**Structure**: JSONL with session + messages

**Key Features**:
- SQLite database native storage (can be exported to JSONL)
- Session hierarchy with parent-child relationships
- Role-based messages: user, assistant, tool
- Token tracking and cost calculation

**Sample Record**:
```json
{
  "id": "msg-1",
  "role": "user",
  "content": [{"type": "text", "text": "Hello"}],
  "timestamp": 1720546800000
}
```

**Note**: This parser works with JSONL exports. For direct SQLite database access, additional tools are needed.

## Format Detection

Session Converter automatically detects the source format using a confidence-based scoring system:

1. Scans the first 5 lines of the JSONL file
2. Checks for format-specific indicators
3. Assigns confidence scores to each format
4. Selects the format with the highest score

### Detection Indicators

**Claude Code**:
- `uuid` + `parentUuid` fields
- `sessionId` with type in ['user', 'assistant', 'system']
- `gitBranch` field

**Codex CLI**:
- `type: "session_meta"` with `payload`
- Types: 'turn_context', 'response_item', 'input_item'
- `originator` or `cli_version` in payload

**Cursor IDE**:
- `composerId` + `createdAt` fields
- `bubbleId` with type 1 or 2
- `rawText` field

**Pi AI**:
- `type: "header"` with `workingDirectory`
- Message entries with `parentId`
- Types: 'message', 'compaction', 'branch_summary'

**OpenCode**:
- `directory` + `version` + `created` fields
- `role` in ['user', 'assistant', 'tool']
- `slug` + `projectID` fields

## Conversion Matrix

All formats can be converted to all other formats:

| From ↓ / To → | Claude | Codex | Cursor | Pi | OpenCode |
|---------------|--------|-------|--------|----|---------| 
| **Claude**    | ✓      | ✓     | ✓      | ✓  | ✓        |
| **Codex**     | ✓      | ✓     | ✓      | ✓  | ✓        |
| **Cursor**    | ✓      | ✓     | ✓      | ✓  | ✓        |
| **Pi**        | ✓      | ✓     | ✓      | ✓  | ✓        |
| **OpenCode**  | ✓      | ✓     | ✓      | ✓  | ✓        |

## Adding New Formats

To add a new format:

1. Create a parser in `session_converter/parsers/`
2. Create an emitter in `session_converter/emitters/`
3. Add format detection logic in `session_converter/utils.py`
4. Update CLI choices in `session_converter/cli.py`
5. Add example session in `examples/`
6. Add tests in `tests/`

See `DESIGN.md` for architecture details.

## Limitations

### Cursor and OpenCode Native Storage

The Cursor and OpenCode parsers work with JSONL exports. For direct SQLite database access:

- **Cursor**: Database is `state.vscdb` with `cursorDiskKV` table
- **OpenCode**: Database contains `sessions`, `messages`, and `files` tables

Future versions may include native SQLite support.

### Tree Structure Flattening

When converting from tree-based formats (Pi) to linear formats (Claude, Codex), the tree structure is flattened into a linear sequence of turns. Branch information may be lost.

### Format-Specific Features

Some format-specific features may not translate perfectly:

- **Pi branching**: Converted to linear sequence
- **Cursor code blocks**: Extracted as text
- **OpenCode cost tracking**: Not preserved in other formats
- **Compaction summaries**: May be preserved as metadata

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/)
- [Codex CLI Documentation](https://openai.com/codex)
- [Cursor IDE Documentation](https://cursor.com/docs)
- [Pi AI Documentation](https://pi.dev/docs)
- [OpenCode Documentation](https://opencode.ai/docs)
