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
#    "packaging",
# ]
# ///

import os

from packaging import utils
from rich.console import Console

console = Console(width=400, color_system="standard")
pypi_package_urls = []

def create_pypi_package_index_url(packages: list[str], url: str):
    wheel_files = [package for package in packages if package.endswith(".whl")]
    for wheel_file in wheel_files:
        parsed_wheel = utils.parse_wheel_filename(wheel_file)

        # Create a tuple of package name and its URL eg:
        # (apache-airflow-providers-amazon, https://pypi.org/project/apache-airflow-providers-amazon/9.2.0rc2)

        pypi_package_urls.append((parsed_wheel[0], f"{url}{parsed_wheel[0]}/{parsed_wheel[1]}"))
    pypi_package_urls.sort()


def set_header(url: str):
    index_type = "TestPyPI" if "test.pypi" in url else "PyPI"
    publisher_name = os.environ.get("PUBLISHER_NAME", "Package")

    header = f"### {publisher_name} distributions published to [{index_type}]({url}) :rocket:\n"

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(header)


def create_publish_summary(url: str):
    create_pypi_package_index_url(files, url)
    set_header(url)

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        for package_name, pypi_package_url in pypi_package_urls:
            f.write(f"[{package_name}]({pypi_package_url})\n")

        f.write('<details><summary><strong>Distributions</strong></summary><pre lang="yaml"><code>')

        for _, pypi_package_url in pypi_package_urls:
            f.write(f"{pypi_package_url}\n")

        f.write("</code></pre></details>")


if __name__ == "__main__":
    dist_file_paths = os.environ.get("DIST_FILE_PATHS", "./dist")
    index_url = os.environ.get("PYPI_INDEX_URL", "https://pypi.org/project/")
    if dist_file_paths:
        files = os.listdir(dist_file_paths)
        files.sort()
        create_publish_summary(index_url)
