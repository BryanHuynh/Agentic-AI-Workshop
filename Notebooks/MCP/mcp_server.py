from fastmcp import FastMCP
from core import register_resources, register_tools, register_prompts


mcp = FastMCP("Workshop Server")

register_resources(mcp)
register_tools(mcp)
register_prompts(mcp)


if __name__ == "__main__":
    mcp.run(transport='sse')
    
    
