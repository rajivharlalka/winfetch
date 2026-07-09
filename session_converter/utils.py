"""Utility functions for session conversion."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional
import uuid


def read_jsonl(file_path: Path) -> Generator[Dict[str, Any], None, None]:
    """Read JSONL file line by line."""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_number}: {e}")


def write_jsonl(file_path: Path, records: list[Dict[str, Any]], pretty: bool = False) -> None:
    """Write records to JSONL file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            if pretty:
                f.write(json.dumps(record, indent=2))
            else:
                f.write(json.dumps(record))
            f.write('\n')


def parse_timestamp(timestamp: Optional[str]) -> datetime:
    """Parse ISO 8601 timestamp string."""
    if not timestamp:
        return datetime.now()
    
    try:
        # Handle various ISO 8601 formats
        if timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp)
    except (ValueError, AttributeError):
        return datetime.now()


def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""
    return dt.isoformat() + 'Z' if dt.tzinfo is None else dt.isoformat()


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def detect_format(file_path: Path) -> Optional[str]:
    """Detect the session format (claude or codex).
    
    Returns:
        'claude' if Claude Code format detected
        'codex' if Codex CLI format detected
        None if format cannot be determined
    """
    try:
        claude_indicators = 0
        codex_indicators = 0
        lines_checked = 0
        max_lines = 5  # Check first 5 lines for confidence
        
        for record in read_jsonl(file_path):
            lines_checked += 1
            
            # Claude format indicators
            if 'uuid' in record and 'parentUuid' in record:
                claude_indicators += 2
            if 'sessionId' in record and record.get('type') in ['user', 'assistant', 'system']:
                claude_indicators += 2
            if 'gitBranch' in record:
                claude_indicators += 1
            if 'message' in record and 'content' in record.get('message', {}):
                claude_indicators += 1
            
            # Codex format indicators
            if record.get('type') == 'session_meta' and 'payload' in record:
                codex_indicators += 5  # Strong indicator
            if record.get('type') in ['turn_context', 'response_item', 'input_item', 'event_msg']:
                codex_indicators += 2
            if 'payload' in record:
                payload = record.get('payload', {})
                if 'originator' in payload or 'cli_version' in payload:
                    codex_indicators += 2
            
            # Stop after checking enough lines
            if lines_checked >= max_lines:
                break
        
        # Determine format based on indicators
        if codex_indicators > claude_indicators:
            return 'codex'
        elif claude_indicators > codex_indicators:
            return 'claude'
        else:
            return None
    
    except Exception:
        return None


def calculate_duration(start_time: datetime, end_time: datetime) -> str:
    """Calculate duration between two timestamps in human-readable format."""
    delta = end_time - start_time
    
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def safe_get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, {})
        else:
            return default
    return d if d != {} else default
