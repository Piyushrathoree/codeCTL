from client.llm_client import LLMClient
import asyncio


async def main():
    llm_client = LLMClient()

    messages = [{"role": "user", "content": "Hello, how are you?"}]
    async for reponse in llm_client.chat_completion(messages, False):
        print(reponse)


if __name__ == "__main__":
    asyncio.run(main())
