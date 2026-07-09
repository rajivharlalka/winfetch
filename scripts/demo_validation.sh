#!/bin/bash
# Demo script showing various validation methods

set -e

echo "============================================"
echo "Session Converter Validation Demo"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure PATH includes local bin
export PATH="$HOME/.local/bin:$PATH"

echo -e "${BLUE}1. Basic CLI Commands${NC}"
echo "-----------------------------------"
echo ""

echo "$ session-convert --help"
session-convert --help | head -10
echo ""

echo -e "${BLUE}2. Inspecting Example Sessions${NC}"
echo "-----------------------------------"
echo ""

echo "$ session-convert info examples/claude_session.jsonl"
session-convert info examples/claude_session.jsonl
echo ""

echo "$ session-convert info examples/codex_session.jsonl"
session-convert info examples/codex_session.jsonl
echo ""

echo -e "${BLUE}3. Validating Sessions${NC}"
echo "-----------------------------------"
echo ""

echo "$ session-convert validate examples/claude_session.jsonl --format claude"
session-convert validate examples/claude_session.jsonl --format claude
echo ""

echo "$ session-convert validate examples/codex_session.jsonl --format codex"
session-convert validate examples/codex_session.jsonl --format codex
echo ""

echo -e "${BLUE}4. Converting Claude → Codex${NC}"
echo "-----------------------------------"
echo ""

echo "$ session-convert claude-to-codex examples/claude_session.jsonl -o /tmp/converted_codex.jsonl --stats"
session-convert claude-to-codex examples/claude_session.jsonl -o /tmp/converted_codex.jsonl --stats
echo ""

echo "Inspecting output..."
echo "$ head -2 /tmp/converted_codex.jsonl | jq ."
head -2 /tmp/converted_codex.jsonl | jq . 2>/dev/null || cat /tmp/converted_codex.jsonl | head -2
echo ""

echo -e "${BLUE}5. Converting Codex → Claude${NC}"
echo "-----------------------------------"
echo ""

echo "$ session-convert codex-to-claude examples/codex_session.jsonl -o /tmp/converted_claude.jsonl --stats"
session-convert codex-to-claude examples/codex_session.jsonl -o /tmp/converted_claude.jsonl --stats
echo ""

echo "Inspecting output..."
echo "$ head -1 /tmp/converted_claude.jsonl | jq ."
head -1 /tmp/converted_claude.jsonl | jq . 2>/dev/null || cat /tmp/converted_claude.jsonl | head -1
echo ""

echo -e "${BLUE}6. Round-Trip Test${NC}"
echo "-----------------------------------"
echo ""

echo "Claude → Codex → Claude round-trip..."
session-convert claude-to-codex examples/claude_session.jsonl -o /tmp/rt_step1.jsonl
session-convert codex-to-claude /tmp/rt_step1.jsonl -o /tmp/rt_step2.jsonl

echo "Original session info:"
session-convert info examples/claude_session.jsonl | grep "Session ID"

echo "Round-trip session info:"
session-convert info /tmp/rt_step2.jsonl | grep "Session ID"
echo ""

echo -e "${BLUE}7. Running Unit Tests${NC}"
echo "-----------------------------------"
echo ""

echo "$ pytest tests/ -v --tb=short"
pytest tests/ -v --tb=short
echo ""

echo -e "${BLUE}8. Running Automated Validation${NC}"
echo "-----------------------------------"
echo ""

echo "$ python3 scripts/validate_converter.py"
python3 scripts/validate_converter.py
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ All validation checks passed!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

echo "Validation complete! The session converter is working correctly."
echo ""
echo "For more validation options, see VALIDATION.md"
