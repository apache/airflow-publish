import tempfile
from unittest.mock import patch

import gnupg

from signature.signature_check import (
    invalid_signature_files,
    svn_files,
    temp_signature_key_file_path,
    validate_signature_with_gpg,
)


@patch("signature.signature_check.download_keys")
def test_sign_file(mock_download_keys):
    mock_download_keys.return_value = None
    gpg = gnupg.GPG()
    input_data = gpg.gen_key_input(
        name_email="test@gmail.com",
        passphrase="test",
    )
    key = gpg.gen_key(input_data)
    public_key = gpg.export_keys(key.fingerprint)
    with open(temp_signature_key_file_path, "w") as f:
        f.write(public_key)

    sample_file = tempfile.NamedTemporaryFile().name
    with open(sample_file, "w") as f:
        f.write("Hello World")
    sig_file = sample_file + ".asc"
    gpg.sign_file(
        sample_file,
        keyid=key.fingerprint,
        passphrase="test",
        detach=True,
        output=sig_file,
    )
    svn_files.extend([sample_file, sig_file])
    validate_signature_with_gpg({"keys": temp_signature_key_file_path})
    assert not invalid_signature_files


@patch("signature.signature_check.download_keys")
def test_sign_file_should_fail_when_not_signed(mock_download_keys):
    mock_download_keys.return_value = None
    gpg = gnupg.GPG()
    input_data = gpg.gen_key_input(
        name_email="test@gmail.com",
        passphrase="test",
    )
    key = gpg.gen_key(input_data)

    public_key = gpg.export_keys(key.fingerprint)
    with open(temp_signature_key_file_path, "w") as f:
        f.write(public_key)

    sample_file = tempfile.NamedTemporaryFile().name
    with open(sample_file, "w") as f:
        f.write("Hello World")
    sig_file = sample_file + ".asc"
    with open(sig_file, "wb") as f:
        f.write(b"")
    svn_files.extend([sample_file, sig_file])
    validate_signature_with_gpg({"keys": temp_signature_key_file_path})
    assert invalid_signature_files
