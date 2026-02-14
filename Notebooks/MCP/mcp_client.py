import asyncio

from core.connection import ConnectionManager
from core.agent import Agent
from core.cli_chat import CLIChat
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os

load_dotenv()
model = os.getenv("model")
mistral_key = os.getenv("mistral_key")


async def main():
    manager = ConnectionManager()
    manager.add_server("recipes", "http://127.0.0.1:8000/sse")

    llm = ChatMistralAI(model=model, mistral_api_key=mistral_key)
    agent = Agent(connection_manager=manager, llm=llm)

    chat = CLIChat(agent=agent, connection_manager=manager)

    async with manager.connect_all():
        await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
