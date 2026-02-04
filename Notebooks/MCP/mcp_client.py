import asyncio

from langchain_ollama import ChatOllama

from core.connection import ConnectionManager
from core.agent import Agent
from core.cli_chat import CLIChat


async def main():
    manager = ConnectionManager()
    manager.add_server("recipes", "http://127.0.0.1:8000/sse")

    llm = ChatOllama(model="qwen2.5:7b")
    agent = Agent(connection_manager=manager, llm=llm)

    chat = CLIChat(agent=agent, connection_manager=manager)

    async with manager.connect_all():
        await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
