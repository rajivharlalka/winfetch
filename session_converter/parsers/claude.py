"""Parser for Claude Code session format."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ..models import Session, Turn, Message, ContentBlock, ToolCall
from ..utils import read_jsonl, parse_timestamp, generate_uuid, safe_get


class ClaudeParser:
    """Parse Claude Code JSONL session files to intermediate format."""
    
    def __init__(self) -> None:
        self.warnings: List[str] = []
    
    def parse(self, file_path: Path) -> Session:
        """Parse a Claude Code session file."""
        events = list(read_jsonl(file_path))
        
        if not events:
            raise ValueError("Empty session file")
        
        # Extract session metadata from first event
        first_event = events[0]
        session_id = first_event.get('sessionId', generate_uuid())
        timestamp = parse_timestamp(first_event.get('timestamp'))
        cwd = first_event.get('cwd', '.')
        git_branch = first_event.get('gitBranch')
        version = first_event.get('version')
        
        session = Session(
            id=session_id,
            timestamp=timestamp,
            cwd=cwd,
            git_branch=git_branch,
            version=version,
            originator='claude-code',
        )
        
        # Group events into turns
        turns = self._group_into_turns(events)
        
        for turn_events in turns:
            turn = self._parse_turn(turn_events)
            if turn:
                session.add_turn(turn)
        
        return session
    
    def _group_into_turns(self, events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group events into conversation turns."""
        turns: List[List[Dict[str, Any]]] = []
        current_turn: List[Dict[str, Any]] = []
        
        for event in events:
            event_type = event.get('type')
            
            # Start a new turn on user message
            if event_type == 'user':
                # Only start new turn if we have a non-tool-result user message
                content = safe_get(event, 'message', 'content', default=[])
                is_tool_result = any(
                    isinstance(block, dict) and block.get('type') == 'tool_result'
                    for block in content
                )
                
                if not is_tool_result and current_turn:
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
        
        # Track tool calls by ID
        tool_call_map: Dict[str, Dict[str, Any]] = {}
        
        for event in events:
            event_type = event.get('type')
            
            if event_type == 'user':
                msg = self._parse_user_message(event)
                if msg and not user_message:
                    user_message = msg
                
                # Extract tool results
                tool_calls.extend(self._extract_tool_results(event, tool_call_map))
            
            elif event_type == 'assistant':
                assistant_message = self._parse_assistant_message(event)
                
                # Extract tool_use blocks
                self._extract_tool_uses(event, tool_call_map)
            
            elif event_type == 'system':
                # Handle system events (like compact_boundary)
                subtype = event.get('subtype')
                if subtype == 'compact_boundary':
                    self.warnings.append(
                        f"Line: compact_boundary event preserved (Codex uses API-level compaction)"
                    )
        
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
        
        if not user_message and not assistant_message and not tool_calls:
            return None
        
        return Turn(
            id=turn_id,
            timestamp=timestamp,
            user_message=user_message,
            assistant_message=assistant_message,
            tool_calls=tool_calls,
        )
    
    def _parse_user_message(self, event: Dict[str, Any]) -> Optional[Message]:
        """Parse a user message event."""
        content_data = safe_get(event, 'message', 'content', default=[])
        
        if not content_data:
            return None
        
        # Filter out tool_result blocks (they're handled separately)
        text_blocks = []
        for block in content_data:
            if isinstance(block, str):
                text_blocks.append(ContentBlock(type='text', content=block))
            elif isinstance(block, dict) and block.get('type') != 'tool_result':
                text_blocks.append(self._parse_content_block(block))
        
        if not text_blocks:
            return None
        
        return Message(
            role='user',
            content=text_blocks,
            timestamp=parse_timestamp(event.get('timestamp')),
        )
    
    def _parse_assistant_message(self, event: Dict[str, Any]) -> Optional[Message]:
        """Parse an assistant message event."""
        content_data = safe_get(event, 'message', 'content', default=[])
        
        if not content_data:
            return None
        
        content_blocks = [self._parse_content_block(block) for block in content_data]
        
        token_usage = safe_get(event, 'message', 'usage')
        
        return Message(
            role='assistant',
            content=content_blocks,
            timestamp=parse_timestamp(event.get('timestamp')),
            token_usage=token_usage if token_usage else None,
        )
    
    def _parse_content_block(self, block: Any) -> ContentBlock:
        """Parse a content block."""
        if isinstance(block, str):
            return ContentBlock(type='text', content=block)
        
        if not isinstance(block, dict):
            return ContentBlock(type='text', content=str(block))
        
        block_type = block.get('type', 'text')
        
        if block_type == 'text':
            return ContentBlock(type='text', content=block.get('text', ''))
        
        elif block_type == 'thinking':
            return ContentBlock(
                type='thinking',
                content=block.get('thinking', ''),
                thinking_content=block.get('thinking', ''),
                signature=block.get('signature'),
            )
        
        elif block_type == 'tool_use':
            return ContentBlock(
                type='tool_use',
                content=block.get('input', {}),
                tool_use_id=block.get('id'),
                tool_name=block.get('name'),
                tool_input=block.get('input', {}),
            )
        
        elif block_type == 'tool_result':
            return ContentBlock(
                type='tool_result',
                content=block.get('content', ''),
                tool_result_id=block.get('tool_use_id'),
            )
        
        else:
            # Unknown block type, preserve as-is
            return ContentBlock(
                type=block_type,
                content=block,
                metadata={'original_block': block},
            )
    
    def _extract_tool_uses(
        self,
        event: Dict[str, Any],
        tool_call_map: Dict[str, Dict[str, Any]]
    ) -> None:
        """Extract tool_use blocks from an assistant message."""
        content_data = safe_get(event, 'message', 'content', default=[])
        
        for block in content_data:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                tool_id = block.get('id')
                if tool_id:
                    tool_call_map[tool_id] = {
                        'name': block.get('name'),
                        'input': block.get('input', {}),
                        'timestamp': event.get('timestamp'),
                    }
    
    def _extract_tool_results(
        self,
        event: Dict[str, Any],
        tool_call_map: Dict[str, Dict[str, Any]]
    ) -> List[ToolCall]:
        """Extract tool_result blocks from a user message."""
        content_data = safe_get(event, 'message', 'content', default=[])
        tool_calls = []
        
        for block in content_data:
            if isinstance(block, dict) and block.get('type') == 'tool_result':
                tool_use_id = block.get('tool_use_id')
                output = block.get('content', '')
                
                if tool_use_id and tool_use_id in tool_call_map:
                    tool_call_map[tool_use_id]['output'] = output
        
        return tool_calls
