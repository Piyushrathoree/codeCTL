from prompts.system import get_system_prompt
from dataclasses import dataclass
from utils.text import count_tokens
from typing import Any
import json


@dataclass
class MessageItem:
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    token_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": self.role}

        if self.content is not None:
            result["content"] = self.content

        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls

        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id

        if self.name is not None:
            result["name"] = self.name

        return result

class ContextManager:
    def __init__(self, max_history_tokens: int = 4_000) -> None:
        self._system_prompt = get_system_prompt()
        self._model_name = "openai/gpt-oss-120b"
        self._messages: list[MessageItem] = []
        self._max_history_tokens = max_history_tokens

    def add_user_message(self, content: str) -> None:
        item = MessageItem(
            role="user",
            content=content,
            token_count=count_tokens(content, self._model_name),
        )
        self._messages.append(item)

    def add_assistant_message(self, content: str) -> None:
        item = MessageItem(
            role="assistant",
            content=content or "",
            token_count=count_tokens(content, self._model_name),
        )
        self._messages.append(item)

    def add_assistant_tool_calls(self, tool_calls: list[dict[str, Any]]) -> None:
        self._messages.append(
            MessageItem(
                role="assistant",
                tool_calls=tool_calls,
                token_count=count_tokens(json.dumps(tool_calls), self._model_name),
            )
        )

    def add_tool_result(
      self,
      tool_call_id: str,
      name: str,
      content: str,
  ) -> None:
      self._messages.append(
          MessageItem(
              role="tool",
              content=content,
              tool_call_id=tool_call_id,
              name=name,
              token_count=count_tokens(content, self._model_name),
          )
      )

    def get_messages(self) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []

        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        selected: list[MessageItem] = []
        remaining_tokens = self._max_history_tokens
        for item in reversed(self._messages):
            item_tokens = item.token_count or 0

            # always keep the latest message
            if selected and item_tokens > remaining_tokens:
                break
            selected.append(item)
            remaining_tokens -= item_tokens

        messages.extend(item.to_dict() for item in reversed(selected))
        return messages

    def clear(self) -> None:
        self._messages.clear()
