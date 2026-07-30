from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from client.response import  TokenUsage


class TextDelta:
    text: str
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None


class AgentEventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"
    AGENT_MESSAGE = "agent_message"
    AGENT_TASK = "agent_task"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"
    # AGENT_TASK_CANCELLED = "agent_task_cancelled"
    # AGENT_TASK_TIMEOUT = "agent_task_timeout"

    # Text stream
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"


@dataclass
class AgentEvent:
    type: AgentEventType
    data: dict[str, any] = field(default_factory=dict)

    @classmethod
    def agent_start(cls, message: str) -> AgentEvent:
        return cls(type=AgentEventType.AGENT_START, data={"message": message})

    @classmethod
    def agent_end(
        cls, response: str | None = None, usage: TokenUsage | None = None
    ) -> AgentEvent:
        return cls(
            type=AgentEventType.AGENT_END,
            data={"response": response, "usage": usage.__dict__ if usage else None},
        )

    @classmethod
    def agent_error(
        cls, error: str, details: dict[str, any] | None = None
    ) -> AgentEvent:
        return cls(
            type=AgentEventType.AGENT_ERROR,
            data={"error": error, "details": details or {}},
        )

    @classmethod
    def text_delta(cls, content: str) -> AgentEvent:
        return cls(type=AgentEventType.TEXT_DELTA, data={"content": content})

    @classmethod
    def text_complete(cls , content: str) -> AgentEvent:
        return cls(type=AgentEventType.TEXT_COMPLETE, data={"content": content})
