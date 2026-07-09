"""Tests for Pi, Cursor, and OpenCode format conversions."""

import json
from pathlib import Path
import pytest

from session_converter.parsers import PiParser, CursorParser, OpenCodeParser
from session_converter.emitters import PiEmitter, CursorEmitter, OpenCodeEmitter
from session_converter.utils import read_jsonl, write_jsonl


def test_pi_parse():
    """Test parsing Pi format."""
    parser = PiParser()
    session = parser.parse(Path('examples/pi_session.jsonl'))
    
    assert session.id is not None
    assert session.originator == 'pi'
    assert len(session.turns) > 0
    assert session.cwd == '/workspace/my-project'


def test_cursor_parse():
    """Test parsing Cursor format."""
    parser = CursorParser()
    session = parser.parse(Path('examples/cursor_session.jsonl'))
    
    assert session.id == 'cursor-session-abc123'
    assert session.originator == 'cursor'
    assert len(session.turns) > 0


def test_opencode_parse():
    """Test parsing OpenCode format."""
    parser = OpenCodeParser()
    session = parser.parse(Path('examples/opencode_session.jsonl'))
    
    assert session.id == 'opencode-session-xyz789'
    assert session.originator == 'opencode'
    assert len(session.turns) > 0
    assert session.cwd == '/workspace/scraper-project'


def test_pi_roundtrip(tmp_path):
    """Test Pi parse -> emit roundtrip."""
    parser = PiParser()
    emitter = PiEmitter()
    
    # Parse
    session = parser.parse(Path('examples/pi_session.jsonl'))
    
    # Emit
    events = emitter.emit(session)
    
    # Write and re-parse
    output_file = tmp_path / 'pi_roundtrip.jsonl'
    write_jsonl(output_file, events)
    
    session2 = parser.parse(output_file)
    
    # Compare
    assert len(session2.turns) == len(session.turns)
    assert session2.cwd == session.cwd


def test_cursor_roundtrip(tmp_path):
    """Test Cursor parse -> emit roundtrip."""
    parser = CursorParser()
    emitter = CursorEmitter()
    
    # Parse
    session = parser.parse(Path('examples/cursor_session.jsonl'))
    
    # Emit
    events = emitter.emit(session)
    
    # Write and re-parse
    output_file = tmp_path / 'cursor_roundtrip.jsonl'
    write_jsonl(output_file, events)
    
    session2 = parser.parse(output_file)
    
    # Compare
    assert len(session2.turns) == len(session.turns)


def test_opencode_roundtrip(tmp_path):
    """Test OpenCode parse -> emit roundtrip."""
    parser = OpenCodeParser()
    emitter = OpenCodeEmitter()
    
    # Parse
    session = parser.parse(Path('examples/opencode_session.jsonl'))
    
    # Emit
    events = emitter.emit(session)
    
    # Write and re-parse
    output_file = tmp_path / 'opencode_roundtrip.jsonl'
    write_jsonl(output_file, events)
    
    session2 = parser.parse(output_file)
    
    # Compare
    assert len(session2.turns) == len(session.turns)
    assert session2.cwd == session.cwd


def test_cross_format_conversions(tmp_path):
    """Test converting between different format pairs."""
    conversions = [
        ('pi', PiParser(), CursorEmitter()),
        ('cursor', CursorParser(), PiEmitter()),
        ('opencode', OpenCodeParser(), PiEmitter()),
        ('pi', PiParser(), OpenCodeEmitter()),
    ]
    
    for format_name, parser, emitter in conversions:
        # Parse
        session = parser.parse(Path(f'examples/{format_name}_session.jsonl'))
        
        # Emit
        events = emitter.emit(session)
        
        # Verify events were created
        assert len(events) > 0
        assert all(isinstance(event, dict) for event in events)


def test_pi_tree_structure():
    """Test that Pi format maintains tree structure."""
    parser = PiParser()
    emitter = PiEmitter()
    
    session = parser.parse(Path('examples/pi_session.jsonl'))
    events = emitter.emit(session)
    
    # First event should be header
    assert events[0]['type'] == 'header'
    
    # Subsequent events should have id and parentId
    for event in events[1:]:
        assert 'id' in event
        assert 'parentId' in event


def test_cursor_bubble_types():
    """Test that Cursor format uses correct bubble types."""
    parser = CursorParser()
    emitter = CursorEmitter()
    
    session = parser.parse(Path('examples/cursor_session.jsonl'))
    events = emitter.emit(session)
    
    # Check bubble types (1 = user, 2 = assistant)
    user_bubbles = [e for e in events if e.get('type') == 1]
    assistant_bubbles = [e for e in events if e.get('type') == 2]
    
    assert len(user_bubbles) > 0
    assert len(assistant_bubbles) > 0


def test_opencode_structure():
    """Test OpenCode format structure."""
    parser = OpenCodeParser()
    emitter = OpenCodeEmitter()
    
    session = parser.parse(Path('examples/opencode_session.jsonl'))
    events = emitter.emit(session)
    
    # First event should have session info
    assert 'id' in events[0]
    assert 'directory' in events[0]
    
    # Check for user/assistant/tool roles
    roles = set()
    for event in events[1:]:
        if 'role' in event:
            roles.add(event['role'])
    
    assert 'user' in roles or 'assistant' in roles or 'tool' in roles
