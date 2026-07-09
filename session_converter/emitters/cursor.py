"""Emitter for Cursor IDE session format."""

from typing import Any, Dict, List
from datetime import datetime
from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import format_timestamp, generate_uuid


class CursorEmitter:
    """Convert intermediate format to Cursor JSONL format."""
    
    def emit(self, session: Session) -> List[Dict[str, Any]]:
        """Convert a Session to Cursor format events."""
        events: List[Dict[str, Any]] = []
        
        # Cursor uses numbered bubble IDs and types
        # type: 1 = user, 2 = assistant
        bubble_idx = 0
        
        for turn in session.turns:
            # User message (type: 1)
            if turn.user_message:
                bubble_idx += 1
                events.append(self._emit_bubble(
                    turn.user_message,
                    bubble_idx,
                    bubble_type=1,
                    session_id=session.id,
                ))
            
            # Assistant message (type: 2)
            if turn.assistant_message:
                bubble_idx += 1
                events.append(self._emit_bubble(
                    turn.assistant_message,
                    bubble_idx,
                    bubble_type=2,
                    session_id=session.id,
                ))
        
        # Add session metadata as first event
        session_meta = {
            'composerId': session.id,
            'createdAt': int(session.timestamp.timestamp() * 1000),
            'workspace': session.cwd,
            'version': session.version or '1',
            'status': 'completed',
        }
        events.insert(0, session_meta)
        
        return events
    
    def _emit_bubble(
        self,
        message: Message,
        bubble_idx: int,
        bubble_type: int,
        session_id: str,
    ) -> Dict[str, Any]:
        """Convert a Message to Cursor bubble format."""
        # Combine all text content
        text_parts = []
        for block in message.content:
            if block.type == 'text':
                text_parts.append(block.content if isinstance(block.content, str) else str(block.content))
        
        text = '\n'.join(text_parts) if text_parts else ''
        
        return {
            'bubbleId': f"{session_id}-{bubble_idx}",
            'type': bubble_type,  # 1 = user, 2 = assistant
            'rawText': text,
            'text': text,
            'timestamp': int(message.timestamp.timestamp() * 1000),
        }
