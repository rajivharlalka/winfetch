"""Parser for Codex CLI session format."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import read_jsonl, parse_timestamp, generate_uuid, safe_get


class CodexParser:
    """Parse Codex CLI JSONL session files to intermediate format."""
    
    def __init__(self) -> None:
        self.warnings: List[str] = []
    
    def parse(self, file_path: Path) -> Session:
        """Parse a Codex CLI session file."""
        events = list(read_jsonl(file_path))
        
        if not events:
            raise ValueError("Empty session file")
        
        # Extract session metadata from session_meta event
        session_meta = self._find_session_meta(events)
        
        if not session_meta:
            raise ValueError("No session_meta event found")
        
        payload = session_meta.get('payload', {})
        session_id = payload.get('id', generate_uuid())
        timestamp = parse_timestamp(session_meta.get('timestamp'))
        cwd = payload.get('cwd', '.')
        git_info = payload.get('git', {})
        
        session = Session(
            id=session_id,
            timestamp=timestamp,
            cwd=cwd,
            git_branch=git_info.get('branch') if git_info else None,
            git_commit=git_info.get('commit_hash') if git_info else None,
            git_repository=git_info.get('repository_url') if git_info else None,
            version=payload.get('cli_version'),
            originator=payload.get('originator', 'codex-cli'),
            model=payload.get('model_provider'),
        )
        
        # Group events into turns
        turns = self._group_into_turns(events)
        
        for turn_events in turns:
            turn = self._parse_turn(turn_events)
            if turn:
                session.add_turn(turn)
        
        return session
    
    def _find_session_meta(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the session_meta event."""
        for event in events:
            if event.get('type') == 'session_meta':
                return event
        return None
    
    def _group_into_turns(self, events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group events into conversation turns."""
        turns: List[List[Dict[str, Any]]] = []
        current_turn: List[Dict[str, Any]] = []
        
        for event in events:
            event_type = event.get('type')
            
            # Skip session_meta as it's already processed
            if event_type == 'session_meta':
                continue
            
            # Start a new turn on turn_context
            if event_type == 'turn_context':
                if current_turn:
                    turns.append(current_turn)
                    current_turn = []
            
            current_turn.append(event)
        
        # Add the last turn
        if current_turn:
            turns.append(current_turn)
        
        return turns
    
    def _parse_turn(self, events: List[Dict[str, Any]]) -> Optional[Turn]:
        """Parse a turn from a list of events."""
        if not events:
            return None
        
        turn_id = generate_uuid()
        timestamp = parse_timestamp(events[0].get('timestamp'))
        
        user_message: Optional[Message] = None
        assistant_message: Optional[Message] = None
        tool_calls: List[ToolCall] = []
        
        # Track tool calls
        tool_call_map: Dict[str, Dict[str, Any]] = {}
        
        for event in events:
            event_type = event.get('type')
            payload = event.get('payload', {})
            
            if event_type == 'response_item':
                # Parse response items (assistant messages, function calls, reasoning)
                self._parse_response_item(
                    event,
                    assistant_message,
                    tool_call_map,
                )
            
            elif event_type == 'input_item':
                # Parse input items (user messages, function outputs)
                self._parse_input_item(
                    event,
                    user_message,
                    tool_call_map,
                )
            
            elif event_type == 'event_msg':
                # Parse UI events (might contain message content)
                self._parse_event_msg(event, user_message, assistant_message)
        
        # Convert tool_call_map to ToolCall objects
        for tool_id, tool_data in tool_call_map.items():
            if 'name' in tool_data:
                tool_calls.append(ToolCall(
                    id=tool_id,
                    name=tool_data['name'],
                    input=tool_data.get('input', {}),
                    output=tool_data.get('output'),
                    timestamp=parse_timestamp(tool_data.get('timestamp')),
                ))
        
        # If we only have tool calls, still create the turn
        if not user_message and not assistant_message:
            # Try to extract from response_item
            for event in events:
                if event.get('type') == 'response_item':
                    payload = event.get('payload', {})
                    role = payload.get('role')
                    item_type = payload.get('type')
                    
                    if role == 'assistant':
                        content_blocks = self._parse_response_content(payload)
                        if content_blocks:
                            assistant_message = Message(
                                role='assistant',
                                content=content_blocks,
                                timestamp=parse_timestamp(event.get('timestamp')),
                            )
                            break
                    elif role == 'user':
                        content = payload.get('content', '')
                        if content:
                            user_message = Message(
                                role='user',
                                content=[ContentBlock(type='text', content=content)],
                                timestamp=parse_timestamp(event.get('timestamp')),
                            )
                            break
        
        if not user_message and not assistant_message and not tool_calls:
            return None
        
        return Turn(
            id=turn_id,
            timestamp=timestamp,
            user_message=user_message,
            assistant_message=assistant_message,
            tool_calls=tool_calls,
        )
    
    def _parse_response_item(
        self,
        event: Dict[str, Any],
        assistant_message: Optional[Message],
        tool_call_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Message]:
        """Parse a response_item event."""
        payload = event.get('payload', {})
        role = payload.get('role')
        item_type = payload.get('type')
        
        if role != 'assistant':
            return assistant_message
        
        if item_type == 'function_call':
            # Extract function call
            tool_id = payload.get('call_id', generate_uuid())
            tool_call_map[tool_id] = {
                'name': payload.get('name', ''),
                'input': payload.get('arguments', {}),
                'timestamp': event.get('timestamp'),
            }
        
        elif item_type == 'reasoning':
            # Thinking/reasoning content
            if not assistant_message:
                assistant_message = Message(
                    role='assistant',
                    content=[],
                    timestamp=parse_timestamp(event.get('timestamp')),
                )
            
            content = payload.get('content', '')
            if content:
                assistant_message.content.append(
                    ContentBlock(
                        type='thinking',
                        content=content,
                        thinking_content=content,
                    )
                )
        
        else:
            # Regular message content
            content_blocks = self._parse_response_content(payload)
            if content_blocks and not assistant_message:
                assistant_message = Message(
                    role='assistant',
                    content=content_blocks,
                    timestamp=parse_timestamp(event.get('timestamp')),
                )
        
        return assistant_message
    
    def _parse_input_item(
        self,
        event: Dict[str, Any],
        user_message: Optional[Message],
        tool_call_map: Dict[str, Dict[str, Any]],
    ) -> Optional[Message]:
        """Parse an input_item event."""
        payload = event.get('payload', {})
        role = payload.get('role')
        item_type = payload.get('type')
        
        if role == 'user':
            content = payload.get('content', '')
            if content and not user_message:
                user_message = Message(
                    role='user',
                    content=[ContentBlock(type='text', content=content)],
                    timestamp=parse_timestamp(event.get('timestamp')),
                )
        
        elif item_type == 'function_call_output':
            # Extract function output
            call_id = payload.get('call_id')
            output = payload.get('output', '')
            
            if call_id and call_id in tool_call_map:
                tool_call_map[call_id]['output'] = output
        
        return user_message
    
    def _parse_event_msg(
        self,
        event: Dict[str, Any],
        user_message: Optional[Message],
        assistant_message: Optional[Message],
    ) -> None:
        """Parse an event_msg event (UI events)."""
        payload = event.get('payload', {})
        msg_type = payload.get('type')
        
        # Event messages are usually UI updates, not core conversation content
        # We might extract token usage here if needed
        if msg_type == 'token_count':
            usage = payload.get('usage', {})
            if assistant_message and not assistant_message.token_usage:
                assistant_message.token_usage = usage
    
    def _parse_response_content(self, payload: Dict[str, Any]) -> List[ContentBlock]:
        """Parse content from a response payload."""
        content_blocks = []
        
        content = payload.get('content', '')
        if isinstance(content, str) and content:
            content_blocks.append(ContentBlock(type='text', content=content))
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    content_blocks.append(ContentBlock(type='text', content=item))
                elif isinstance(item, dict):
                    # Handle structured content
                    if item.get('type') == 'text':
                        content_blocks.append(
                            ContentBlock(type='text', content=item.get('text', ''))
                        )
        
        return content_blocks
