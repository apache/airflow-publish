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
import json
import os.path
import tempfile

import pytest
from pytest_unordered import unordered

from artifacts.publish_packages_finder import PublishPackagesFinder


def write_data(files, path):
    if not os.path.exists(path):
        os.makedirs(path)
    for file in files:
        with open(os.path.join(path, file), "w") as f:
            f.write("test")


class TestPublishPackagesFinder:
    @pytest.mark.parametrize(
        "packages, exclude_config, expected",
        [
            pytest.param(
                [
                    "airflow-provider-1.0.0.tar.gz.asc",
                    "package3-1.0.0.tar.gz",
                    "package2-1.0.0.py3-none-any.whl.sha512",
                    "package4-1.0.0.tar.gz",
                ],
                [
                    {
                        "type": "regex",
                        "pattern": r".*(tar.gz.asc|py3-none-any.whl.sha512)$",
                    },
                ],
                [
                    "package4-1.0.0.tar.gz",
                    "package3-1.0.0.tar.gz",
                ],
                id="exclude_few_package_extensions",
            ),
            pytest.param(
                [
                    "airflow-provider-1.0.0.tar.gz.asc",
                    "package2-1.0.0.py3-none-any.whl.sha512",
                ],
                [
                    {
                        "type": "regex",
                        "pattern": r".*(tar.gz.asc|py3-none-any.whl.sha512)$",
                    },
                ],
                [],
                id="exclude_all_given_packages",
            ),
        ],
    )
    def test_exclude_packages_to_publish(self, packages, exclude_config, expected):
        publish_packages_finder = PublishPackagesFinder()
        after_exclude_packages = publish_packages_finder.exclude_packages_to_publish(
            packages=packages, exclude_config=exclude_config
        )
        assert after_exclude_packages == unordered(expected)

    def test_dev_svn_files(self):
        publish_packages_finder = PublishPackagesFinder()
        with tempfile.TemporaryDirectory() as temp_dir:
            files = [
                "file1.tar.gz",
                "file2.tar.gz.asc",
                "file3.py3-none-any.whl.sha512",
            ]
            write_data(files, temp_dir)
            os.chdir(temp_dir)
            assert publish_packages_finder.dev_svn_files == unordered(files)

    def test_dev_svn_files_empty(self):
        publish_packages_finder = PublishPackagesFinder()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with pytest.raises(SystemExit):
                publish_packages_finder.dev_svn_files()

    @pytest.mark.parametrize(
        "file, pattern, expected",
        [
            pytest.param(
                "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                ".*(.asc|.sha512)$",
                False,
            ),
            pytest.param(
                "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                ".*(.asc|.sha512)$",
                True,
            ),
            pytest.param(
                "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                ".*(.asc|.sha512)$",
                False,
            ),
            pytest.param(
                "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.sha512",
                ".*(.asc|.sha512)$",
                True,
            ),
            pytest.param("apache_airflow-2.10.4.tar.gz.asc", "(apache_airflow-.*?)$", True),
        ],
    )
    def test_is_matched(self, file, pattern, expected):
        """
        Test is_matched method of PublishPackagesFinder, which checks if the file is matched with the pattern

        """
        publish_packages_finder = PublishPackagesFinder()
        assert publish_packages_finder.is_matched(file, pattern) == expected

    def test_exclude_config(self):
        publish_packages_finder = PublishPackagesFinder()
        publish_packages_finder.artifacts_config = {
            "exclude": [{"type": "regex", "pattern": r".*(tar.gz.asc|py3-none-any.whl.sha512)$"}]
        }
        assert publish_packages_finder.exclude_config == [
            {"type": "regex", "pattern": r".*(tar.gz.asc|py3-none-any.whl.sha512)$"}
        ]

    def test_exclude_config_empty(self):
        publish_packages_finder = PublishPackagesFinder()
        publish_packages_finder.artifacts_config = {}
        assert publish_packages_finder.exclude_config is None

    def test_exclude_config_empty_list(self):
        publish_packages_finder = PublishPackagesFinder()
        publish_packages_finder.artifacts_config = {"exclude": []}
        assert publish_packages_finder.exclude_config == []

    def test_run_should_fail_if_no_packages_found(self):
        publish_packages_finder = PublishPackagesFinder()
        with pytest.raises(SystemExit):
            publish_packages_finder.run()

    @pytest.mark.parametrize(
        "temp_packages, exclude_config, expected",
        [
            pytest.param(
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.sha512",
                ],
                [{"type": "regex", "pattern": ".*(.asc|.sha512)$"}],
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                ],
                id="exclude_asc_sha512",
            ),
            pytest.param(
                [
                    "apache-airflow-2.10.4-source.tar.gz",
                    "apache-airflow-2.10.4-source.tar.gz.asc",
                    "apache-airflow-2.10.4-source.tar.gz.sha512",
                    "apache_airflow-2.10.4-py3-none-any.whl",
                    "apache_airflow-2.10.4-py3-none-any.whl.asc",
                    "apache_airflow-2.10.4-py3-none-any.whl.sha512",
                    "apache_airflow-2.10.4.tar.gz",
                    "apache_airflow-2.10.4.tar.gz.asc",
                    "apache_airflow-2.10.4.tar.gz.sha512",
                ],
                [
                    {"type": "regex", "pattern": ".*(.asc|.sha512)$"},
                    {"type": "regex", "pattern": "(apache-airflow-.*?)$"},
                ],
                [
                    "apache_airflow-2.10.4.tar.gz",
                    "apache_airflow-2.10.4-py3-none-any.whl",
                ],
            ),
        ],
    )
    def test_run_should_find_packages(self, monkeypatch, temp_packages, exclude_config, expected):
        monkeypatch.setenv(
            "ARTIFACTS_CONFIG",
            json.dumps(
                {"id": "artifact", "description": "Find publish packages to PyPI", "exclude": exclude_config}
            ),
        )
        dist_folder = tempfile.TemporaryDirectory()
        monkeypatch.setenv("DIST_PATH", dist_folder.name)
        publish_packages_finder = PublishPackagesFinder()
        with tempfile.TemporaryDirectory() as temp_dir:
            write_data(temp_packages, temp_dir)
            os.chdir(temp_dir)
            publish_packages_finder.run()
            assert publish_packages_finder.final_packages_to_publish == unordered(expected)
            assert os.listdir(dist_folder.name) == unordered(expected)
