"""Emitter for Claude Code session format."""

from typing import Any, Dict, List
from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import format_timestamp, generate_uuid


class ClaudeEmitter:
    """Convert intermediate format to Claude Code JSONL format."""
    
    def __init__(self) -> None:
        self.parent_uuid: str | None = None
    
    def emit(self, session: Session) -> List[Dict[str, Any]]:
        """Convert a Session to Claude Code format events."""
        events: List[Dict[str, Any]] = []
        
        # Track parent UUID chain
        self.parent_uuid = None
        
        for turn in session.turns:
            turn_events = self._emit_turn(turn, session)
            events.extend(turn_events)
        
        return events
    
    def _emit_turn(self, turn: Turn, session: Session) -> List[Dict[str, Any]]:
        """Convert a Turn to Claude Code events."""
        events: List[Dict[str, Any]] = []
        
        # Emit user message
        if turn.user_message:
            user_event = self._emit_user_message(turn.user_message, session)
            events.append(user_event)
            self.parent_uuid = user_event['uuid']
        
        # Emit assistant message with tool_use blocks
        if turn.assistant_message:
            assistant_event = self._emit_assistant_message(
                turn.assistant_message,
                turn.tool_calls,
                session
            )
            events.append(assistant_event)
            self.parent_uuid = assistant_event['uuid']
        
        # Emit tool results as user messages
        if turn.tool_calls:
            for tool_call in turn.tool_calls:
                if tool_call.output is not None:
                    tool_result_event = self._emit_tool_result(tool_call, session)
                    events.append(tool_result_event)
                    self.parent_uuid = tool_result_event['uuid']
        
        return events
    
    def _emit_user_message(self, message: Message, session: Session) -> Dict[str, Any]:
        """Convert a user Message to a Claude user event."""
        content_blocks = []
        
        for block in message.content:
            if block.type == 'text':
                content_blocks.append({
                    'type': 'text',
                    'text': block.content if isinstance(block.content, str) else str(block.content),
                })
            else:
                # Preserve other block types
                content_blocks.append({
                    'type': block.type,
                    'content': block.content,
                })
        
        event_uuid = generate_uuid()
        
        return {
            'type': 'user',
            'uuid': event_uuid,
            'parentUuid': self.parent_uuid,
            'sessionId': session.id,
            'timestamp': format_timestamp(message.timestamp),
            'cwd': session.cwd,
            'gitBranch': session.git_branch,
            'version': session.version or '2.5.0',
            'message': {
                'content': content_blocks,
            },
        }
    
    def _emit_assistant_message(
        self,
        message: Message,
        tool_calls: List[ToolCall],
        session: Session
    ) -> Dict[str, Any]:
        """Convert an assistant Message to a Claude assistant event."""
        content_blocks = []
        
        # Add message content blocks
        for block in message.content:
            if block.type == 'text':
                content_blocks.append({
                    'type': 'text',
                    'text': block.content if isinstance(block.content, str) else str(block.content),
                })
            elif block.type == 'thinking':
                content_blocks.append({
                    'type': 'thinking',
                    'thinking': block.thinking_content or block.content,
                    'signature': block.signature,
                })
            elif block.type == 'tool_use':
                content_blocks.append({
                    'type': 'tool_use',
                    'id': block.tool_use_id or generate_uuid(),
                    'name': block.tool_name or '',
                    'input': block.tool_input or {},
                })
        
        # Add tool_use blocks from tool_calls
        for tool_call in tool_calls:
            content_blocks.append({
                'type': 'tool_use',
                'id': tool_call.id,
                'name': tool_call.name,
                'input': tool_call.input,
            })
        
        event_uuid = generate_uuid()
        
        event: Dict[str, Any] = {
            'type': 'assistant',
            'uuid': event_uuid,
            'parentUuid': self.parent_uuid,
            'sessionId': session.id,
            'timestamp': format_timestamp(message.timestamp),
            'cwd': session.cwd,
            'gitBranch': session.git_branch,
            'version': session.version or '2.5.0',
            'message': {
                'content': content_blocks,
            },
        }
        
        # Add token usage if available
        if message.token_usage:
            event['message']['usage'] = message.token_usage
        
        return event
    
    def _emit_tool_result(self, tool_call: ToolCall, session: Session) -> Dict[str, Any]:
        """Convert a tool result to a Claude user event with tool_result."""
        event_uuid = generate_uuid()
        
        return {
            'type': 'user',
            'uuid': event_uuid,
            'parentUuid': self.parent_uuid,
            'sessionId': session.id,
            'timestamp': format_timestamp(tool_call.timestamp),
            'cwd': session.cwd,
            'gitBranch': session.git_branch,
            'version': session.version or '2.5.0',
            'message': {
                'content': [
                    {
                        'type': 'tool_result',
                        'tool_use_id': tool_call.id,
                        'content': tool_call.output or '',
                    }
                ],
            },
        }
