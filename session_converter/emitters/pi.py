"""Emitter for Pi AI assistant session format."""

from typing import Any, Dict, List
from datetime import datetime
from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import format_timestamp, generate_uuid


class PiEmitter:
    """Convert intermediate format to Pi JSONL format."""
    
    def emit(self, session: Session) -> List[Dict[str, Any]]:
        """Convert a Session to Pi format events."""
        events: List[Dict[str, Any]] = []
        
        # First event: header
        header = {
            'type': 'header',
            'version': 3,
            'workingDirectory': session.cwd,
            'timestamp': format_timestamp(session.timestamp),
        }
        events.append(header)
        
        # Track parent IDs for tree structure
        parent_id: str | None = None
        
        # Convert turns to messages
        for turn in session.turns:
            # User message
            if turn.user_message:
                event_id = generate_uuid()
                events.append(self._emit_message(
                    turn.user_message,
                    event_id,
                    parent_id,
                ))
                parent_id = event_id
            
            # Tool calls
            for tool_call in turn.tool_calls:
                # Tool use in assistant message would be here
                # Tool result
                if tool_call.output:
                    event_id = generate_uuid()
                    events.append(self._emit_tool_result(
                        tool_call,
                        event_id,
                        parent_id,
                    ))
                    parent_id = event_id
            
            # Assistant message
            if turn.assistant_message:
                event_id = generate_uuid()
                events.append(self._emit_message(
                    turn.assistant_message,
                    event_id,
                    parent_id,
                ))
                parent_id = event_id
        
        return events
    
    def _emit_message(
        self,
        message: Message,
        event_id: str,
        parent_id: str | None,
    ) -> Dict[str, Any]:
        """Convert a Message to Pi format."""
        content = []
        
        for block in message.content:
            if block.type == 'text':
                content.append({
                    'type': 'text',
                    'text': block.content if isinstance(block.content, str) else str(block.content),
                })
            elif block.type == 'tool_use':
                content.append({
                    'type': 'tool_use',
                    'id': block.tool_use_id or generate_uuid(),
                    'name': block.tool_name or 'unknown',
                    'input': block.tool_input or {},
                })
        
        return {
            'type': 'message',
            'id': event_id,
            'parentId': parent_id,
            'message': {
                'role': message.role,
                'content': content,
                'timestamp': int(message.timestamp.timestamp() * 1000),
            },
        }
    
    def _emit_tool_result(
        self,
        tool_call: ToolCall,
        event_id: str,
        parent_id: str | None,
    ) -> Dict[str, Any]:
        """Convert a tool result to Pi format."""
        return {
            'type': 'message',
            'id': event_id,
            'parentId': parent_id,
            'message': {
                'role': 'toolResult',
                'content': [
                    {
                        'type': 'tool_result',
                        'tool_use_id': tool_call.id,
                        'tool_name': tool_call.name,
                        'content': tool_call.output or '',
                    }
                ],
                'timestamp': int(tool_call.timestamp.timestamp() * 1000),
            },
        }
