# Session Converter Design Document

## Overview
A CLI tool to convert AI assistant sessions between Claude Code and OpenAI Codex CLI formats.

## Session Format Analysis

### Claude Code Format
**Location:** `~/.claude/projects/<encoded-path>/<session-uuid>.jsonl`

**Structure:**
- JSONL format (one JSON object per line)
- Append-only, chronological event stream

**Key Event Types:**
- `user` - User messages and tool results
- `assistant` - Claude responses with text, tool calls, and thinking
- `system` - Metadata (turn_duration, compact_boundary)
- `progress` - Tool execution progress
- `file-history-snapshot` - Git state snapshots
- `summary` - Compaction summaries

**Common Fields (all events):**
```json
{
  "type": "user|assistant|system|progress|...",
  "uuid": "unique-id",
  "parentUuid": "parent-id",
  "sessionId": "session-uuid",
  "timestamp": "2026-07-09T18:00:00.000Z",
  "cwd": "/workspace",
  "gitBranch": "main",
  "version": "2.5.0",
  "message": {
    "content": [/* content blocks */],
    "usage": {/* token counts */}
  }
}
```

**Content Block Types:**
- `text` - Plain text content
- `tool_use` - Tool calls with id, name, input
- `tool_result` - Tool outputs referencing tool_use_id
- `thinking` - Internal reasoning blocks

### Codex CLI Format
**Location:** `~/.codex/sessions/YYYY/MM/DD/rollout-{timestamp}-{uuid}.jsonl`

**Structure:**
- JSONL format
- Date-partitioned directory structure

**Key Event Types:**
- `session_meta` - Session identity, cwd, model, git info (first line)
- `turn_context` - Per-turn settings (model, approval policy)
- `response_item` - Raw LLM transcript
- `event_msg` - UI events (messages, token counts, task status)
- `input_item` - Items sent to the model
- `config_snapshot` - Configuration state

**Event Structure:**
```json
{
  "type": "session_meta|turn_context|response_item|event_msg|...",
  "timestamp": "2026-07-09T18:00:00.000Z",
  "payload": {
    /* type-specific data */
  }
}
```

**Conversation Items (in response_item/input_item):**
- Roles: `system`, `developer`, `user`, `assistant`
- Item types: `reasoning`, `function_call`, `function_call_output`, `message`

## Conversion Strategy

### Core Challenges

1. **Event Type Mapping**
   - Claude has fine-grained event types (user, assistant, system, progress)
   - Codex groups into broader categories (response_item, event_msg, input_item)

2. **Content Block Transformation**
   - Claude: Array of typed blocks (text, tool_use, tool_result, thinking)
   - Codex: Item-based structure with roles and type fields

3. **Tool Call Representation**
   - Claude: Separate tool_use and tool_result blocks
   - Codex: function_call and function_call_output items

4. **Metadata Preservation**
   - Claude: Distributed across event fields (uuid, parentUuid, cwd, gitBranch)
   - Codex: Centralized in session_meta and turn_context

5. **Compaction/Summarization**
   - Claude: compact_boundary with logicalParentUuid
   - Codex: Uses API-level compaction

### Conversion Architecture

```
┌─────────────────────────────────────────────────────┐
│                  CLI Entry Point                     │
│  $ session-convert claude-to-codex input.jsonl      │
│  $ session-convert codex-to-claude input.jsonl      │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼────┐
    │  Parser  │          │  Parser  │
    │  Claude  │          │  Codex   │
    └────┬─────┘          └─────┬────┘
         │                       │
         │   ┌──────────────┐   │
         └──►│ Intermediate │◄──┘
             │    Model     │
             └──────┬───────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼─────┐        ┌─────▼────┐
    │ Emitter  │        │ Emitter  │
    │  Codex   │        │  Claude  │
    └──────────┘        └──────────┘
```

### Intermediate Model

A unified representation that both formats can convert to/from:

```typescript
interface Session {
  id: string;
  timestamp: string;
  cwd: string;
  gitBranch?: string;
  gitCommit?: string;
  model: string;
  turns: Turn[];
  metadata: Record<string, unknown>;
}

interface Turn {
  id: string;
  timestamp: string;
  userMessage?: Message;
  assistantMessage?: Message;
  toolCalls: ToolCall[];
  metadata: Record<string, unknown>;
}

interface Message {
  content: ContentBlock[];
  timestamp: string;
}

interface ContentBlock {
  type: 'text' | 'thinking' | 'tool_use' | 'tool_result';
  content: string | object;
  metadata?: Record<string, unknown>;
}

interface ToolCall {
  id: string;
  name: string;
  input: object;
  output?: string;
  timestamp: string;
}
```

## Mapping Rules

### Claude → Codex

1. **Session Initialization**
   - First line: Create `session_meta` from Claude session metadata
   - Extract: sessionId, cwd, gitBranch from first event

2. **Turn Reconstruction**
   - Group consecutive events by turn boundaries
   - User events → `input_item` with role=user
   - Assistant events → `response_item` with role=assistant

3. **Content Blocks**
   - `text` block → message item with text content
   - `thinking` block → reasoning item
   - `tool_use` block → function_call item
   - `tool_result` block → function_call_output item

4. **Metadata**
   - `usage` → include in event_msg for token tracking
   - `compact_boundary` → note in metadata (Codex handles differently)

### Codex → Claude

1. **Session Initialization**
   - Parse `session_meta` to extract session identity
   - Create initial system event with session context

2. **Turn Reconstruction**
   - Parse `turn_context` to identify turn boundaries
   - Group `response_item` and `input_item` by turn

3. **Content Items**
   - message with role=user → user event with text block
   - message with role=assistant → assistant event with text block
   - reasoning item → thinking block
   - function_call item → tool_use block
   - function_call_output item → tool_result block

4. **UUID Generation**
   - Generate UUIDs for events
   - Create parent-child chains with parentUuid

5. **Metadata Preservation**
   - Store Codex-specific fields in metadata objects
   - Preserve unknown fields for round-trip compatibility

## CLI Design

### Commands

```bash
# Convert Claude → Codex
session-convert claude-to-codex <input.jsonl> [options]

# Convert Codex → Claude
session-convert codex-to-claude <input.jsonl> [options]

# Validate a session file
session-convert validate <input.jsonl> --format <claude|codex>

# Show session info
session-convert info <input.jsonl>

# Batch convert directory
session-convert batch <input-dir> <output-dir> --from <claude|codex> --to <codex|claude>
```

### Options

```
--output, -o        Output file path (default: stdout)
--pretty           Pretty-print JSON output
--preserve-unknown  Keep unknown fields in output
--validate         Validate output after conversion
--stats            Show conversion statistics
--verbose, -v      Verbose logging
--help, -h         Show help
```

### Output Format

```
Converting: input.jsonl (Claude Code format)
  - Session ID: abc-123
  - Turns: 15
  - Tool calls: 42
  - Events: 156

Conversion complete: output.jsonl (Codex format)
  - Duration: 0.23s
  - Output events: 158
  - Warnings: 2

Warnings:
  - Line 45: compact_boundary event preserved in metadata (Codex uses API-level compaction)
  - Line 89: Custom field 'customData' preserved in metadata
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project setup (TypeScript/Node.js or Python)
- [ ] CLI framework (Commander.js or Click)
- [ ] JSONL reader/writer utilities
- [ ] Intermediate model definitions

### Phase 2: Parsers
- [ ] Claude Code parser
- [ ] Codex CLI parser
- [ ] Validation for both formats

### Phase 3: Converters
- [ ] Claude → Intermediate
- [ ] Codex → Intermediate
- [ ] Intermediate → Claude
- [ ] Intermediate → Codex

### Phase 4: CLI & Features
- [ ] Command implementations
- [ ] Batch processing
- [ ] Validation mode
- [ ] Statistics reporting
- [ ] Error handling & logging

### Phase 5: Testing & Documentation
- [ ] Unit tests for parsers
- [ ] Integration tests for conversions
- [ ] Round-trip tests
- [ ] Example session files
- [ ] Usage documentation

## Edge Cases & Considerations

1. **Incomplete Sessions**
   - Handle sessions without proper endings
   - Preserve partial turns

2. **Custom Fields**
   - Preserve unknown fields in metadata
   - Document non-standard extensions

3. **Large Sessions**
   - Stream processing for large files
   - Memory-efficient parsing

4. **Version Differences**
   - Handle schema evolution
   - Version detection and compatibility

5. **Error Recovery**
   - Continue on parse errors when possible
   - Detailed error reporting with line numbers

6. **Round-trip Fidelity**
   - Test: Claude → Codex → Claude
   - Measure information loss
   - Document non-reversible transformations

## Technology Stack

### Option 1: TypeScript/Node.js
- **Pros:** Type safety, JSON native, good async I/O, rich ecosystem
- **Cons:** Runtime overhead, deployment complexity
- **Libraries:** Commander, zod (validation), chalk (colors)

### Option 2: Python
- **Pros:** Great for data processing, simple deployment, extensive libraries
- **Cons:** Less type safety (unless using mypy), slower for I/O
- **Libraries:** Click, Pydantic (validation), rich (pretty output)

### Option 3: Go
- **Pros:** Fast, single binary, excellent concurrency
- **Cons:** More verbose, less flexible for JSON manipulation
- **Libraries:** cobra (CLI), encoding/json

**Recommendation:** Python with Click and Pydantic for rapid development and ease of use.

## Success Metrics

1. **Correctness:** 100% of valid inputs produce valid outputs
2. **Completeness:** All essential information preserved
3. **Performance:** Process 1000-line session in < 100ms
4. **Usability:** Clear error messages, helpful documentation
5. **Reliability:** Round-trip conversion with < 5% information loss

## Future Enhancements

1. **Web UI:** Browser-based converter
2. **API Server:** REST API for conversions
3. **Diff Tool:** Compare sessions visually
4. **Merge Tool:** Combine multiple sessions
5. **Analytics:** Session statistics and insights
6. **Export Formats:** Markdown, HTML reports
7. **Format Support:** Add more AI assistant formats (Cursor, Aider, etc.)
