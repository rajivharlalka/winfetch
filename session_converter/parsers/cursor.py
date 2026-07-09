"""Parser for Cursor IDE session format (JSONL export)."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import read_jsonl, parse_timestamp, generate_uuid, safe_get


class CursorParser:
    """Parse Cursor IDE JSONL session files to intermediate format.
    
    Note: This parser works with JSONL exports from Cursor.
    For SQLite database parsing, additional tools are needed.
    """
    
    def __init__(self) -> None:
        self.warnings: List[str] = []
    
    def parse(self, file_path: Path) -> Session:
        """Parse a Cursor session file."""
        events = list(read_jsonl(file_path))
        
        if not events:
            raise ValueError("Empty session file")
        
        # Extract session metadata
        first_event = events[0]
        session_id = first_event.get('composerId', first_event.get('id', generate_uuid()))
        timestamp_ms = first_event.get('createdAt', datetime.now().timestamp() * 1000)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
        cwd = first_event.get('workspace', first_event.get('workingDirectory', '.'))
        
        session = Session(
            id=session_id,
            timestamp=timestamp,
            cwd=cwd,
            originator='cursor',
        )
        
        # Build turns from messages
        turns = self._build_turns(events)
        
        for turn in turns:
            session.add_turn(turn)
        
        return session
    
    def _build_turns(self, events: List[Dict[str, Any]]) -> List[Turn]:
        """Build turns from Cursor events."""
        turns: List[Turn] = []
        current_turn: Dict[str, Any] = {'user': None, 'assistant': None, 'tools': []}
        
        for event in events:
            # Cursor uses type: 1 for user, 2 for assistant
            bubble_type = event.get('type')
            
            if bubble_type == 1:  # User message
                # Start new turn
                if current_turn['user'] or current_turn['assistant'] or current_turn['tools']:
                    turn = self._create_turn(current_turn)
                    if turn:
                        turns.append(turn)
                    current_turn = {'user': None, 'assistant': None, 'tools': []}
                
                current_turn['user'] = self._parse_message(event, 'user')
            
            elif bubble_type == 2:  # Assistant message
                current_turn['assistant'] = self._parse_message(event, 'assistant')
        
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
        """Parse a Cursor message."""
        # Cursor stores text in rawText or text field
        content = event.get('rawText', event.get('text', ''))
        
        content_blocks = [ContentBlock(type='text', content=content)] if content else []
        
        # Extract timestamp if available
        timestamp_ms = event.get('timestamp', datetime.now().timestamp() * 1000)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()
        
        return Message(
            role=role,
            content=content_blocks,
            timestamp=timestamp,
        )
