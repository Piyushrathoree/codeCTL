from typing import Required
from client.llm_client import LLMClient
import asyncio
import click 


@click.command()
@click.argument("prompt", Required=False)

async def main(
    prompt: str | None = None,
    stream: bool = True,
):
    llm_client = LLMClient()
    messages = [{"role": "user", "content": prompt}]
    async for reponse in llm_client.chat_completion(messages, stream):
        print(reponse)

if __name__ == "__main__":
    asyncio.run(main())
