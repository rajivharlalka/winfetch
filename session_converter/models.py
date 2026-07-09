"""Intermediate data models for session conversion."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """A content block within a message."""
    
    type: str = Field(..., description="Block type: text, thinking, tool_use, or tool_result")
    content: Union[str, Dict[str, Any]] = Field(..., description="Block content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # For tool_use blocks
    tool_use_id: Optional[str] = Field(None, description="Tool use identifier")
    tool_name: Optional[str] = Field(None, description="Tool name")
    tool_input: Optional[Dict[str, Any]] = Field(None, description="Tool input parameters")
    
    # For tool_result blocks
    tool_result_id: Optional[str] = Field(None, description="Reference to tool_use_id")
    
    # For thinking blocks
    thinking_content: Optional[str] = Field(None, description="Internal reasoning content")
    signature: Optional[str] = Field(None, description="Thinking signature")


class ToolCall(BaseModel):
    """A tool invocation with its result."""
    
    id: str = Field(..., description="Unique tool call identifier")
    name: str = Field(..., description="Tool name")
    input: Dict[str, Any] = Field(..., description="Tool input parameters")
    output: Optional[str] = Field(None, description="Tool execution output")
    timestamp: datetime = Field(..., description="When the tool was called")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Message(BaseModel):
    """A message from user or assistant."""
    
    role: str = Field(..., description="Message role: user, assistant, system")
    content: List[ContentBlock] = Field(default_factory=list, description="Message content blocks")
    timestamp: datetime = Field(..., description="Message timestamp")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Turn(BaseModel):
    """A conversation turn (user message + assistant response + tool calls)."""
    
    id: str = Field(..., description="Turn identifier")
    timestamp: datetime = Field(..., description="Turn start timestamp")
    user_message: Optional[Message] = Field(None, description="User's message")
    assistant_message: Optional[Message] = Field(None, description="Assistant's response")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tool calls in this turn")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Session(BaseModel):
    """A complete session with all turns."""
    
    id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(..., description="Session start timestamp")
    cwd: str = Field(..., description="Working directory")
    model: Optional[str] = Field(None, description="AI model used")
    turns: List[Turn] = Field(default_factory=list, description="Conversation turns")
    
    # Git information
    git_branch: Optional[str] = Field(None, description="Git branch")
    git_commit: Optional[str] = Field(None, description="Git commit hash")
    git_repository: Optional[str] = Field(None, description="Git repository URL")
    
    # Additional metadata
    version: Optional[str] = Field(None, description="CLI version")
    originator: Optional[str] = Field(None, description="Tool that created the session")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def add_turn(self, turn: Turn) -> None:
        """Add a turn to the session."""
        self.turns.append(turn)
    
    def get_turn_count(self) -> int:
        """Get the number of turns."""
        return len(self.turns)
    
    def get_tool_call_count(self) -> int:
        """Get the total number of tool calls."""
        return sum(len(turn.tool_calls) for turn in self.turns)
    
    def get_event_count(self) -> int:
        """Estimate the total number of events."""
        count = 0
        for turn in self.turns:
            if turn.user_message:
                count += 1
            if turn.assistant_message:
                count += 1
            count += len(turn.tool_calls)
        return count


class ConversionStats(BaseModel):
    """Statistics about a conversion operation."""
    
    input_file: str
    output_file: Optional[str] = None
    source_format: str
    target_format: str
    
    session_id: str
    turn_count: int
    tool_call_count: int
    event_count: int
    
    duration_seconds: float
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
