import os
import tarfile
import tempfile
from unittest.mock import patch

from checksum.checksum_check import (
    get_valid_files,
    invalid_checksums,
    validate_checksum,
)


def test_get_valid_files_sha512():
    files = [
        "apache-airflow-2.10.3-source.tar.gz.sha512",
        "apache_airflow-2.10.3-py3-none-any.whl.asc",
        "apache_airflow-2.10.3-py3-none-any.whl.sha512",
        "apache_airflow-2.10.3.tar.gz",
    ]
    valida_files = get_valid_files("sha512", files)
    assert valida_files == [
        {
            "sha_file": "apache-airflow-2.10.3-source.tar.gz.sha512",
            "check_file": "apache-airflow-2.10.3-source.tar.gz",
        },
        {
            "sha_file": "apache_airflow-2.10.3-py3-none-any.whl.sha512",
            "check_file": "apache_airflow-2.10.3-py3-none-any.whl",
        },
    ]


def test_get_valid_files_with_sha256():
    files = [
        "apache-airflow-2.10.3-source.tar.gz.sha256",
        "apache_airflow-2.10.3-py3-none-any.whl.asc",
        "apache_airflow-2.10.3-py3-none-any.whl.sha256",
        "apache_airflow-2.10.3.tar.gz",
    ]
    valida_files = get_valid_files("sha256", files)
    assert valida_files == [
        {
            "sha_file": "apache-airflow-2.10.3-source.tar.gz.sha256",
            "check_file": "apache-airflow-2.10.3-source.tar.gz",
        },
        {
            "sha_file": "apache_airflow-2.10.3-py3-none-any.whl.sha256",
            "check_file": "apache_airflow-2.10.3-py3-none-any.whl",
        },
    ]


@patch("hashlib.file_digest")
def test_validate_checksum(mock_file_digest):
    mock_file_digest.return_value.hexdigest.return_value = "bbc759357eb1980e7f80ba0b016e9ed02120e26fcd008129b5777baf8086208c45e170e3c98cf35bd96a246d59484bde3220a897e5e6a7f688a69a40bcd451bd"

    invalid_checksums.clear()
    temp_dir = tempfile.TemporaryDirectory()
    temp_file = tempfile.NamedTemporaryFile()
    os.chdir(temp_dir.name)

    with open(temp_file.name, "wb") as temp_data:
        temp_data.write(b"some random data")

    with open(
        temp_dir.name + "/apache-airflow-2.10.3-source.tar.gz.sha512", "wb"
    ) as temp_file:
        temp_file.write(
            b"bbc759357eb1980e7f80ba0b016e9ed02120e26fcd008129b5777baf8086208c45e170e3c98cf35bd96a246d59484bde3220a897e5e6a7f688a69a40bcd451bd apache-airflow-2.10.3-source.tar.gz"
        )
    tar = tarfile.open(temp_dir.name + "/apache-airflow-2.10.3-source.tar.gz", "w:gz")
    tar.add(temp_file.name)
    tar.close()

    check_sum_files = [
        {
            "sha_file": "apache-airflow-2.10.3-source.tar.gz.sha512",
            "check_file": "apache-airflow-2.10.3-source.tar.gz",
        }
    ]
    validate_checksum(check_sum_files, "sha512")
    assert not invalid_checksums


@patch("hashlib.file_digest")
def test_validate_checksum_invalid(mock_file_digest):
    mock_file_digest.return_value.hexdigest.return_value = "bbc759357eb1980e7f80ba0b016e9ed02120e26fcd008129b5777baf8086208c45e170e3c98cf35bd96a246d59484bde3220a897e5e6a7f688a69a40bcd451bd12"
    invalid_checksums.clear()
    temp_dir = tempfile.TemporaryDirectory()
    temp_file = tempfile.NamedTemporaryFile()
    os.chdir(temp_dir.name)

    with open(temp_file.name, "wb") as temp_data:
        temp_data.write(b"some random data")

    with open(
        temp_dir.name + "/apache-airflow-2.10.3-source.tar.gz.sha512", "wb"
    ) as temp_file:
        temp_file.write(
            b"bbc759357eb1980e7f80ba0b016e9ed02120e26fcd008129b5777baf8086208c45e170e3c98cf35bd96a246d59484bde3220a897e5e6a7f688a69a40bcd451bd apache-airflow-2.10.3-source.tar.gz"
        )
    tar = tarfile.open(temp_dir.name + "/apache-airflow-2.10.3-source.tar.gz", "w:gz")
    tar.add(temp_file.name)
    tar.close()

    check_sum_files = [
        {
            "sha_file": "apache-airflow-2.10.3-source.tar.gz.sha512",
            "check_file": "apache-airflow-2.10.3-source.tar.gz",
        }
    ]
    validate_checksum(check_sum_files, "sha512")
    assert invalid_checksums == [
        {
            "file": "apache-airflow-2.10.3-source.tar.gz.sha512",
            "expected_sha": "bbc759357eb1980e7f80ba0b016e9ed02120e26fcd008129b5777baf8086208c45e170e3c98cf35bd96a246d59484bde3220a897e5e6a7f688a69a40bcd451bd",
            "actual_sha": "bbc759357eb1980e7f80ba0b016e9ed02120e26fcd008129b5777baf8086208c45e170e3c98cf35bd96a246d59484bde3220a897e5e6a7f688a69a40bcd451bd12",
        }
    ]
