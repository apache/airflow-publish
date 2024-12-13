# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "pyyaml",
#     "jsonschema",
# ]
# ///
import json
import os
import sys

import yaml
from jsonschema.validators import validator_for
from rich.console import Console

console = Console(width=200, color_system="standard")
config_file = os.environ.get("RELEASE_CONFIG_FILE")
schema_path = os.environ.get("RELEASE_CONFIG_SCHEMA")

if not config_file:
    console.print(
        "[red]Error:  RELEASE_CONFIG_FILE not set[/]\n"
        "You must set `RELEASE_CONFIG_FILE` environment variable to run this script"
    )
    sys.exit(1)


def set_outputs(yml_config):
    """
    Set the outputs to GITHUB_OUTPUT
    :param yml_config:
    :return: None
    """

    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        for root_element, root_values in yml_config.items():
            for key, value in root_values.items():
                if isinstance(value, dict) or isinstance(value, list):
                    f.write(f"{root_element}-{key}={json.dumps(value)}\n")
                else:
                    f.write(f"{root_element}-{key}={value}\n")


def read_file(path) -> dict:
    """
    Read the file and return the data
    :param path:
    :return:
    """
    if path.endswith(".yml") or path.endswith(".yaml"):
        with open(path) as file:
            return yaml.safe_load(file)

    if path.endswith(".json"):
        with open(path) as file:
            return json.load(file)


def validate_config(yml_config):
    """
    Validate the release config against the schema

    :param yml_config:
    :return: None
    """
    exit_code = 0

    with open(schema_path) as schema_file:
        schema = json.loads(schema_file.read())

    validator = validator_for(schema)
    validator.check_schema(schema)

    for error in validator(schema).iter_errors(yml_config):
        exit_code = 1
        console.print(f"[red]Error: {error}[/]")

    if exit_code:
        console.print("[red]Release config validation failed[/]")


if __name__ == "__main__":
    yml_config_data = read_file(config_file)
    console.print("[blue]Release config validation started[/]")
    validate_config(yml_config_data)
    console.print("[blue]Release config validation passed[/]")
    console.print("[blue]Setting outputs to GITHUB_OUTPUT[/]")
    set_outputs(yml_config_data)
    console.print("[blue]Completed setting outputs to GITHUB_OUTPUT[/]")
    console.print("[blue]Release config validation completed successfully[/]")
    console.print("")
    console.print("[blue]Starting validations for:[/]")
    console.print(f"[blue]  Project: {yml_config_data.get('project').get('name')}[/]")
    console.print(
        f"[blue]  Description: {yml_config_data.get('project').get('description')}[/]"
    )
    console.print(
        f"[blue]  Publisher: {yml_config_data.get('publisher').get('name')}[/]"
    )
