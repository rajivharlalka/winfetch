"""Test automatic format detection."""

import pytest
from pathlib import Path

from session_converter.utils import detect_format


FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_detect_claude_format():
    """Test detecting Claude Code format."""
    claude_file = EXAMPLES_DIR / "claude_session.jsonl"
    
    if not claude_file.exists():
        pytest.skip("Example file not found")
    
    detected = detect_format(claude_file)
    assert detected == "claude", f"Expected 'claude', got '{detected}'"


def test_detect_codex_format():
    """Test detecting Codex CLI format."""
    codex_file = EXAMPLES_DIR / "codex_session.jsonl"
    
    if not codex_file.exists():
        pytest.skip("Example file not found")
    
    detected = detect_format(codex_file)
    assert detected == "codex", f"Expected 'codex', got '{detected}'"


def test_detect_minimal_claude():
    """Test detecting minimal Claude session."""
    fixture_file = FIXTURES_DIR / "claude_minimal.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    detected = detect_format(fixture_file)
    assert detected == "claude"


def test_detect_claude_with_thinking():
    """Test detecting Claude session with thinking blocks."""
    fixture_file = FIXTURES_DIR / "claude_with_thinking.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    detected = detect_format(fixture_file)
    assert detected == "claude"


def test_detect_claude_multi_tool():
    """Test detecting Claude session with multiple tools."""
    fixture_file = FIXTURES_DIR / "claude_multi_tool.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    detected = detect_format(fixture_file)
    assert detected == "claude"


def test_detect_claude_unicode():
    """Test detecting Claude session with Unicode content."""
    fixture_file = FIXTURES_DIR / "claude_unicode.jsonl"
    
    if not fixture_file.exists():
        pytest.skip("Fixture file not found")
    
    detected = detect_format(fixture_file)
    assert detected == "claude"


def test_detect_invalid_file():
    """Test detection on invalid/non-existent file."""
    invalid_file = Path("/tmp/nonexistent-session.jsonl")
    
    detected = detect_format(invalid_file)
    assert detected is None


def test_detect_empty_file():
    """Test detection on empty file."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
        # Write nothing
    
    try:
        detected = detect_format(temp_path)
        assert detected is None
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_detect_malformed_json():
    """Test detection on malformed JSON."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
        f.write("not valid json\n")
    
    try:
        detected = detect_format(temp_path)
        assert detected is None
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_detection_confidence():
    """Test that detection uses multiple indicators for confidence."""
    from session_converter.models import Session, Turn, Message, ContentBlock
    from session_converter.emitters import ClaudeEmitter, CodexEmitter
    from session_converter.utils import write_jsonl
    from datetime import datetime
    import tempfile
    
    # Create a session
    session = Session(
        id="test-detection",
        timestamp=datetime.now(),
        cwd="/workspace",
        git_branch="main",
    )
    
    turn = Turn(
        id="turn-1",
        timestamp=datetime.now(),
        user_message=Message(
            role="user",
            content=[ContentBlock(type="text", content="Hello")],
            timestamp=datetime.now(),
        ),
        assistant_message=Message(
            role="assistant",
            content=[ContentBlock(type="text", content="Hi there!")],
            timestamp=datetime.now(),
        ),
    )
    
    session.add_turn(turn)
    
    # Test Claude detection
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        claude_path = Path(f.name)
    
    try:
        claude_emitter = ClaudeEmitter()
        claude_events = claude_emitter.emit(session)
        write_jsonl(claude_path, claude_events)
        
        detected = detect_format(claude_path)
        assert detected == "claude", f"Failed to detect Claude format, got {detected}"
    finally:
        if claude_path.exists():
            claude_path.unlink()
    
    # Test Codex detection
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        codex_path = Path(f.name)
    
    try:
        codex_emitter = CodexEmitter()
        codex_events = codex_emitter.emit(session)
        write_jsonl(codex_path, codex_events)
        
        detected = detect_format(codex_path)
        assert detected == "codex", f"Failed to detect Codex format, got {detected}"
    finally:
        if codex_path.exists():
            codex_path.unlink()
