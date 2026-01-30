from pathlib import Path
from fastmcp import FastMCP


def register_resources(mcp: FastMCP):
    @mcp.resource("docs://recipes/list", mime_type="application/json")
    def list_all_recipes():
        """List the name of all recipes in documents"""
        docs = []
        for file in Path("./documents").glob("*.json"):
            docs.append(
                {
                    "name": file.stem,
                    "uri": f"docs://recipes/{file.stem}",
                    "size": file.stat().st_size,
                    "modified": file.stat().st_mtime,
                }
            )
        return docs

    @mcp.resource("docs://recipes/{name}", mime_type="application/json")
    def get_recipe(name: str):
        """Get contents of a recipe by name"""
        file_path = Path(f"./documents/{name}.json")
        if not file_path.exists():
            raise mcp.HTTPException(404, f"Recipe {name} not found")
        else:
            return file_path.read_text()
