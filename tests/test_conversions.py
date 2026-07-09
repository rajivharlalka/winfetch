"""Test conversion between formats."""

import pytest
from pathlib import Path

from session_converter.parsers import ClaudeParser, CodexParser
from session_converter.emitters import ClaudeEmitter, CodexEmitter


def test_claude_parser():
    """Test parsing Claude format."""
    example_file = Path(__file__).parent.parent / "examples" / "claude_session.jsonl"
    
    if not example_file.exists():
        pytest.skip("Example file not found")
    
    parser = ClaudeParser()
    session = parser.parse(example_file)
    
    assert session.id == "session-123"
    assert session.cwd == "/workspace"
    assert session.git_branch == "main"
    assert len(session.turns) > 0
    assert session.get_tool_call_count() > 0


def test_codex_parser():
    """Test parsing Codex format."""
    example_file = Path(__file__).parent.parent / "examples" / "codex_session.jsonl"
    
    if not example_file.exists():
        pytest.skip("Example file not found")
    
    parser = CodexParser()
    session = parser.parse(example_file)
    
    assert session.id == "session-456"
    assert session.cwd == "/workspace"
    assert session.git_branch == "main"
    assert len(session.turns) > 0


def test_claude_to_codex_roundtrip():
    """Test Claude -> Intermediate -> Codex conversion."""
    example_file = Path(__file__).parent.parent / "examples" / "claude_session.jsonl"
    
    if not example_file.exists():
        pytest.skip("Example file not found")
    
    # Parse Claude format
    claude_parser = ClaudeParser()
    session = claude_parser.parse(example_file)
    
    # Convert to Codex
    codex_emitter = CodexEmitter()
    events = codex_emitter.emit(session)
    
    assert len(events) > 0
    assert events[0]['type'] == 'session_meta'
    assert events[0]['payload']['id'] == session.id


def test_codex_to_claude_roundtrip():
    """Test Codex -> Intermediate -> Claude conversion."""
    example_file = Path(__file__).parent.parent / "examples" / "codex_session.jsonl"
    
    if not example_file.exists():
        pytest.skip("Example file not found")
    
    # Parse Codex format
    codex_parser = CodexParser()
    session = codex_parser.parse(example_file)
    
    # Convert to Claude
    claude_emitter = ClaudeEmitter()
    events = claude_emitter.emit(session)
    
    assert len(events) > 0
    # Should have user and assistant events
    event_types = [e['type'] for e in events]
    assert 'user' in event_types or 'assistant' in event_types
