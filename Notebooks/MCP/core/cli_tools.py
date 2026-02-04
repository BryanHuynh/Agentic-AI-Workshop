from dataclasses import dataclass

from .connection import ConnectionManager


@dataclass
class Prompt:
    name: str
    args: dict[str, str]


def parse_prompts(user_input: str) -> list[Prompt] | None:
    """Parse a slash command with named arguments."""
    prompts: list[Prompt] = []

    splits = user_input.split(" ")
    for i in range(len(splits)):
        if splits[i].startswith("/"):
            command = splits[i]
            args = {}
            j = i + 1
            while j < len(splits) - 1 and splits[j].startswith("--"):
                args[splits[j][2:]] = splits[j + 1]
                j += 2
            prompts.append(Prompt(command[1:], args))

    return prompts


def parse_resources(user_input: str, resource_list: list[str]) -> set[str]:
    """Parse resources use in input."""
    resources: set[str] = set()
    for resource in resource_list:
        if resource in user_input:
            resources.add(resource.strip("@"))
    return resources


async def process_input(
    user_input: str,
    recipe_names: list[str],
    connection_manager: ConnectionManager,
) -> list[dict[str, str]]:
    """returns a list of all reources and prompts used in the input. returns list of {role, content} for each resource"""
    prompts_used = parse_prompts(user_input)
    resouces_used = parse_resources(user_input, recipe_names)

    messages: list[dict[str, str]] = []

    for resource in resouces_used:
        contents = await connection_manager.call_resource(
            f"docs://recipes/{resource}", "recipes"
        )
        for item in contents:
            messages.append({"role": "user", "content": item.text})

    for prompt in prompts_used:
        prompt_messages = await connection_manager.call_prompt(prompt.name, prompt.args, "recipes")
        for msg in prompt_messages:
            messages.append({"role": msg.role, "content": msg.content.text})

    return messages
