import asyncio
from os import getenv
from typing import Any, AsyncGenerator
from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
from client.response import StreamEventType, StreamEvent, TextDelta, ToolCall
from client.response import TokenUsage
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._max_retries: int = 3

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=getenv("API_KEY"),
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @staticmethod
    def _parse_usage(raw_usage: Any) -> TokenUsage:
        details = getattr(raw_usage, "prompt_tokens_details", None)

        return TokenUsage(
            prompt_tokens=getattr(raw_usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(raw_usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(raw_usage, "total_tokens", 0) or 0,
            cached_tokens=getattr(details, "cached_tokens", 0) or 0,
        )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:

        # created client and kwargs
        client = self.get_client()
        kwargs: dict[str, Any] = {
            "model": "openai/gpt-oss-120b",
            "messages": messages,
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = [{"type": "function", "function": tool} for tool in tools]
            kwargs["tool_choice"] = "auto"

        for attempt in range(self._max_retries + 1):
            try:

                if stream:
                    async for event in self._stream_response(client, kwargs):
                        yield event
                else:
                    event = await self._non_stream_response(client, kwargs)
                    yield event
                return
            except RateLimitError as e:
                if attempt < self._max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"Rate limit exceeded: {e}",
                    )
                    return

            except APIConnectionError as e:
                if attempt < self._max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"API connection error: {e}",
                    )
                    return

            except APIError as e:
                yield StreamEvent(
                    type=StreamEventType.ERROR,
                    error=f"API error: {e.code} - {e.message}",
                )
                return

    async def _stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ) -> AsyncGenerator[StreamEvent, None]:
        response = await client.chat.completions.create(**kwargs)

        finish_reason = None
        usage: TokenUsage | None = None
        tool_call_parts: dict[int, dict[str, str]] = {}

        async for chunk in response:
            if hasattr(chunk, "usage") and chunk.usage:
                usage = self._parse_usage(chunk.usage)

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            if choice.delta.content:

                content = choice.delta.content
                if content:
                    yield StreamEvent(
                        type=StreamEventType.TEXT_DELTA,
                        text_delta=TextDelta(content),
                    )
            if choice.delta.tool_calls:
                for tool_call_delta in choice.delta.tool_calls:
                    index = tool_call_delta.index
                    if index not in tool_call_parts:
                        tool_call_parts[index] = {"id": "", "name": "", "arguments": ""}
                    current_call = tool_call_parts[index]
                    if tool_call_delta.id:
                        current_call["id"] = tool_call_delta.id

                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            current_call["name"] = tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            current_call["arguments"] += (
                                tool_call_delta.function.arguments
                            )

        if tool_call_parts:
            tool_calls = [
                ToolCall(
                    call_id=tool_call["id"],
                    name=tool_call["name"],
                    arguments=tool_call["arguments"],
                )
                for _, tool_call in sorted(tool_call_parts.items())
            ]
            yield StreamEvent(
                type=StreamEventType.TOOL_CALL_COMPLETE,
                tool_calls=tool_calls,
            )

        yield StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            usage=usage,
            finish_reason=finish_reason,
        )

    async def _non_stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ) -> StreamEvent:
        response = await client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        text_delta = None
        if message.content:
            text_delta = TextDelta(content=message.content)

        usage = None
        if response.usage:
            usage = self._parse_usage(response.usage)

        return StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            usage=usage,
        )
