"""Emitter for OpenCode session format."""

from typing import Any, Dict, List
from datetime import datetime
from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import format_timestamp, generate_uuid


class OpenCodeEmitter:
    """Convert intermediate format to OpenCode JSONL format."""
    
    def emit(self, session: Session) -> List[Dict[str, Any]]:
        """Convert a Session to OpenCode format events."""
        events: List[Dict[str, Any]] = []
        
        # First event: session info
        session_info = {
            'id': session.id,
            'title': f"Session {session.id[:8]}",
            'directory': session.cwd,
            'version': session.version or '1.0',
            'created': int(session.timestamp.timestamp() * 1000),
            'updated': int(datetime.now().timestamp() * 1000),
        }
        events.append(session_info)
        
        # Convert turns to messages
        for turn in session.turns:
            # User message
            if turn.user_message:
                events.append(self._emit_message(turn.user_message, 'user'))
            
            # Tool calls
            for tool_call in turn.tool_calls:
                events.append(self._emit_tool_call(tool_call))
            
            # Assistant message
            if turn.assistant_message:
                events.append(self._emit_message(turn.assistant_message, 'assistant'))
        
        return events
    
    def _emit_message(self, message: Message, role: str) -> Dict[str, Any]:
        """Convert a Message to OpenCode format."""
        # Extract text content
        content_parts = []
        for block in message.content:
            if block.type == 'text':
                content_parts.append({
                    'type': 'text',
                    'text': block.content if isinstance(block.content, str) else str(block.content),
                })
        
        return {
            'id': generate_uuid(),
            'role': role,
            'content': content_parts,
            'timestamp': int(message.timestamp.timestamp() * 1000),
        }
    
    def _emit_tool_call(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Convert a ToolCall to OpenCode format."""
        return {
            'id': tool_call.id,
            'role': 'tool',
            'name': tool_call.name,
            'input': tool_call.input,
            'output': tool_call.output or '',
            'timestamp': int(tool_call.timestamp.timestamp() * 1000),
        }
