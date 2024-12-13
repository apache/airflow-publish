import pytest

from svn.svn_check import (
    check_files_with_identifiers,
    check_with_regex,
    unknown_file_extensions,
    unknown_files,
)


@pytest.mark.parametrize(
    "file, pattern, check_type, expected",
    [
        pytest.param(
            "apache-airflow-2.10.3-source.tar.gz",
            ".*(tar.gz)$",
            "extension",
            True,
            id="valid_extension",
        ),
        pytest.param(
            "apache-airflow-2.10.3-source.tar12.gz",
            ".*(tar.gz)$",
            "extension",
            None,
            id="invalid_extension",
        ),
        pytest.param(
            "apache_airflow-2.10.3-source.tar.gz",
            ".*(apache_airflow.*)$",
            "package_name",
            True,
            id="valid_package_name",
        ),
        pytest.param(
            "apache-airflow-2.10.3-source.tar.gz",
            ".*(apache-airflow.*)$",
            "package_name",
            True,
            id="valid_package_name",
        ),
        pytest.param(
            "apacheairflow-2.10.3-source.tar.gz",
            ".*(apache-airflow.*)$",
            "package_name",
            None,
            id="invalid_valid_package_name",
        ),
    ],
)
def test_check_with_regex_extension_type(file, pattern, check_type, expected):
    assert check_with_regex(file, pattern, check_type) == expected


def test_check_files_with_identifiers_for_extension():
    unknown_file_extensions.clear()
    all_files = [
        "apache-airflow-2.10.3-source.tar.gz",
        "apache-airflow-2.10.3-py3-none-any.whl.asc",
        "apache-airflow-2.10.3-py3-none-any.whl.sha512",
        "apache-airflow-2.10.3.tar.gz",
    ]
    identifiers = [
        {
            "type": "regex",
            "pattern": ".*(py3-none-any.whl|tar.gz.sha512|tar.gz.asc|tar.gz|py3-none-any.whl.asc|py3-none-any.whl.sha512)$",
        }
    ]
    check_type = "extension"
    check_files_with_identifiers(identifiers, all_files, check_type)
    assert not unknown_file_extensions


def test_check_files_with_identifiers_for_invalid_extension():
    unknown_file_extensions.clear()
    all_files = [
        "apache-airflow-2.10.3-source.tar.gz",
        "apache-airflow-2.10.3-py3-none-any.whl.asc123",
        "apache-airflow-2.10.3-py3-none-any.whl.sha512",
        "apache-airflow-2.10.3.tar.jpeg",
    ]
    identifiers = [
        {
            "type": "regex",
            "pattern": ".*(py3-none-any.whl|tar.gz.sha512|tar.gz.asc|tar.gz|py3-none-any.whl.asc|py3-none-any.whl.sha512)$",
        }
    ]
    check_type = "extension"
    check_files_with_identifiers(identifiers, all_files, check_type)
    assert unknown_file_extensions == [
        "apache-airflow-2.10.3-py3-none-any.whl.asc123",
        "apache-airflow-2.10.3.tar.jpeg",
    ]


def test_check_files_with_identifiers_for_package_name():
    unknown_files.clear()
    all_files = [
        "apache-airflow-2.10.3-source.tar.gz",
        "apache-airflow-2.10.3-py3-none-any.whl.asc",
        "apache-airflow-2.10.3-py3-none-any.whl.sha512",
        "apache-airflow-2.10.3.tar.gz",
    ]
    identifiers = [{"type": "regex", "pattern": ".*(apache-airflow.*)$"}]
    check_type = "package_name"
    check_files_with_identifiers(identifiers, all_files, check_type)
    assert not unknown_files


def test_check_files_with_identifiers_for_invalid_package_name():
    unknown_files.clear()
    all_files = [
        "apache-airflow-2.10.3-source.tar.gz",
        "apache-airflow-2.10.3-py3-none-any.whl.asc",
        "apache-airflow-2.10.3-py3-none-any.whl.sha512",
        "apacheairflow-2.10.3.tar.gz",
    ]
    identifiers = [{"type": "regex", "pattern": ".*(apache-airflow.*)$"}]
    check_type = "package_name"
    check_files_with_identifiers(identifiers, all_files, check_type)
    assert unknown_files == ["apacheairflow-2.10.3.tar.gz"]


def test_check_files_with_multiple_identifiers_for_package_name():
    unknown_files.clear()
    all_files = [
        "apache-airflow-2.10.3-source.tar.gz",
        "apache-airflow-2.10.3-py3-none-any.whl.asc",
        "apache-airflow-2.10.3-py3-none-any.whl.sha512",
        "apache_airflow-2.10.3.tar.gz",
    ]
    identifiers = [
        {"type": "regex", "pattern": ".*(apache-airflow.*)$"},
        {"type": "regex", "pattern": ".*(apache_airflow.*)$"},
    ]
    check_type = "package_name"
    check_files_with_identifiers(identifiers, all_files, check_type)
    assert not unknown_files


def test_check_files_with_multiple_identifiers_for_invalid_package_name():
    unknown_files.clear()
    all_files = [
        "apache-airflow-2.10.3-source.tar.gz",
        "apache-airflow-2.10.3-py3-none-any.whl.asc",
        "apache-airflow-2.10.3-py3-none-any.whl.sha512",
        "apache_air-2.10.3.tar.gz",
    ]
    identifiers = [
        {"type": "regex", "pattern": ".*(apache-airflow.*)$"},
        {"type": "regex", "pattern": ".*(apache_airflow.*)$"},
    ]
    check_type = "package_name"
    check_files_with_identifiers(identifiers, all_files, check_type)
    assert unknown_files == [
        "apache_air-2.10.3.tar.gz",
    ]
