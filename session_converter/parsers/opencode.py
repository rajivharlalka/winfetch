"""Parser for OpenCode session format (JSONL export)."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import read_jsonl, parse_timestamp, generate_uuid, safe_get


class OpenCodeParser:
    """Parse OpenCode JSONL session files to intermediate format.
    
    Note: This parser works with JSONL exports from OpenCode.
    For SQLite database parsing, additional tools are needed.
    """
    
    def __init__(self) -> None:
        self.warnings: List[str] = []
    
    def parse(self, file_path: Path) -> Session:
        """Parse an OpenCode session file."""
        events = list(read_jsonl(file_path))
        
        if not events:
            raise ValueError("Empty session file")
        
        # First event should contain session info
        first_event = events[0]
        session_id = first_event.get('id', generate_uuid())
        
        # OpenCode uses Unix timestamps in milliseconds
        created_at = first_event.get('created', first_event.get('createdAt', datetime.now().timestamp() * 1000))
        timestamp = datetime.fromtimestamp(created_at / 1000) if created_at else datetime.now()
        
        cwd = first_event.get('directory', first_event.get('workingDirectory', '.'))
        version = first_event.get('version', '1.0')
        
        session = Session(
            id=session_id,
            timestamp=timestamp,
            cwd=cwd,
            version=version,
            originator='opencode',
        )
        
        # Build turns from messages
        turns = self._build_turns(events)
        
        for turn in turns:
            session.add_turn(turn)
        
        return session
    
    def _build_turns(self, events: List[Dict[str, Any]]) -> List[Turn]:
        """Build turns from OpenCode events."""
        turns: List[Turn] = []
        current_turn: Dict[str, Any] = {'user': None, 'assistant': None, 'tools': []}
        
        for event in events:
            role = event.get('role', event.get('type'))
            
            if role == 'user':
                # Start new turn
                if current_turn['user'] or current_turn['assistant'] or current_turn['tools']:
                    turn = self._create_turn(current_turn)
                    if turn:
                        turns.append(turn)
                    current_turn = {'user': None, 'assistant': None, 'tools': []}
                
                current_turn['user'] = self._parse_message(event, 'user')
            
            elif role == 'assistant':
                current_turn['assistant'] = self._parse_message(event, 'assistant')
            
            elif role == 'tool':
                tool_call = self._parse_tool_call(event)
                if tool_call:
                    current_turn['tools'].append(tool_call)
        
        # Add final turn
        if current_turn['user'] or current_turn['assistant'] or current_turn['tools']:
            turn = self._create_turn(current_turn)
            if turn:
                turns.append(turn)
        
        return turns
    
    def _create_turn(self, turn_data: Dict[str, Any]) -> Optional[Turn]:
        """Create a Turn from collected data."""
        if not turn_data['user'] and not turn_data['assistant'] and not turn_data['tools']:
            return None
        
        return Turn(
            id=generate_uuid(),
            timestamp=datetime.now(),
            user_message=turn_data['user'],
            assistant_message=turn_data['assistant'],
            tool_calls=turn_data['tools'],
        )
    
    def _parse_message(self, event: Dict[str, Any], role: str) -> Message:
        """Parse an OpenCode message."""
        content = event.get('content', event.get('text', ''))
        
        # Handle both string and structured content
        content_blocks = []
        if isinstance(content, str):
            content_blocks.append(ContentBlock(type='text', content=content))
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    content_blocks.append(ContentBlock(
                        type=item.get('type', 'text'),
                        content=item.get('text', item.get('content', ''))
                    ))
                elif isinstance(item, str):
                    content_blocks.append(ContentBlock(type='text', content=item))
        
        # Extract timestamp
        timestamp_ms = event.get('timestamp', event.get('created', datetime.now().timestamp() * 1000))
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()
        
        return Message(
            role=role,
            content=content_blocks,
            timestamp=timestamp,
        )
    
    def _parse_tool_call(self, event: Dict[str, Any]) -> Optional[ToolCall]:
        """Parse a tool call from OpenCode format."""
        tool_id = event.get('id', event.get('tool_id', generate_uuid()))
        tool_name = event.get('name', event.get('tool', 'unknown'))
        tool_input = event.get('input', event.get('parameters', {}))
        tool_output = event.get('output', event.get('result', ''))
        
        timestamp_ms = event.get('timestamp', datetime.now().timestamp() * 1000)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()
        
        return ToolCall(
            id=tool_id,
            name=tool_name,
            input=tool_input,
            output=tool_output if tool_output else None,
            timestamp=timestamp,
        )
