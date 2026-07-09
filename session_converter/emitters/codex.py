"""Emitter for Codex CLI session format."""

from typing import Any, Dict, List
from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import format_timestamp, generate_uuid


class CodexEmitter:
    """Convert intermediate format to Codex CLI JSONL format."""
    
    def emit(self, session: Session) -> List[Dict[str, Any]]:
        """Convert a Session to Codex CLI format events."""
        events: List[Dict[str, Any]] = []
        
        # First event: session_meta
        session_meta = self._emit_session_meta(session)
        events.append(session_meta)
        
        # Emit turns
        for turn in session.turns:
            turn_events = self._emit_turn(turn, session)
            events.extend(turn_events)
        
        return events
    
    def _emit_session_meta(self, session: Session) -> Dict[str, Any]:
        """Create the session_meta event."""
        payload: Dict[str, Any] = {
            'id': session.id,
            'timestamp': format_timestamp(session.timestamp),
            'cwd': session.cwd,
            'originator': session.originator or 'session-converter',
            'cli_version': session.version or '0.121.0',
            'model_provider': session.model or 'openai',
            'source': 'cli',
        }
        
        # Add git info if available
        if session.git_branch or session.git_commit or session.git_repository:
            payload['git'] = {}
            if session.git_branch:
                payload['git']['branch'] = session.git_branch
            if session.git_commit:
                payload['git']['commit_hash'] = session.git_commit
            if session.git_repository:
                payload['git']['repository_url'] = session.git_repository
        
        return {
            'type': 'session_meta',
            'timestamp': format_timestamp(session.timestamp),
            'payload': payload,
        }
    
    def _emit_turn(self, turn: Turn, session: Session) -> List[Dict[str, Any]]:
        """Convert a Turn to Codex CLI events."""
        events: List[Dict[str, Any]] = []
        
        # Emit turn_context
        turn_context = {
            'type': 'turn_context',
            'timestamp': format_timestamp(turn.timestamp),
            'payload': {
                'model': session.model or 'openai',
                'approval_policy': 'always',
            },
        }
        events.append(turn_context)
        
        # Emit user message as input_item
        if turn.user_message:
            for block in turn.user_message.content:
                input_event = self._emit_input_item(block, turn.user_message, session)
                if input_event:
                    events.append(input_event)
        
        # Emit tool calls and results
        for tool_call in turn.tool_calls:
            # Function call
            function_call_event = {
                'type': 'response_item',
                'timestamp': format_timestamp(tool_call.timestamp),
                'payload': {
                    'role': 'assistant',
                    'type': 'function_call',
                    'call_id': tool_call.id,
                    'name': tool_call.name,
                    'arguments': tool_call.input,
                },
            }
            events.append(function_call_event)
            
            # Function output
            if tool_call.output is not None:
                function_output_event = {
                    'type': 'input_item',
                    'timestamp': format_timestamp(tool_call.timestamp),
                    'payload': {
                        'type': 'function_call_output',
                        'call_id': tool_call.id,
                        'output': tool_call.output,
                    },
                }
                events.append(function_output_event)
        
        # Emit assistant message as response_item
        if turn.assistant_message:
            for block in turn.assistant_message.content:
                response_event = self._emit_response_item(block, turn.assistant_message, session)
                if response_event:
                    events.append(response_event)
            
            # Emit event_msg for token usage if available
            if turn.assistant_message.token_usage:
                event_msg = {
                    'type': 'event_msg',
                    'timestamp': format_timestamp(turn.assistant_message.timestamp),
                    'payload': {
                        'type': 'token_count',
                        'usage': turn.assistant_message.token_usage,
                    },
                }
                events.append(event_msg)
        
        return events
    
    def _emit_input_item(
        self,
        block: ContentBlock,
        message: Message,
        session: Session
    ) -> Dict[str, Any] | None:
        """Convert a content block to an input_item event."""
        if block.type == 'text':
            return {
                'type': 'input_item',
                'timestamp': format_timestamp(message.timestamp),
                'payload': {
                    'role': 'user',
                    'type': 'message',
                    'content': block.content if isinstance(block.content, str) else str(block.content),
                },
            }
        
        # Other block types might need special handling
        return None
    
    def _emit_response_item(
        self,
        block: ContentBlock,
        message: Message,
        session: Session
    ) -> Dict[str, Any] | None:
        """Convert a content block to a response_item event."""
        if block.type == 'text':
            return {
                'type': 'response_item',
                'timestamp': format_timestamp(message.timestamp),
                'payload': {
                    'role': 'assistant',
                    'type': 'message',
                    'content': block.content if isinstance(block.content, str) else str(block.content),
                },
            }
        
        elif block.type == 'thinking':
            return {
                'type': 'response_item',
                'timestamp': format_timestamp(message.timestamp),
                'payload': {
                    'role': 'assistant',
                    'type': 'reasoning',
                    'content': block.thinking_content or block.content,
                },
            }
        
        elif block.type == 'tool_use':
            return {
                'type': 'response_item',
                'timestamp': format_timestamp(message.timestamp),
                'payload': {
                    'role': 'assistant',
                    'type': 'function_call',
                    'call_id': block.tool_use_id or generate_uuid(),
                    'name': block.tool_name or '',
                    'arguments': block.tool_input or {},
                },
            }
        
        return None
