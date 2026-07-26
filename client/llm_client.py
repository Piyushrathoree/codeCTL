from os import getenv
from typing import Any, AsyncGenerator
from openai import AsyncOpenAI
from client.response import EventType, StreamEvent, TextDelta
from client.response import TokenUsage
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=getenv("OPENROUTER_API_KEY"),
                default_headers={
                    "HTTP-Referer": "https://github.com/inclusionai/ling-3.0-flash",
                    "X-Title": "inclusionai/ling-3.0-flash",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def chat_completion(
        self, messages: list[dict[str, Any]], stream: bool = False, 
    ) -> AsyncGenerator[StreamEvent, None]:
        client = self.get_client()

        kwargs: dict[str, Any] = {
            "model": "inclusionai/ling-3.0-flash:free",
            "messages": messages,
            "stream": stream,
        }

        if stream:
            await self._stream_response(client, kwargs)
        else:
            event = await self._non_stream_response(client, kwargs)
            yield event
        return 

    async def _stream_response(
        self,
        client: AsyncOpenAI,
        kwargs: dict[str, Any],
    ):
        response = await client.chat.completions.create(**kwargs)
        print(response)

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
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=response.usage.prompt_tokens_details.cached_tokens,
            )   

        return StreamEvent(
            type= EventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            usage=usage,
        )