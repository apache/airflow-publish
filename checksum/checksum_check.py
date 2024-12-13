# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
# ]
# ///
import hashlib
import json
import os
import sys
from typing import Any

from rich.console import Console

console = Console(width=400, color_system="standard")

svn_files = os.listdir()

invalid_checksums = []


def validate_checksum(check_sum_files: list[dict[str, str]], algorithm: str):
    for file_dict in check_sum_files:
        sha_file, check_file = file_dict.values()

        with open(check_file, "rb") as chk:
            digest = hashlib.file_digest(chk, algorithm)

        actual_sha = digest.hexdigest()

        with open(sha_file, "rb") as shf:
            content = shf.read().decode("utf-8").strip()

        expected_sha = content.split()[0]

        if actual_sha != expected_sha:
            invalid_checksums.append(
                {
                    "file": sha_file,
                    "expected_sha": expected_sha,
                    "actual_sha": actual_sha,
                }
            )


def get_valid_files(algorithm: str, files: list[str]) -> list[dict[str, str]]:
    eligible_files = []
    for file in files:
        if file.endswith(algorithm):
            eligible_files.append(
                {
                    "sha_file": file,
                    "check_file": file.replace(algorithm, "").rstrip("."),
                }
            )
    return eligible_files


if __name__ == "__main__":
    check_sum_config: list[dict[str, Any]] = json.loads(
        os.environ.get("CHECK_SUM_CONFIG")
    )

    if not check_sum_config:
        console.print(
            "[red]Error: CHECK_SUM_CONFIG not set[/]\n"
            "You must set `CHECK_SUM_CONFIG` environment variable to run this script"
        )
        sys.exit(1)

    if not svn_files:
        console.print(
            f"[red]Error: No files found in SVN directory at {os.environ.get('REPO_PATH')}[/]"
        )
        sys.exit(1)

    for check in check_sum_config:
        console.print(f"[blue]{check.get('description')}[/]")
        valid_files = get_valid_files(check.get("algorithm"), svn_files)
        validate_checksum(valid_files, check.get("algorithm"))

    if invalid_checksums:
        console.print("[red]Checksum validation failed[/]")
        for invalid in invalid_checksums:
            console.print(f"[red]File: {invalid.get('file')}[/]")
            console.print(f"[red]Expected SHA: {invalid.get('expected_sha')}[/]")
            console.print(f"[red]Actual SHA: {invalid.get('actual_sha')}[/]")
        sys.exit(1)

    console.print("[blue]Checksum validation passed[/]")
