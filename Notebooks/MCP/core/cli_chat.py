import json
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.history import InMemoryHistory

from .recipes_autocomplete import RecipesAutocomplete
from .connection import ConnectionManager
from .agent import Agent

from .cli_tools import parse_prompts, parse_resources, process_input


class CLIChat:
    def __init__(self, agent: Agent, connection_manager: ConnectionManager):
        self.agent = agent
        self.connection_manager = connection_manager
        self.session = PromptSession(history=InMemoryHistory())

    async def run(self):
        recipes = await self.connection_manager.call_resource(
            "docs://recipes/list", "recipes"
        )
        prompts = await self.connection_manager.list_all_prompts_from_server("recipes")
        data = json.loads(recipes[0].text)
        recipe_names = [f"@{recipe['name']}" for recipe in data]

        completer = FuzzyCompleter(RecipesAutocomplete(recipe_names, prompts))
        while True:
            user_input = await self.session.prompt_async(
                "Enter something: ", completer=completer
            )
            if user_input == "exit":
                break
            else:
                resources_messages = await process_input(
                    user_input, recipe_names, self.connection_manager
                )
                self.agent.add_messages(resources_messages)
                result = await self.agent.execute(user_input)
                if result:
                    print(result)
