# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "requests",
#     "python-gnupg",
# ]
# ///
import json
import os
import sys
import tempfile
from typing import Any

import gnupg
import requests
from rich.console import Console

console = Console(width=400, color_system="standard")

svn_files = os.listdir()
temp_signature_key_file_path = tempfile.NamedTemporaryFile().name

invalid_signature_files = []


def download_keys(key_url: str):
    response = requests.get(key_url)
    if response.status_code != 200:
        console.print(
            f"[red]Error: Unable to download signature file from {key_url}: received: {response.status_code}[/]"
        )
        sys.exit(1)

    with open(temp_signature_key_file_path, "w") as key_file:
        key_file.write(response.text)


def validate_signature_with_gpg(signature_check: dict[str, Any]):
    key_url = signature_check.get("keys")

    download_keys(key_url)
    gpg = gnupg.GPG()
    with open(temp_signature_key_file_path, "rb") as key_file:
        gpg.import_keys(key_file.read())

    for file in svn_files:
        if file.endswith(".asc"):
            with open(file, "rb") as singed_file:
                status = gpg.verify_file(
                    fileobj_or_path=singed_file, data_filename=file.replace(".asc", "")
                )
            if not status.valid:
                invalid_signature_files.append(
                    {"file": file, "status": status.valid, "problems": status.problems}
                )
            else:
                console.print(f"[blue]File {file} signed by {status.username}[/]")


if __name__ == "__main__":
    signature_check_config: list[dict[str, Any]] = json.loads(
        os.environ.get("SIGNATURE_CHECK_CONFIG")
    )

    if not signature_check_config:
        console.print(
            "[red]Error: SIGNATURE_CHECK_CONFIG not set[/]\n"
            "You must set `SIGNATURE_CHECK_CONFIG` environment variable to run this script"
        )
        sys.exit(1)

    if not svn_files:
        console.print(
            f"[red]Error: No files found in SVN directory at {os.environ.get('REPO_PATH')}[/]"
        )
        sys.exit(1)

    for check in signature_check_config:
        console.print(f"[blue]{check.get('description')}[/]")
        if check.get("method") == "gpg":
            validate_signature_with_gpg(check)

    if invalid_signature_files:
        for error in invalid_signature_files:
            console.print(
                f"[red]Error: Invalid signature found for {error.get('file')} status: {error.get('status')} problems: {error.get('problems')}[/]"
            )
        sys.exit(1)

    console.print("[blue]All signatures are valid[/]")
