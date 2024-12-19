# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
#     "tabulate",
# ]
# ///

import json
import os
import re
import subprocess
import sys
from functools import cached_property
from typing import Any

from rich.console import Console
from tabulate import tabulate

console = Console(width=400, color_system="standard")

# We always work on the path provided in the release config eg: below publisher.path is providers/ so
# the current working directory will be providers/
# publisher:
#   name: providers
#   url: https://dist.apache.org/repos/dist/dev/airflow/
#   path: providers/pypi-rc/


class PublishPackagesFinder:
    final_packages_to_publish: list[str] = []

    @cached_property
    def artifacts_config(self):
        return json.loads(os.environ.get("ARTIFACTS_CONFIG", "{}"))

    @cached_property
    def dev_svn_files(self):
        """
        Get the list of files in the current directory
        :return:
        """
        files = [file for file in os.listdir() if os.path.isfile(file)]

        if not files:
            console.print(f"[red]No packages found in the {os.getcwd()}[/]")
            sys.exit(1)
        return files

    @staticmethod
    def is_matched(file: str, pattern: str) -> bool:
        match = re.match(pattern, file)
        if match and file.endswith(match.group(1)):
            return True
        return False

    @cached_property
    def dist_path(self):
        # Path where the final packages will be moved and pushed to artifactory
        dist_path = os.environ.get("DIST_PATH")
        if not os.path.exists(dist_path):
            os.makedirs(dist_path)
        return dist_path

    @cached_property
    def exclude_config(self):
        return self.artifacts_config.get("exclude")

    @staticmethod
    def print_table_format(packages: list[str], headers: list[str]):
        """
        Print the packages in tabulate format

        :param packages: list of packages
        :param headers: headers for the table
        :return:
        """
        packages_tabulate_format = [[package] for package in packages]

        console.print(
            tabulate(
                packages_tabulate_format,
                headers=headers,
                tablefmt="grid"
            )
        )

    def exclude_packages_to_publish(
        self, packages: list[str], exclude_config: list[dict[str, Any]]
    ) -> list[str]:
        """
        Exclude the packages based on the exclude config

        :param packages:  List of packages to exclude
        :param exclude_config: Configuration to exclude the final publish packages based on the extension, eg: .asc, .sha512
        :return: list of packages to publish
        """

        exclude_packages: set[str] = set()
        for exclude_config in exclude_config:
            if exclude_config.get("type") == "regex":
                regex_pattern = exclude_config.get("pattern")
                [
                    exclude_packages.add(package)
                    for package in packages
                    if self.is_matched(package, regex_pattern)
                ]
        if exclude_packages:
            console.print("[blue]Following packages excluded: [/]")
            self.print_table_format(list(exclude_packages), ["Packages"])
            console.print("\n")

        return list(set(packages) - exclude_packages)

    def move_packages_to_dist_folder(self, packages_path: str):
        """
        Move the packages to dist folder

        :param packages_path: location of the packages, where the packages are checked out
        :return:
        """

        if not self.final_packages_to_publish:
            console.print("[red]No packages found to move[/]")
            sys.exit(1)

        for package_name in self.final_packages_to_publish:
            full_path = os.path.join(packages_path, package_name)
            subprocess.run(["mv", full_path, self.dist_path], check=True)

    def run(self):
        try:
            console.print(f"[blue]{self.artifacts_config.get('description')}[/]")
            console.print()

            self.final_packages_to_publish = self.exclude_packages_to_publish(
                self.dev_svn_files, self.exclude_config
            )

            self.move_packages_to_dist_folder(os.getcwd())

            if os.environ.get("MODE", "VERIFY") == "VERIFY":
                console.print(
                    "[blue]To publish these packages to PyPI, set the mode=RELEASE in workflow and run[/]"
                )
            else:
                console.print("[blue]Following packages will be published to PyPI.[/]")

            self.print_table_format(self.final_packages_to_publish, ["Packages"])

        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            sys.exit(1)


if __name__ == "__main__":
    PublishPackagesFinder().run()
