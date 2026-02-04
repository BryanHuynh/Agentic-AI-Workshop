from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit import PromptSession


class RecipesAutocomplete(Completer):
    def __init__(self, words, prompts=[]):
        self.words = words
        self.prompts = prompts

    def get_completions(self, document: Document, complete_event):
        resouce_completions = self.get_completions_resources(document, complete_event)
        prompt_completions = self.get_completions_prompts(document, complete_event)
        return list(resouce_completions) + list(prompt_completions)

    def get_completions_resources(self, document: Document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if "@" not in word_before_cursor:
            return

        for word in self.words:
            if word.startswith(word_before_cursor):
                yield Completion(word, start_position=-len(word_before_cursor))

        
    def get_completions_prompts(self, document: Document, complete_event):
        text = document.text_before_cursor

        # Stage 1: Show prompts when user types /
        if "/" in text and not " " in text.split("/")[-1]:
            prefix = text.split("/")[-1]
            for prompt in self.prompts:
                prompt_name = f"{prompt.name}"
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
                        arg_str = f"--{arg.name}"
                        if arg_str.startswith(prefix):
                            required = " (required)" if arg.required else " (optional)"
                            yield Completion(
                                arg_str,
                                start_position=-len(prefix),
                                display_meta=required,
                            )
