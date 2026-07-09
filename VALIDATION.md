# Session Converter Validation Guide

This guide provides comprehensive methods to validate the session converter tool.

## Table of Contents

1. [Quick Validation](#quick-validation)
2. [Unit Tests](#unit-tests)
3. [Round-Trip Testing](#round-trip-testing)
4. [Real Session Testing](#real-session-testing)
5. [Edge Cases](#edge-cases)
6. [Automated Validation Script](#automated-validation-script)
7. [Manual Verification](#manual-verification)

## Quick Validation

### 1. Basic Functionality Check

```bash
# Test help command
session-convert --help

# Test info command
session-convert info examples/claude_session.jsonl
session-convert info examples/codex_session.jsonl

# Test validation
session-convert validate examples/claude_session.jsonl --format claude
session-convert validate examples/codex_session.jsonl --format codex

# Test conversions with stats
session-convert claude-to-codex examples/claude_session.jsonl -o /tmp/test1.jsonl --stats
session-convert codex-to-claude examples/codex_session.jsonl -o /tmp/test2.jsonl --stats
```

### 2. Verify Output Format

```bash
# Convert and inspect output
session-convert claude-to-codex examples/claude_session.jsonl -o /tmp/output.jsonl
head -5 /tmp/output.jsonl

# Validate the output
session-convert validate /tmp/output.jsonl --format codex
```

## Unit Tests

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=session_converter --cov-report=html

# Run specific test
pytest tests/test_conversions.py::test_claude_to_codex_roundtrip -v
```

## Round-Trip Testing

Round-trip testing ensures data fidelity by converting back and forth:

### Claude → Codex → Claude

```bash
# Original
session-convert info examples/claude_session.jsonl

# Convert to Codex
session-convert claude-to-codex examples/claude_session.jsonl -o /tmp/step1_codex.jsonl --stats

# Convert back to Claude
session-convert codex-to-claude /tmp/step1_codex.jsonl -o /tmp/step2_claude.jsonl --stats

# Compare
session-convert info /tmp/step2_claude.jsonl

# Validate both outputs
session-convert validate /tmp/step1_codex.jsonl --format codex
session-convert validate /tmp/step2_claude.jsonl --format claude
```

### Codex → Claude → Codex

```bash
# Original
session-convert info examples/codex_session.jsonl

# Convert to Claude
session-convert codex-to-claude examples/codex_session.jsonl -o /tmp/step1_claude.jsonl --stats

# Convert back to Codex
session-convert claude-to-codex /tmp/step1_claude.jsonl -o /tmp/step2_codex.jsonl --stats

# Compare
session-convert info /tmp/step2_codex.jsonl
```

## Real Session Testing

### Testing with Your Own Sessions

#### Claude Code Sessions

```bash
# Find your Claude sessions
ls -la ~/.claude/projects/*/

# Pick a session file
SESSION_FILE=~/.claude/projects/my-project-path/abc-123-def.jsonl

# Validate original
session-convert validate "$SESSION_FILE" --format claude

# Get info
session-convert info "$SESSION_FILE"

# Convert and validate
session-convert claude-to-codex "$SESSION_FILE" -o /tmp/converted.jsonl --stats --validate
```

#### Codex CLI Sessions

```bash
# Find your Codex sessions
ls -la ~/.codex/sessions/2026/

# Pick a session file
SESSION_FILE=~/.codex/sessions/2026/07/09/rollout-2026-07-09T12-00-00-000Z-abc123.jsonl

# Validate original
session-convert validate "$SESSION_FILE" --format codex

# Get info
session-convert info "$SESSION_FILE"

# Convert and validate
session-convert codex-to-claude "$SESSION_FILE" -o /tmp/converted.jsonl --stats --validate
```

## Edge Cases

### Test Cases to Validate

1. **Empty/Minimal Sessions**
   - Sessions with no tool calls
   - Single turn sessions
   - Sessions with only user messages

2. **Complex Sessions**
   - Many tool calls (50+)
   - Long conversations (20+ turns)
   - Large file operations

3. **Special Content**
   - Unicode characters
   - Very long text blocks
   - Code with special characters
   - Binary data in outputs

4. **Metadata Variations**
   - Missing git information
   - Different model providers
   - Various CLI versions
   - Custom metadata fields

5. **Error Conditions**
   - Malformed JSON
   - Missing required fields
   - Invalid timestamps
   - Corrupted session files

## Automated Validation Script

Use the provided validation script:

```bash
# Run all validation checks
python scripts/validate_converter.py

# Run specific validation
python scripts/validate_converter.py --test roundtrip
python scripts/validate_converter.py --test examples
python scripts/validate_converter.py --test real-sessions
```

## Manual Verification

### 1. Content Verification

Manually inspect converted files to ensure:

**For Claude → Codex conversion:**
- [ ] First event is `session_meta` with correct session ID
- [ ] `turn_context` events mark turn boundaries
- [ ] User messages become `input_item` events
- [ ] Assistant messages become `response_item` events
- [ ] Tool calls become `function_call` events
- [ ] Tool outputs become `function_call_output` events
- [ ] Thinking blocks become `reasoning` type items
- [ ] Timestamps are preserved
- [ ] Git information is in session_meta

**For Codex → Claude conversion:**
- [ ] Events have `uuid` and `parentUuid` chains
- [ ] Session ID is consistent across events
- [ ] User messages have `type: "user"`
- [ ] Assistant messages have `type: "assistant"`
- [ ] Tool uses are in assistant content blocks
- [ ] Tool results are in separate user events
- [ ] Git branch appears in each event
- [ ] Token usage is preserved

### 2. Statistical Verification

After conversion, check that:

```bash
# Count events
echo "Original events:"
wc -l < examples/claude_session.jsonl

echo "Converted events:"
wc -l < /tmp/converted.jsonl

# Check session info matches
session-convert info examples/claude_session.jsonl
session-convert info /tmp/converted.jsonl
```

### 3. JSON Schema Validation

Validate against expected schemas:

```bash
# For Claude format
cat /tmp/converted.jsonl | jq -c 'select(.type == "user" or .type == "assistant") | 
  {type: .type, has_uuid: (.uuid != null), has_sessionId: (.sessionId != null)}'

# For Codex format
cat /tmp/converted.jsonl | jq -c 'select(.type == "session_meta") | 
  {type: .type, has_payload: (.payload != null), has_id: (.payload.id != null)}'
```

### 4. Diff Comparison

For round-trip testing, compare key fields:

```bash
# Extract key information from original
jq -c '{type, sessionId, cwd}' examples/claude_session.jsonl > /tmp/original_keys.jsonl

# Extract from round-trip result
jq -c '{type, sessionId, cwd}' /tmp/roundtrip.jsonl > /tmp/roundtrip_keys.jsonl

# Compare
diff /tmp/original_keys.jsonl /tmp/roundtrip_keys.jsonl
```

## Validation Checklist

### Pre-Release Validation

- [ ] All unit tests pass
- [ ] Round-trip tests pass for both directions
- [ ] Example files validate and convert correctly
- [ ] CLI help text is correct and complete
- [ ] Error messages are clear and helpful
- [ ] Stats output is accurate
- [ ] Batch processing works correctly
- [ ] Large files (1000+ lines) process without errors
- [ ] Memory usage is reasonable for large files
- [ ] Edge cases are handled gracefully

### Production Validation

When using with real sessions:

- [ ] Backup original sessions before conversion
- [ ] Test on a small sample first
- [ ] Verify session ID preservation
- [ ] Check tool call input/output integrity
- [ ] Confirm timestamp consistency
- [ ] Validate git information transfer
- [ ] Ensure no data loss in conversion
- [ ] Test with various session types (interactive, batch, subagents)

## Common Issues and Solutions

### Issue: "Invalid JSON at line N"
**Solution:** Check that the input file is valid JSONL (one JSON object per line)

### Issue: "No session_meta event found"
**Solution:** Ensure you're using a Codex format file, not Claude format

### Issue: "Could not detect session format"
**Solution:** Manually specify format with `--format` flag

### Issue: Conversion is slow
**Solution:** For large batches, use `--continue-on-error` and process in parallel

### Issue: Missing tool outputs
**Solution:** Check that tool_result blocks reference correct tool_use_id

## Performance Benchmarks

Expected performance on typical hardware:

| Session Size | Events | Conversion Time | Memory Usage |
|--------------|--------|-----------------|--------------|
| Small        | 10-50  | < 0.1s         | < 50MB       |
| Medium       | 100-500| < 0.5s         | < 100MB      |
| Large        | 1000+  | < 2s           | < 200MB      |

## Validation Metrics

Track these metrics during validation:

1. **Correctness**: % of conversions that produce valid output
2. **Completeness**: % of information preserved (sessions, turns, tool calls)
3. **Fidelity**: % of round-trip conversions that match original
4. **Performance**: Average conversion time per session
5. **Reliability**: % of conversions that complete without errors

## Reporting Issues

If you find validation failures:

1. Note the input file characteristics (size, format, special features)
2. Record the exact command used
3. Capture the error message or unexpected output
4. Try to create a minimal reproduction case
5. Report with: input sample, command, expected vs actual output
