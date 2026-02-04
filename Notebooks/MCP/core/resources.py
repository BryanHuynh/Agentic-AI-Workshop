from pathlib import Path
from fastmcp import FastMCP

root_dir = Path(__file__).resolve().parent.parent
docs_dir = root_dir / Path("documents")


def register_resources(mcp: FastMCP):
    @mcp.resource("docs://recipes/list", mime_type="application/json")
    def list_all_recipes():
        """List the name of all recipes in documents"""
        docs = []
        for file in docs_dir.glob("*.json"):
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
        file_path = docs_dir / f"{name}.json"
        if not file_path.exists():
            raise mcp.HTTPException(404, f"Recipe {name} not found")
        else:
            return file_path.read_text()
