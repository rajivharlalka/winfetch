"""Parser for Pi AI assistant session format."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import read_jsonl, parse_timestamp, generate_uuid, safe_get


class PiParser:
    """Parse Pi AI JSONL session files to intermediate format.
    
    Pi uses a tree structure with id/parentId relationships.
    Entry types: header, message, compaction, branch_summary, custom
    """
    
    def __init__(self) -> None:
        self.warnings: List[str] = []
    
    def parse(self, file_path: Path) -> Session:
        """Parse a Pi session file."""
        events = list(read_jsonl(file_path))
        
        if not events:
            raise ValueError("Empty session file")
        
        # First event should be header
        header = events[0]
        if header.get('type') != 'header':
            self.warnings.append("First event is not a header")
            header = {}
        
        session_id = header.get('id', generate_uuid())
        timestamp = parse_timestamp(header.get('timestamp'))
        cwd = header.get('workingDirectory', '.')
        version = str(header.get('version', '3'))
        
        session = Session(
            id=session_id,
            timestamp=timestamp,
            cwd=cwd,
            version=version,
            originator='pi',
        )
        
        # Build turn structure from messages
        # Pi's tree structure is flattened into linear turns
        turns = self._build_turns(events[1:])  # Skip header
        
        for turn in turns:
            session.add_turn(turn)
        
        return session
    
    def _build_turns(self, events: List[Dict[str, Any]]) -> List[Turn]:
        """Build turns from Pi events."""
        turns: List[Turn] = []
        current_turn: Dict[str, Any] = {'user': None, 'assistant': None, 'tools': []}
        
        for event in events:
            event_type = event.get('type')
            
            if event_type == 'message':
                message_data = event.get('message', {})
                role = message_data.get('role')
                
                if role == 'user':
                    # Start new turn if we have pending content
                    if current_turn['user'] or current_turn['assistant'] or current_turn['tools']:
                        turn = self._create_turn(current_turn, event.get('timestamp'))
                        if turn:
                            turns.append(turn)
                        current_turn = {'user': None, 'assistant': None, 'tools': []}
                    
                    current_turn['user'] = self._parse_message(message_data, event.get('timestamp'))
                
                elif role == 'assistant':
                    current_turn['assistant'] = self._parse_message(message_data, event.get('timestamp'))
                
                elif role == 'toolResult':
                    # Parse tool result
                    tool_call = self._parse_tool_result(message_data, event.get('timestamp'))
                    if tool_call:
                        current_turn['tools'].append(tool_call)
            
            elif event_type == 'compaction':
                # Add compaction as a note
                self.warnings.append(f"Compaction event found (tokens: {event.get('tokensBefore')} -> {event.get('tokensAfter')})")
        
        # Add final turn
        if current_turn['user'] or current_turn['assistant'] or current_turn['tools']:
            turn = self._create_turn(current_turn, None)
            if turn:
                turns.append(turn)
        
        return turns
    
    def _create_turn(self, turn_data: Dict[str, Any], timestamp: Optional[str]) -> Optional[Turn]:
        """Create a Turn from collected data."""
        if not turn_data['user'] and not turn_data['assistant'] and not turn_data['tools']:
            return None
        
        return Turn(
            id=generate_uuid(),
            timestamp=parse_timestamp(timestamp) if timestamp else datetime.now(),
            user_message=turn_data['user'],
            assistant_message=turn_data['assistant'],
            tool_calls=turn_data['tools'],
        )
    
    def _parse_message(self, message_data: Dict[str, Any], timestamp: Optional[str]) -> Message:
        """Parse a Pi message."""
        role = message_data.get('role', 'user')
        content_list = message_data.get('content', [])
        
        content_blocks = []
        for content_item in content_list:
            if isinstance(content_item, dict):
                content_type = content_item.get('type', 'text')
                
                if content_type == 'text':
                    content_blocks.append(ContentBlock(
                        type='text',
                        content=content_item.get('text', '')
                    ))
                elif content_type == 'tool_use':
                    content_blocks.append(ContentBlock(
                        type='tool_use',
                        content=content_item.get('input', {}),
                        tool_use_id=content_item.get('id'),
                        tool_name=content_item.get('name'),
                        tool_input=content_item.get('input', {}),
                    ))
            elif isinstance(content_item, str):
                content_blocks.append(ContentBlock(type='text', content=content_item))
        
        return Message(
            role='assistant' if role == 'assistant' else 'user',
            content=content_blocks,
            timestamp=parse_timestamp(timestamp) if timestamp else datetime.now(),
        )
    
    def _parse_tool_result(self, message_data: Dict[str, Any], timestamp: Optional[str]) -> Optional[ToolCall]:
        """Parse a tool result from Pi format."""
        content_list = message_data.get('content', [])
        
        for content_item in content_list:
            if isinstance(content_item, dict) and content_item.get('type') == 'tool_result':
                return ToolCall(
                    id=content_item.get('tool_use_id', generate_uuid()),
                    name=content_item.get('tool_name', 'unknown'),
                    input={},
                    output=content_item.get('content', ''),
                    timestamp=parse_timestamp(timestamp) if timestamp else datetime.now(),
                )
        
        return None
