from pydantic import BaseModel, Field


class Recipe(BaseModel):
    name: str = Field(..., description="Name of the recipe")
    description: str = Field(..., description="Description of the recipe")
    fun_fact: str = Field(
        ..., description="Fun fact about the recipe", default_factory=""
    )
    ingredients: list[str] = Field(..., description="List of ingredients")
    instructions: list[str] = Field(..., description="List of instructions")
