from fastmcp import FastMCP


def register_prompts(mcp: FastMCP):
    @mcp.prompt()
    def create_recipe_prompt(name: str, cuisine: str = "any") -> str:
        """A prompt to create a new recipe with structured fields."""
        return f"""
Create a new recipe for '{name}'
{f" ({cuisine} cuisine)" if cuisine != "any" else ""}. 
Use the create_recipe tool with the following fields:
    - name: A clear, descriptive recipe name
    - description: A short summary of the dish
    - fun_fact: An interesting fact about the dish or its origins
    - ingredients: A complete list of ingredients with quantities
    - instructions: Step-by-step cooking instructions
"""
