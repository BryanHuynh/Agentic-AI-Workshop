import json
import asyncio
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_ollama import ChatOllama
from langchain_classic.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser


class MCPClient:
    """Client that connects to an MCP server, selects tools via an LLM, and executes them."""

    def __init__(self, server_url: str, llm_model_name: str = "qwen2.5:7b"):
        self.server_url = server_url
        self.chat_llm = ChatOllama(model=llm_model_name)

    @asynccontextmanager
    async def connect(self):
        """Open an SSE connection to the MCP server and yield a ClientSession."""
        async with sse_client(url=self.server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    async def list_tools(self, session: ClientSession) -> list:
        """Return the list of tools registered on the server."""
        result = await session.list_tools()
        return result.tools

    async def call_tool(self, session: ClientSession, tool_name: str, parameters: dict):
        """Execute a tool on the MCP server and return the result."""
        print(
            f"Calling tool {tool_name} with parameters: \n {json.dumps(parameters, indent=2)}"
        )
        result = await session.call_tool(tool_name, parameters)
        return result

    @staticmethod
    def _mcp_tools_to_openai(tools: list) -> list:
        """Convert MCP tool objects to OpenAI function-calling format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
            )
        return openai_tools

    async def execute(self, task: str, max_iterations: int = 10):
        """End-to-end: connect, let the LLM pick tools in a loop until done."""
        async with self.connect() as session:
            tools = await self.list_tools(session)
            print("available tools:", [tool.name for tool in tools])
            openai_tools = self._mcp_tools_to_openai(tools)
            llm_with_tools = self.chat_llm.bind_tools(openai_tools)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. \n When calling tools, pass each parameter as a separate key-value pair, not as a single string."
                    ),
                },
                {"role": "user", "content": task},
            ]

            for i in range(max_iterations):
                print("Iteration", i)
                response = await llm_with_tools.ainvoke(messages)
                messages.append(response)

                if not response.tool_calls:
                    print(f"Final response: {response.content}")
                    return response.content

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    parameters = tool_call.get("args", {})
                    result = await self.call_tool(session, tool_name, parameters)
                    print(f"Tool {tool_name} returned {result}")
                    messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                            "tool_call_id": tool_call["id"],
                        }
                    )

            print("Max iterations reached")
            return None


if __name__ == "__main__":
    client = MCPClient(server_url="http://127.0.0.1:8000/sse")
    # result = asyncio.run(client.execute("Create a new American Smash Burger Recipe"))
    # result = asyncio.run(
    #     client.execute(
    #         "Add an instruction to the American Smash Burger recipe to add sesame seeds as add it to the ingredients if it is not already there"
    #     )
    # )
    # result = asyncio.run(
    #     client.execute(
    #         "Find a recipe with sesame seeds and also add instructions to add cheese and bacon"
    #     )
    # )
    result = asyncio.run(
        client.execute(
            "Make a new recipe with instant noodles, chicken, and rice and a slice of cheese"
        )
    )
    # print(result)
