from .connection import ConnectionManager
from .tool_converter import mcp_tools_to_openai


class Agent:
    """Agentic execution loop that uses a ConnectionManager and an LLM."""

    def __init__(self, connection_manager: ConnectionManager, llm):
        self.connection_manager = connection_manager
        self.llm = llm
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. \n"
                    " When calling tools, pass each parameter as a separate key-value pair, not as a single string."
                ),
            },
        ]
        
    def add_messages(self, messages: list[dict[str, str]]):
        self.messages.extend(messages)

    async def execute(self, task: str, max_iterations: int = 10):
        """Run the agentic loop: bind tools from all servers, invoke LLM, route tool calls."""
        tools = await self.connection_manager.list_all_tools()
        openai_tools = mcp_tools_to_openai(tools)
        llm_with_tools = self.llm.bind_tools(openai_tools)

        self.messages.append({"role": "user", "content": task})

        for i in range(max_iterations):
            print("Iteration", i)
            response = await llm_with_tools.ainvoke(self.messages)
            self.messages.append(response)

            if not response.tool_calls:
                print(f"Final response: {response.content}")
                return response.content

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                parameters = tool_call.get("args", {})
                result = await self.connection_manager.call_tool(tool_name, parameters)
                print(f"Tool {tool_name} returned {result}")
                self.messages.append(
                    {
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": tool_call["id"],
                    }
                )

        print("Max iterations reached")
        return None
