from fastmcp import FastMCP
from core import register_resources, register_tools


mcp = FastMCP("Workshop Server")

register_resources(mcp)
register_tools(mcp)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
