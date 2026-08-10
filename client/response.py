from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass
class TextDelta:
    content: str

    def _str_(self):
        return self.content


@dataclass
class ToolCall:
    call_id: str
    name: str
    arguments: str


class StreamEventType(str, Enum):
    TEXT_DELTA = "text_delta"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"
    TOOL_CALL_COMPLETE = "tool_call_complete"


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
        )


@dataclass
class StreamEvent:
    type: StreamEventType
    text_delta: TextDelta | None = None
    error: str | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass
class Usage:
    prompt_tokens: int
