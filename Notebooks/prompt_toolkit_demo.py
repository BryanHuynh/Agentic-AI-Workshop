from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit import PromptSession
from typing import List


class Prompt:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class DynamicPromptCompleter(Completer):
    def __init__(self, prompts: List[Prompt]):
        self.prompts = prompts

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        # Stage 1: Show prompts when user types /
        if "/" in text and not " " in text.split("/")[-1]:
            prefix = text.split("/")[-1]
            for prompt in self.prompts:
                prompt_name = f"/{prompt.name}"
                if prompt_name.startswith(prefix):
                    yield Completion(
                        prompt_name,
                        start_position=-len(prefix),
                        display_meta=f"Arguments: {len(prompt.arguments)}",
                    )

        # Stage 2: Show arguments after prompt is selected
        elif " " in text:
            parts = text.split()
            prompt_name = parts[0].lstrip("/")

            # Find matching prompt
            for prompt in self.prompts:
                if prompt.name == prompt_name:
                    prefix = parts[-1] if len(parts) > 1 else ""
                    for arg in prompt.arguments:
                        arg_str = f"--{arg}"
                        if arg_str.startswith(prefix):
                            yield Completion(
                                arg_str,
                                start_position=-len(prefix),
                            )


# Your data
prompts = [
    Prompt("create_recipe_prompt", ["name", "cuisine"]),
    Prompt("create_recipe_prompt_2", ["name", "cuisine"]),
]

completer = DynamicPromptCompleter(prompts)
session = PromptSession(completer=completer)

while True:
    result = session.prompt("$ ")
    print(f"You entered: {result}")
