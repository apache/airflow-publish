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

    #
    @pytest.mark.parametrize(
        "packages, exclude_config, expected",
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
                [
                    {
                        "type": "regex",
                        "pattern": r".*(.asc|.sha512)$",
                    },
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                ],
                id="return_rc_packages",
            ),
            pytest.param(
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.sha512",
                ],
                [
                    {
                        "type": "regex",
                        "pattern": r".*(.asc|.sha512)$",
                    },
                ],
                [],
                id="no_rc_packages",
            ),
        ],
    )
    def test_filter_rc_packages_to_publish(self, packages, exclude_config, expected):
        publish_packages_finder = PublishPackagesFinder()
        publish_packages_finder.final_packages_to_publish.clear()

        # Write some files to temporary dev svn folder
        temp_dev_svn_folder = tempfile.TemporaryDirectory()
        os.chdir(temp_dev_svn_folder.name)
        write_data(packages, temp_dev_svn_folder.name)
        publish_packages_finder.filter_rc_packages_to_publish(
            exclude_extensions_config=exclude_config
        )

        assert publish_packages_finder.final_packages_to_publish == unordered(expected)

    @pytest.mark.parametrize(
        "packages, package_name_config, expected",
        [
            pytest.param(
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl.sha512",
                ],
                [
                    {
                        "type": "regex",
                        "pattern": "(apache_airflow_providers.*?)(?=rc)",
                    },
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0",
                    "apache_airflow_providers_airbyte-10.1.0",
                ],
                id="return_package_name_without_rc",
            ),
            pytest.param(
                [
                    "apache-superset-incubating-0.34.0rc2-source.tar.gz",
                    "apache-superset-incubating-0.34.0rc2-source.tar.gz.asc",
                    "apache-superset-incubating-0.34.0rc2-source.tar.gz.sha512",
                ],
                [
                    {
                        "type": "regex",
                        "pattern": "(apache-superset-incubating.*?)(?=rc)",
                    },
                ],
                [
                    "apache-superset-incubating-0.34.0",
                ],
                id="return_superset_package_name_without_rc",
            ),
        ],
    )
    def test_extract_package_names(self, packages, package_name_config, expected):
        publish_packages_finder = PublishPackagesFinder()
        extracted_names = publish_packages_finder.extract_package_names(
            package_name_config=package_name_config, lookup_packages=packages
        )
        assert extracted_names == unordered(expected)

    @pytest.mark.parametrize(
        "compare_config, temp_release_dir_files, temp_dev_svn_files, expected",
        [
            pytest.param(
                {
                    "url": "https://dist.apache.org/repos/dist/release/airflow/",
                    "path": "airflow/providers/",
                    "package_names": [
                        {
                            "type": "regex",
                            "pattern": "(apache_airflow_providers.*?)(?=rc)",
                        }
                    ],
                },
                [
                    "apache_airflow_providers_amazon-9.1.0.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.sha512",
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl.sha512",
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.sha512",
                ],
                id="find_matched_packages_between_dev_and_release",
            ),
            pytest.param(
                {
                    "url": "https://dist.apache.org/repos/dist/release/airflow/",
                    "path": "airflow/providers/",
                    "package_names": [
                        {
                            "type": "regex",
                            "pattern": "(apache_airflow_providers.*?)(?=rc)",
                        }
                    ],
                },
                [
                    "apache_airflow_providers_amazon-9.1.0.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.sha512",
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.sha512",
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.sha512",
                ],
                id="find_matched_packages_between_dev_and_release_should_return_one_provider",
            ),
        ],
    )
    def test_find_matched_packages_between_dev_and_release(
        self,
        compare_config,
        temp_release_dir_files,
        temp_dev_svn_files,
        expected,
    ):
        publish_packages_finder = PublishPackagesFinder()

        # Write some files to temporary release folder
        write_data(
            temp_release_dir_files,
            os.path.join(
                publish_packages_finder.svn_dist_release_dir, compare_config.get("path")
            ),
        )

        # Write some files to temporary dev svn folder
        temp_dev_svn_folder = tempfile.TemporaryDirectory()
        os.chdir(temp_dev_svn_folder.name)
        write_data(temp_dev_svn_files, temp_dev_svn_folder.name)

        publish_packages_finder.find_matched_packages_between_dev_and_release(
            compare_config
        )
        assert (
            publish_packages_finder.matched_packages_between_dev_and_release
            == unordered(expected)
        )

    def test_find_matched_packages_between_dev_and_release_when_no_match_should_fail(
        self,
    ):
        publish_packages_finder = PublishPackagesFinder()
        files = [
            "apache_airflow_providers_amazon-9.1.0.tar.gz",
            "apache_airflow_providers_amazon-9.1.0.tar.gz.asc",
            "apache_airflow_providers_amazon-9.1.0.tar.gz.sha512",
        ]
        write_data(files, publish_packages_finder.svn_dist_release_dir)

        temp_dev_svn_folder = tempfile.TemporaryDirectory()
        os.chdir(temp_dev_svn_folder.name)
        write_data(
            [
                "apache_airflow_providers-airbyte-9.1.0.tar.gz.sha512",
            ],
            temp_dev_svn_folder.name,
        )

        with pytest.raises(SystemExit):
            publish_packages_finder.find_matched_packages_between_dev_and_release(
                compare_config={
                    "url": "https://someurl/",
                    "path": "airflow/providers/",
                    "package_names": [
                        {
                            "type": "regex",
                            "pattern": "(apache_airflow_providers.*?)(?=rc)",
                        }
                    ],
                }
            )

    @pytest.mark.parametrize(
        "compare_config, temp_release_dir_files, temp_dev_svn_files, expected",
        [
            pytest.param(
                {
                    "url": "https://dist.apache.org/repos/dist/release/airflow/",
                    "path": "airflow/providers/",
                    "package_names": [
                        {
                            "type": "regex",
                            "pattern": "(apache_airflow_providers.*?)(?=rc)",
                        }
                    ],
                },
                [
                    "apache_airflow_providers_amazon-9.1.0.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl.sha512",
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_amazon-9.1.0rc1-py3-none-any.whl.sha512",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz.asc",
                    "apache_airflow_providers_airbyte-10.1.0rc1.tar.gz.sha512",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl.asc",
                    "apache_airflow_providers_airbyte-10.1.0rc1-py3-none-any.whl.sha512",
                ],
                [
                    "apache_airflow_providers_amazon-9.1.0.tar.gz",
                    "apache_airflow_providers_amazon-9.1.0-py3-none-any.whl",
                    "apache_airflow_providers_airbyte-10.1.0.tar.gz",
                    "apache_airflow_providers_airbyte-10.1.0-py3-none-any.whl",
                ],
                id="find_matched_packages_between_dev_and_release",
            ),
        ],
    )
    def test_filter_pypi_version_packages_to_publish(
        self, compare_config, temp_release_dir_files, temp_dev_svn_files, expected
    ):
        # Test compare the dev and release packages and filter the packages to publish
        publish_packages_finder = PublishPackagesFinder()
        publish_packages_finder.final_packages_to_publish.clear()

        # Write some files to temporary dev svn folder
        temp_dev_svn_folder = tempfile.TemporaryDirectory()
        os.chdir(temp_dev_svn_folder.name)
        write_data(temp_dev_svn_files, temp_dev_svn_folder.name)

        dist_folder = tempfile.TemporaryDirectory()
        os.environ["DIST_PATH"] = dist_folder.name

        # Create temporary release folder files
        write_data(temp_release_dir_files, publish_packages_finder.svn_dist_release_dir)

        publish_packages_finder.filter_pypi_version_packages_to_publish(
            compare_config=compare_config,
            extension_exclude_config=[
                {
                    "type": "regex",
                    "pattern": r".*(.asc|.sha512)$",
                }
            ],
        )
        assert publish_packages_finder.final_packages_to_publish == unordered(expected)
