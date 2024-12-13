# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich",
# ]
# ///

import json
import os
import re
import subprocess
import sys
import tempfile
from functools import cached_property
from typing import Any

from rich.console import Console

console = Console(width=400, color_system="standard")

# We always work on the path provided in the release config eg: below publisher.path is providers/ so
# the current working directory will be providers/
# publisher:
#   name: providers
#   url: https://dist.apache.org/repos/dist/dev/airflow/"
#   path: providers/


class PublishPackagesFinder:
    final_packages_to_publish: list[str] = []
    matched_packages_between_dev_and_release: list[str] = []
    publish_config = json.loads(os.environ.get("PUBLISH_PACKAGES_CONFIG", "{}"))
    temp_svn_dist_release_dir = tempfile.TemporaryDirectory()

    @cached_property
    def dev_svn_files(self):
        return os.listdir()

    @cached_property
    def svn_dist_release_dir(self):
        return self.temp_svn_dist_release_dir.name

    @staticmethod
    def is_extension_matched(file: str, pattern: str) -> bool:
        match = re.match(pattern, file)
        return match and file.endswith(match.group(1))

    @cached_property
    def dist_path(self):
        # Path where the final packages will be moved and pushed to artifactory
        if not os.path.exists(os.environ.get("DIST_PATH")):
            os.makedirs(os.environ.get("DIST_PATH"))
        return os.environ.get("DIST_PATH")

    @cached_property
    def release_type(self):
        return self.publish_config.get("release-type")

    @cached_property
    def extension_exclude_config(self):
        return self.publish_config.get("exclude_extensions")

    @cached_property
    def github_workspace(self):
        return os.environ.get("GITHUB_WORKSPACE")

    @staticmethod
    def extract_package_names(
        package_name_config: list[dict[str, Any]], lookup_packages: list[str]
    ) -> list[str]:
        """
        Extract the package names based on the regex pattern provided in the package_names config
        :param package_name_config:

              package_names:
                   - type: regex
                     pattern: "(apache_airflow_providers.*?)(?=rc)"

             eg: for a rc package apache-airflow-1.0.0rc1.targ.gz it will extract the package name as "apache-airflow-providers-1.0.0"
        :param lookup_packages: List of packages to check for the package names
        :return: matched package names
        """
        package_names: set[str] = set()

        for package_name_config in package_name_config:
            if package_name_config.get("type") == "regex":
                regex_pattern = package_name_config.get("pattern")
                package_names.update(
                    match.group(1)
                    for file in lookup_packages
                    if (match := re.match(regex_pattern, file))
                )

        return list(package_names)

    def find_matched_packages_between_dev_and_release(
        self, compare_config: dict[str, Any]
    ):
        """
        Find the matched packages between dev and release folder based on the package names. the comparison works with config provided in compare
         section of the release config.
             compare:
              url: "https://dist.apache.org/repos/dist/release/airflow/"
              path: "providers/"
              package_names:
               - type: regex
                 pattern: "(apache_airflow_providers.*?)(?=rc)"

         Here the package names are extracted based on the regex pattern provided, here in this case for a rc package apache-airflow-1.0.0rc1.targ.gz
         it will extract the package name as "apache-airflow-providers-1.0.0" and compare with the release folder packages. below it used startswith
         to compare the package names. if it matches it considers the package to final publish list.

        :param compare_config: Configuration to compare the packages between dev and release folder, likely the dist
        :return: None
        """

        # This dev_package_names contains all the packages without rc or based on regex pattern extracted name
        # if dev package name is "apache-airflow-1.0.0rc1.targ.gz" and
        # extract_package_names function returns package name like "apache-airflow-1.0.0"
        # (it depends on regex pattern provided in package_names)

        dev_package_names = self.extract_package_names(
            compare_config.get("package_names"), self.dev_svn_files
        )

        if not dev_package_names:
            console.print(
                f"[red]No package names found in {os.getcwd()} with {compare_config.get('package_names')} [/]"
            )
            sys.exit(1)

        inner_path = compare_config.get("path")
        path_to_lookup = os.path.join(self.svn_dist_release_dir, inner_path)

        release_folder_packages = os.listdir(path=path_to_lookup)
        self.matched_packages_between_dev_and_release = [
            package
            for package in release_folder_packages
            if any(
                package.startswith(package_name) for package_name in dev_package_names
            )
        ]

        if not self.matched_packages_between_dev_and_release:
            svn_full_path = os.path.join(
                self.publish_config.get("compare").get("url"), inner_path
            ).strip()

            console.print(
                f"[red]No matched packages found between {os.getcwd()} and {svn_full_path}[/]"
            )
            sys.exit(1)

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
                    if self.is_extension_matched(package, regex_pattern)
                ]
        if exclude_packages:
            console.print("[blue]Following packages excluded: [/]")
            console.print(f"[blue]{exclude_packages}[/]")
            console.print("\n")

        return list(set(packages) - exclude_packages)

    def filter_rc_packages_to_publish(
        self, exclude_extensions_config: list[dict[str, Any]]
    ):
        """
        Filter the packages to publish based on the release type RC_VERSION, for rc release we directly consider
        packages from dev svn folder path provided in the release config

        :param exclude_extensions_config:  Configuration to exclude the final publish packages based on the extension, eg: .asc, .sha512
        :return:
        """
        packages_to_publish = self.exclude_packages_to_publish(
            packages=self.dev_svn_files, exclude_config=exclude_extensions_config
        )
        self.final_packages_to_publish.extend(packages_to_publish)

    def move_packages_to_dist_folder(self, packages_path: str):
        """
        Move the packages to dist folder

        :param packages_path: location of the packages, where the packages are checked out
        :return:
        """

        if not self.final_packages_to_publish:
            console.print("[red]No packages found to publish[/]")
            sys.exit(1)

        for package_name in self.final_packages_to_publish:
            full_path = os.path.join(packages_path, package_name)
            subprocess.run(["mv", full_path, self.dist_path], check=True)

    def filter_pypi_version_packages_to_publish(
        self,
        compare_config: dict[str, Any],
        extension_exclude_config: list[dict[str, Any]],
    ):
        """
        :param compare_config: Configuration to compare the packages between dev and release folder, likely the dist
            release svn folder
            {
              "url": "https://dist.apache.org/repos/dist/release/airflow/",
              "path": "providers/",
              "package_names": [
                {
                  "type": "regex",
                  "pattern": "(apache_airflow_providers.*?)(?=rc)"
                }
              ]
            }
        :param extension_exclude_config:  Configuration to exclude the final publish packages based on the extension, eg: .asc, .sha512
        :return: None
        """

        self.find_matched_packages_between_dev_and_release(compare_config)

        # self.matched_packages_between_dev_and_release
        # package names contains all the packages without
        # rc or based on regex pattern extracted name

        self.final_packages_to_publish.extend(
            self.exclude_packages_to_publish(
                self.matched_packages_between_dev_and_release, extension_exclude_config
            )
        )

    @staticmethod
    def checkout_svn_repo(repo_url: str, path_to_checkout: str):
        console.print(
            f"[blue]Checking out files from {repo_url} to {path_to_checkout}[/]"
        )
        subprocess.run(["svn", "co", repo_url, path_to_checkout], check=True)

    def run(self):
        try:
            if self.release_type == "RC_VERSION":
                self.filter_rc_packages_to_publish(self.extension_exclude_config)

                # For RC release we directly move the packages from the provided source path.
                # also the current working directory is the source path
                self.move_packages_to_dist_folder(os.getcwd())

            elif self.release_type == "PYPI_VERSION":
                compare_config = self.publish_config.get("compare")
                repo_url = compare_config.get("url")
                self.checkout_svn_repo(repo_url, self.svn_dist_release_dir)
                self.filter_pypi_version_packages_to_publish(
                    compare_config, self.extension_exclude_config
                )

                # For PYPI_VERSION release we move the packages from the release folder to dist folder,
                # only matched packages between dev and release folder packages will be moved to dist folder for final publishing

                release_files_path = os.path.join(
                    self.svn_dist_release_dir, compare_config.get("path")
                )
                self.move_packages_to_dist_folder(release_files_path)
            else:
                console.print(f"[red]Invalid release type {self.release_type}[/]")
                sys.exit(1)

            if os.environ.get("MODE") == "VERIFY":
                console.print(
                    "[blue]To publish these packages to PyPI, set the mode=RELEASE in workflow and run[/]"
                )
            else:
                console.print("[blue]Following packages will be published to PyPI[/]")

            for package in self.final_packages_to_publish:
                console.print(f"[blue]{package}[/]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            sys.exit(1)


if __name__ == "__main__":
    PublishPackagesFinder().run()
