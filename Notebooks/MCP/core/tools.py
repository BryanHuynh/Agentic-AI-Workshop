from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal
from fastmcp import FastMCP
from pydantic import BaseModel, Field


class Recipe(BaseModel):
    name: str = Field(..., description="Name of the recipe")
    description: str = Field(..., description="Description of the recipe")
    fun_fact: str = Field(
        ..., description="Fun fact about the recipe", default_factory=""
    )
    ingredients: list[str] = Field(..., description="List of ingredients")
    instructions: list[str] = Field(..., description="List of instructions")


def register_tools(mcp: FastMCP):
    @mcp.tool()
    def create_recipe(recipe: Recipe) -> str:
        """Create a new markdown recipe."""
        file_path = Path(f"./documents/{recipe.name}.json")
        if file_path.exists():
            return f"Error: Document {recipe.name} already exists"
        content = json.dumps(recipe.model_dump(), indent=2)
        file_path.write_text(content, encoding="utf-8")
        return f"Created {recipe.name} recipe"

    @mcp.tool()
    def append_to_recipe_section(
        name: str,
        content: str,
        section: Literal["description", "fun_fact", "ingredients", "instructions"],
    ) -> str:
        """Append content to an existing recipe."""
        file_path = Path(f"./documents/{name}.json")
        if not file_path.exists():
            return f"Error: recipe {name} not found"
        recipe_data = file_path.read_text(encoding="utf-8")
        recipe = Recipe.model_validate_json(recipe_data)
        if section in ["ingredients", "instructions"]:
            current_list = getattr(recipe, section)
            current_list.append(content)
        else:
            current_value = getattr(recipe, section)
            setattr(recipe, section, f"{current_value}\n{content}")
        file_path.write_text(recipe.model_dump_json(indent=2), encoding="utf-8")
        return f"Appended to {name}.json"

    @mcp.tool()
    def search_recipes(query: str) -> str:
        """Search for text across all recipe."""
        results = []
        for file in Path("./documents").glob("*.json"):
            content = file.read_text(encoding="utf-8")
            if query.lower() in content.lower() or query.lower() in file.stem.lower():
                results.append(
                    {
                        "name": file.stem,
                        "uri": f"docs://recipes/{file.stem}",
                        "size": file.stat().st_size,
                        "modified": file.stat().st_mtime,
                    }
                )
        return json.dumps(results, indent=2)

    @mcp.tool()
    def delete_recipe(name: str) -> str:
        """Delete a recipe."""
        file_path = Path(f"./documents/{name}.json")
        if file_path.exists():
            file_path.unlink()
            return f"Deleted {name} recipe"
        return f"Error: {name} not found"
