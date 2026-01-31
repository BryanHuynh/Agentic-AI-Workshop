import json
from pathlib import Path
from typing import Literal
from fastmcp import FastMCP
from .recipe import Recipe
import os

root_dir = Path(__file__).resolve().parent.parent
docs_dir = root_dir / Path("documents")


def register_tools(mcp: FastMCP):
    @mcp.tool()
    def get_recipe(name: str) -> str:
        """Get contents of a recipe by name"""
        file_path = docs_dir / f"{name}.json"
        if not file_path.exists():
            raise mcp.HTTPException(404, f"Recipe {name} not found")
        else:
            return file_path.read_text()

    @mcp.tool()
    def create_recipe(recipe: Recipe) -> str:
        """Create a new markdown recipe.
        Example:
            {
            "recipe": {
                "name": "Margherita Pizza",
                "fun_fact": "Created in Naples in 1889, the pizza was named after Queen Margherita of Savoy. It became the foundation of modern Neapolitan pizza.",
                "description": "Pizza Margherita is a simple pizza topped with tomato sauce, mozzarella, and basil—representing the colors of the Italian flag",
                "ingredients": [
                    "Pizza dough",
                    "1/2 cup San Marzano tomato sauce",
                    "150 g fresh mozzarella",
                    "Fresh basil leaves",
                    "Olive oil",
                    "Salt"
                ],
                "instructions": [
                    "Preheat oven to maximum temperature (250–300°C if possible).",
                    "Stretch dough into a thin circle.",
                    "Spread tomato sauce lightly; season with salt.",
                    "Add torn mozzarella.",
                    "Bake 7–10 minutes until crust is blistered.",
                    "Finish with basil and a drizzle of olive oil."
                ]
                }
            }
        """
        file_path = docs_dir / f"{recipe.name}.json"
        print(file_path)
        if file_path.exists():
            return f"Error: Document {recipe.name} already exists"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(recipe.model_dump(), indent=2)
        file_path.write_text(content, encoding="utf-8")
        return f"Created {recipe.name} recipe"

    @mcp.tool()
    def append_to_recipe_section(
        name: str,
        content: str,
        section: Literal["description", "fun_fact", "ingredients", "instructions"],
    ) -> str:
        """Append content to an existing recipe.

        example:
            name: Margherita Pizza
            content: Enjoy!
            section: Instructions
        """

        file_path = docs_dir / f"{name}.json"
        print(file_path)
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
        updated_content = recipe.model_dump_json(indent=2)
        file_path.write_text(updated_content, encoding="utf-8")
        return f"Appended to {name}.json\n\nUpdated recipe:\n{updated_content}"

    @mcp.tool()
    def search_recipes(query: str) -> str:
        """Search for text across all recipe."""
        results = []
        if not docs_dir.exists():
            return json.dumps(results)
        for file in docs_dir.glob("*.json"):
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
        file_path = docs_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            return f"Deleted {name} recipe"
        return f"Error: {name} not found"
