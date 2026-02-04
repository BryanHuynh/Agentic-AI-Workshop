import json
from contextlib import asynccontextmanager
from typing import Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

from .tool_converter import mcp_tools_to_openai


class ServerConnection:
    """Wraps a single MCP server URL with connection and tool/resource access."""

    def __init__(self, url: str):
        self.url = url
        self._session: Optional[ClientSession] = None

    @asynccontextmanager
    async def connect(self):
        """Open an SSE connection to the MCP server and yield a ClientSession."""
        async with sse_client(url=self.url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self._session = session
                try:
                    yield session
                finally:
                    self._session = None

    async def list_tools(self, session: Optional[ClientSession] = None):
        """Return the list of tools registered on the server."""
        s = session or self._session
        if s is None:
            async with self.connect() as s:
                return await self.list_tools(s)
        result = await s.list_tools()
        return result.tools if result else []

    async def list_resources(self, session: Optional[ClientSession] = None):
        """Return the list of resources registered on the server."""
        s = session or self._session
        if s is None:
            async with self.connect() as s:
                return await self.list_resources(s)
        result = await s.list_resources()
        return result.resources if result else []

    async def call_tool(
        self, tool_name: str, parameters: dict, session: Optional[ClientSession] = None
    ):
        """Execute a tool on the MCP server and return the result."""
        s = session or self._session
        if s is None:
            raise RuntimeError("No active session. Use connect() first.")
        print(
            f"Calling tool {tool_name} with parameters:\n {json.dumps(parameters, indent=2)}"
        )
        return await s.call_tool(tool_name, parameters)

    async def call_resource(
        self, resource_name: str, session: Optional[ClientSession] = None
    ):
        """Read a resource from the MCP server and return the result."""
        s = session or self._session
        if s is None:
            async with self.connect() as s:
                return await self.call_resource(resource_name, s)
        result = await s.read_resource(resource_name)
        return [resource for resource in result.contents]

    async def list_prompts(
        self, session: Optional[ClientSession] = None
    ):
        """gets a prompt from the MCP server and return the result."""
        s = session or self._session
        if s is None:
            async with self.connect() as s:
                return await self.call_prompt(s)
        result = await s.list_prompts(params={})
        return [prompt for prompt in result.prompts]
    
    async def call_prompt(
        self, prompt_name: str, parameters: dict, session: Optional[ClientSession] = None
    ):
        """Execute a prompt on the MCP server and return the result."""
        s = session or self._session
        if s is None:
            async with self.connect() as s:
                return await self.call_prompt(prompt_name, parameters, s)
        result = await s.get_prompt(prompt_name, parameters)
        return [prompt for prompt in result.messages]
    
class ConnectionManager:
    """Manages multiple MCP server connections keyed by name."""

    def __init__(self):
        self._servers: dict[str, ServerConnection] = {}
        self._tool_map: dict[str, str] = {}  # tool_name -> server_name

    def add_server(self, name: str, url: str):
        """Register a server by name and URL."""
        self._servers[name] = ServerConnection(url)

    def remove_server(self, name: str):
        """Remove a registered server."""
        self._servers.pop(name, None)
        self._tool_map = {
            tool: server for tool, server in self._tool_map.items() if server != name
        }

    @asynccontextmanager
    async def connect_all(self):
        """Open persistent sessions to all registered servers.

        Uses nested async context managers to keep all sessions alive
        for the duration of the block.
        """
        # We build a stack of context managers manually so we can support
        # an arbitrary number of servers.
        from contextlib import AsyncExitStack

        async with AsyncExitStack() as stack:
            for name, conn in self._servers.items():
                await stack.enter_async_context(conn.connect())
            yield self

    async def list_all_tools(self) -> list:
        """Aggregate tools from all connected servers.

        Returns OpenAI-format tool definitions. Internally tracks which
        server each tool belongs to for routing.
        """
        self._tool_map.clear()
        all_tools = []
        for server_name, conn in self._servers.items():
            tools = await conn.list_tools()
            for tool in tools:
                self._tool_map[tool.name] = server_name
            all_tools.extend(tools)
        return all_tools

    async def call_tool(self, tool_name: str, parameters: dict):
        """Route a tool call to the correct server."""
        server_name = self._tool_map.get(tool_name)
        if server_name is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        conn = self._servers[server_name]
        return await conn.call_tool(tool_name, parameters)

    async def call_resource(
        self, resource_name: str, server_name: Optional[str] = None
    ):
        """Call a resource on a specific server, or the first one if not specified."""
        if server_name:
            return await self._servers[server_name].call_resource(resource_name)
        # Default: try the first server
        for conn in self._servers.values():
            return await conn.call_resource(resource_name)
        raise RuntimeError("No servers registered.")

    async def list_all_prompts_from_server(self, server_name: str):
        """Call a prompt on a specific server, or the first one if not specified."""
        if self._servers[server_name]:
            return await self._servers[server_name].list_prompts()
        else:
            raise RuntimeError(f"Server {server_name} not found.")
        
    async def call_prompt(self, prompt_name: str, parameters: dict, server_name: Optional[str] = None):
        """Call a prompt on a specific server, or the first one if not specified."""
        if server_name:
            return await self._servers[server_name].call_prompt(prompt_name, parameters)
        # Default: try the first server
        for conn in self._servers.values():
            return await conn.call_prompt(prompt_name, parameters)
        raise RuntimeError("No servers registered.")

    def get_server(self, name: str) -> ServerConnection:
        """Get a specific server connection by name."""
        return self._servers[name]

    @property
    def server_names(self) -> list[str]:
        return list(self._servers.keys())
