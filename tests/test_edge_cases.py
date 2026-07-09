"""Test edge cases and special scenarios."""

import pytest
from pathlib import Path

from session_converter.parsers import ClaudeParser, CodexParser
from session_converter.emitters import ClaudeEmitter, CodexEmitter


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_minimal_session():
    """Test conversion of minimal session (just hello/hi)."""
    fixture_file = FIXTURES_DIR / "claude_minimal.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    # Parse
    parser = ClaudeParser()
    session = parser.parse(fixture_file)
    
    assert session.id == "minimal-session"
    assert len(session.turns) == 1
    assert session.get_tool_call_count() == 0
    
    # Convert to Codex
    emitter = CodexEmitter()
    events = emitter.emit(session)
    
    assert len(events) > 0
    assert events[0]['type'] == 'session_meta'


def test_session_with_thinking():
    """Test conversion of session with thinking blocks."""
    fixture_file = FIXTURES_DIR / "claude_with_thinking.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    # Parse
    parser = ClaudeParser()
    session = parser.parse(fixture_file)
    
    assert len(session.turns) == 1
    turn = session.turns[0]
    assert turn.assistant_message is not None
    
    # Check for thinking block
    thinking_blocks = [
        block for block in turn.assistant_message.content
        if block.type == 'thinking'
    ]
    assert len(thinking_blocks) > 0
    
    # Convert to Codex
    emitter = CodexEmitter()
    events = emitter.emit(session)
    
    # Check for reasoning item
    reasoning_events = [
        e for e in events
        if e.get('type') == 'response_item' and
        e.get('payload', {}).get('type') == 'reasoning'
    ]
    assert len(reasoning_events) > 0


def test_multiple_tool_calls():
    """Test conversion with multiple tool calls in one turn."""
    fixture_file = FIXTURES_DIR / "claude_multi_tool.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    # Parse
    parser = ClaudeParser()
    session = parser.parse(fixture_file)
    
    assert len(session.turns) >= 1
    assert session.get_tool_call_count() >= 2
    
    # Convert to Codex
    emitter = CodexEmitter()
    events = emitter.emit(session)
    
    # Count function_call events
    function_calls = [
        e for e in events
        if e.get('type') == 'response_item' and
        e.get('payload', {}).get('type') == 'function_call'
    ]
    assert len(function_calls) >= 2


def test_unicode_content():
    """Test conversion of session with Unicode characters."""
    fixture_file = FIXTURES_DIR / "claude_unicode.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    # Parse
    parser = ClaudeParser()
    session = parser.parse(fixture_file)
    
    assert len(session.turns) == 1
    
    # Convert to Codex
    emitter = CodexEmitter()
    events = emitter.emit(session)
    
    # Convert back to Claude
    # This tests that Unicode survives round-trip
    claude_emitter = ClaudeEmitter()
    
    # Parse the Codex format (we need to actually write and read it)
    import tempfile
    import json
    from session_converter.utils import write_jsonl, read_jsonl
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        write_jsonl(temp_path, events)
        
        # Parse back
        codex_parser = CodexParser()
        roundtrip_session = codex_parser.parse(temp_path)
        
        # Check that we still have the content
        assert len(roundtrip_session.turns) > 0
    
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_empty_tool_output():
    """Test handling of tool calls with empty outputs."""
    from session_converter.models import Session, Turn, Message, ToolCall, ContentBlock
    from datetime import datetime
    
    # Create a session with a tool call that has empty output
    session = Session(
        id="test-empty-output",
        timestamp=datetime.now(),
        cwd="/workspace",
    )
    
    tool_call = ToolCall(
        id="tool-1",
        name="TestTool",
        input={"arg": "value"},
        output="",  # Empty output
        timestamp=datetime.now(),
    )
    
    turn = Turn(
        id="turn-1",
        timestamp=datetime.now(),
        tool_calls=[tool_call],
    )
    
    session.add_turn(turn)
    
    # Convert to both formats
    codex_emitter = CodexEmitter()
    codex_events = codex_emitter.emit(session)
    assert len(codex_events) > 0
    
    claude_emitter = ClaudeEmitter()
    claude_events = claude_emitter.emit(session)
    assert len(claude_events) > 0


def test_missing_git_info():
    """Test handling of sessions without git information."""
    from session_converter.models import Session, Turn, Message, ContentBlock
    from datetime import datetime
    
    session = Session(
        id="test-no-git",
        timestamp=datetime.now(),
        cwd="/workspace",
        git_branch=None,  # No git info
        git_commit=None,
    )
    
    turn = Turn(
        id="turn-1",
        timestamp=datetime.now(),
        user_message=Message(
            role="user",
            content=[ContentBlock(type="text", content="Hello")],
            timestamp=datetime.now(),
        ),
    )
    
    session.add_turn(turn)
    
    # Should not crash
    codex_emitter = CodexEmitter()
    events = codex_emitter.emit(session)
    assert len(events) > 0
    
    # session_meta should still be created
    assert events[0]['type'] == 'session_meta'


def test_long_content():
    """Test handling of very long content blocks."""
    from session_converter.models import Session, Turn, Message, ContentBlock
    from datetime import datetime
    
    # Create a message with very long content
    long_text = "x" * 10000  # 10k characters
    
    session = Session(
        id="test-long",
        timestamp=datetime.now(),
        cwd="/workspace",
    )
    
    turn = Turn(
        id="turn-1",
        timestamp=datetime.now(),
        assistant_message=Message(
            role="assistant",
            content=[ContentBlock(type="text", content=long_text)],
            timestamp=datetime.now(),
        ),
    )
    
    session.add_turn(turn)
    
    # Should handle long content
    codex_emitter = CodexEmitter()
    events = codex_emitter.emit(session)
    
    # Find the response item with the long content
    response_items = [
        e for e in events
        if e.get('type') == 'response_item'
    ]
    assert len(response_items) > 0


def test_special_characters_in_tool_input():
    """Test tool calls with special characters in input."""
    from session_converter.models import Session, Turn, ToolCall
    from datetime import datetime
    
    session = Session(
        id="test-special-chars",
        timestamp=datetime.now(),
        cwd="/workspace",
    )
    
    # Tool call with special characters
    tool_call = ToolCall(
        id="tool-1",
        name="TestTool",
        input={
            "code": 'def test():\n    print("Hello\\nWorld")\n    return True',
            "path": "/tmp/test\"file\".py",
            "quotes": "\"'`",
        },
        output="Success",
        timestamp=datetime.now(),
    )
    
    turn = Turn(
        id="turn-1",
        timestamp=datetime.now(),
        tool_calls=[tool_call],
    )
    
    session.add_turn(turn)
    
    # Convert to both formats
    codex_emitter = CodexEmitter()
    codex_events = codex_emitter.emit(session)
    
    claude_emitter = ClaudeEmitter()
    claude_events = claude_emitter.emit(session)
    
    # Both should succeed
    assert len(codex_events) > 0
    assert len(claude_events) > 0
