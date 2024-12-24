# Airflow Publish

**`airflow publish`** is a composite action repository used to validate artifacts and publish to PyPI from SVN.

## Composite Actions Used in This Repo

## read-config Action
This action reads the release configuration file and writes output to `GITHUB_OUTPUTS`. The configuration file is a YAML file containing rules to validate and config for the publish process.

### Usage
```yaml
- name: "Config parser"
  id: config-parser
  uses: ./read-config
  with:
    release-config: ${{ inputs.release-config }}
```

**Example configuration file:**

```yaml
project:
  name: airflow
  description: "Publish rc provider packages to PyPI"
publisher:
  name: airflow
  url: https://dist.apache.org/repos/dist/dev/airflow/
  path: providers/pypi-rc/
checks:
  svn:
    - id: extension
      description: "Validate svn package extensions"
      identifiers:
        - type: regex
          pattern: ".*(py3-none-any.whl|py3-none-any.whl.asc|py3-none-any.whl.sha512|tar.gz|tar.gz.asc|tar.gz.sha512)$"

    - id: package_name
      description: "Validate svn package names"
      identifiers:
        - type: regex
          pattern: ".*(apache_airflow_providers.*)$"

  checksum:
    - id: checksum
      description: "Validate check sum with SHA512"
      algorithm: "sha512"

  signature:
    - id: signature
      description: "Validate signatures with GPG of packages"
      method: gpg
      keys: "https://dist.apache.org/repos/dist/release/airflow/KEYS"

  artifact:
    id: artifact
    description: "Find providers artifacts to publish to PyPI"
    exclude:
      - type: regex
        pattern: ".*(.asc|.sha512)$"
```
#### Publisher
This section contains the publisher details like `name`, `url`, and `path` to identify the repository in SVN.

- **`name`**: Configure any name for the publisher. A meaningful name is recommended. For example, if you are releasing providers, you can name it `providers`.
- **`url`**: URL of the SVN repository to checkout.
- **`path`**: Path to the directory where the artifacts are stored in the SVN repository.

**Example**:  
If you want to release providers, and the SVN repository structure is as follows:
- `https://dist.apache.org/repos/dist/dev/airflow/providers`
- `https://dist.apache.org/repos/dist/release/airflow/providers`

To publish the packages from the `dev/providers` folder, set `url` and `path` in the `release-config.yml` as shown below:

```yaml
url: https://dist.apache.org/repos/dist/dev/airflow
repo-path: providers/
```
## INIT Action
This action is used to checkout the SVN repository to a temporary directory in the runner.  
It uses the configuration from the `read-config` action to checkout the repository.

**Inputs to the action**:
- **`temp-dir`**: Temporary directory to checkout the repository.
- **`repo-url`**: URL of the SVN repository to checkout.
- **`repo-path`**: Path to the directory where the artifacts are stored in the SVN repository.

### Usage
```yaml
- name: "Checkout svn ${{ steps.config-parser.outputs.publisher-url }}"
  id: "svn-checkout"
  uses: ./init
  with:
    temp-dir: ${{ inputs.temp-dir }}
    repo-url: ${{ steps.config-parser.outputs.publisher-url }}
    repo-path: ${{ steps.config-parser.outputs.publisher-path }}
```

## SVN Action
Action to validate the file name patterns and extensions of the artifacts in the SVN repository.

This action uses the `svn` section from the `release-config.yml` to validate the artifacts. An example configuration is shown below.

```yaml
checks:
  svn:
    - id: extension
      description: "Validate svn package extensions"
      identifiers:
        - type: regex
          pattern: ".*(py3-none-any.whl|tar.gz.sha512|tar.gz.asc|tar.gz|py3-none-any.whl.asc|py3-none-any.whl.sha512)$"

    - id: package_name
      description: "Validate svn package names"
      identifiers:
        - type: regex
          pattern: ".*(apache_airflow.*)$"

        - type: regex
          pattern: ".*(apache-airflow.*)$"
```
#### Extension  
This rule is used to validate the package extension.  
It checks whether each package has the required extension or not. Examples include:

- `.tar.gz`  
- `.tar.gz.asc`  
- `.tar.gz.sha512`  
- `-py3-none-any.whl`  
- `-py3-none-any.whl.asc`  
- `-py3-none-any.whl.sha512`  

---

#### Package Name  
This rule is used to validate the package name.  
It checks whether each package name matches the required pattern or not.

At present, the **SVN Action** supports **only regex type identifiers** to validate the package names and extensions.

### Usage
```yaml
- name: "Svn check"
  id: "svn-check"
  uses: ./svn
  with:
    svn-config: ${{ steps.config-parser.outputs.checks-svn }}
    temp-dir: ${{ inputs.temp-dir }}
    repo-path: ${{ steps.config-parser.outputs.publisher-path }}
```

## Checksum Action
Action to validate the checksum of the artifacts in the SVN repository.

This action uses the `checksum` section from the `release-config.yml` to validate the artifacts. An example configuration is shown below.

```yaml
checks:
  checksum:
    - id: checksum
      description: "Validate check sum with SHA512"
      algorithm: "sha512"
```
#### Checksum
This rule is used to validate the checksum of the artifacts.

It checks the checksum of the artifacts with the provided checksum type.

Provide the checksum type in the `algorithm` field. eg: you may provide `sha512` or `sha256` as the checksum type. anything that is supported by the `hashlib` module in Python.

### Usage
```yaml
- name: "Checksum check"
  id: "checksum-check"
  uses: ./checksum
  with:
    checksum-config: ${{ steps.config-parser.outputs.checks-checksum }}
    temp-dir: ${{ inputs.temp-dir }}
    repo-path: ${{ steps.config-parser.outputs.publisher-path }}
```

## Signature Action
Action to validate the signature of the artifacts in the SVN repository.

This action uses the `signature` section from the `release-config.yml` to validate the artifacts. An example configuration is shown below.

```yaml
checks:
  signature:
    - id: signature
      description: "Validate signatures with GPG of packages"
      method: gpg
      keys: "https://dist.apache.org/repos/dist/release/airflow/KEYS"
```
#### Signature
This rule is used to validate the signature of the artifacts.

It checks the signature of the artifacts with the provided GPG keys file in the `keys` field.

At present, the **Signature Action** supports **only GPG type identifiers** to validate the signature of the artifacts.

### Usage
```yaml
- name: "Signature check"
  id: "signature-check"
  uses: ./signature
  with:
    signature-config: ${{ steps.config-parser.outputs.checks-signature }}
    temp-dir: ${{ inputs.temp-dir }}
    repo-path: ${{ steps.config-parser.outputs.publisher-path }}
```

### Artifacts Action
Action to publish the artifacts to PyPI.

This action uses the `publish` section from the `release-config.yml` to publish the artifacts. An example configuration is shown below.

```yaml
checks:
    artifact:
    id: artifact
    description: "Find providers artifacts to publish to PyPI"
    exclude:
      - type: regex
        pattern: ".*(.asc|.sha512)$"
```
---

### Usage
```yaml
- name: "Find ${{ steps.config-parser.outputs.publisher-name }} packages"
  id: "upload-artifacts"
  uses: ./artifacts
  with:
    artifact-config: ${{ steps.config-parser.outputs.checks-artifact }}
    temp-dir: ${{ inputs.temp-dir }}
    mode: ${{ inputs.mode }}
    publisher-name: ${{ steps.config-parser.outputs.publisher-name }}
    repo-path: ${{ steps.config-parser.outputs.publisher-path }}
    if-no-files-found: ${{ inputs.if-no-files-found }}
    retention-days: ${{ inputs.retention-days }}
    compression-level: ${{ inputs.compression-level }}
    overwrite: ${{ inputs.overwrite }}
```

### Summary Action
This action is used to display the summary of the published artifacts. This needs to be used after the `Publish step`.

```yaml
- name: Publish summary
  uses: ./summary
  with:
  dist-file-path: "${{ github.workspace }}/dist"
  publisher-name: ${{ needs.release-checks.outputs.publisher-name }}
```
dist-file-path: Path to the directory where the artifacts are stored.

publisher-name: Name of the publisher, for example, `providers`.

## Example Workflow
A sample github workflow file to use the composite actions is shown below:

```yaml
name: Dry run publish airflow provider packages
description: "Publish or verify svn artifacts"

on:
  workflow_dispatch:
    inputs:
      release-config:
        description: "Path to the release config file"
        required: true
        default: "providers-rc-config.yml"
        type: choice
        options:
          - "providers-rc-config.yml"
          - "providers-pypi-config.yml"
      temp-dir:
        description: >
          Temporary directory to checkout the svn repo.
        required: false
        default: "asf-dist"
      mode:
        description: >
          Mode to run the action, set mode to 'RELEASE' to publish the packages to PyPI.
        required: false
        default: "VERIFY"
      if-no-files-found:
        description: >
          upload artifacts action behavior if no files are found using the provided path.
        default: 'warn'
      retention-days:
        description: >
          Duration after which artifact will expire in days. 0 means using default retention.
        default: '5'
      compression-level:
        description: >
          The level of compression for artifact upload.
        default: '6'
      overwrite:
        description: >
          Overwrite the existing artifact with the same name.
        default: 'false'

      artifact-name:
        description: >
          The name of the artifact to be uploaded.
        required: false
        default: "pypi-packages"

jobs:
  release-checks:
    outputs:
      publisher-name: ${{ steps.config-parser.outputs.publisher-name }}
    runs-on: ubuntu-20.04
    steps:
     - name: Checkout Code
       uses: actions/checkout@v4
       with:
         persist-credentials: false

     - name: Setup Python
       uses: actions/setup-python@v5
       with:
         python-version: "3.11"

     - name: "Config parser"
       id: config-parser
       uses: ./read-config
       with:
        release-config: ${{ inputs.release-config }}

     - name: "Checkout svn ${{ steps.config-parser.outputs.publisher-url }}"
       id: "svn-checkout"
       uses: ./init
       with:
         temp-dir: ${{ inputs.temp-dir }}
         repo-url: ${{ steps.config-parser.outputs.publisher-url }}
         repo-path: ${{ steps.config-parser.outputs.publisher-path }}

     - name: "Svn check"
       id: "svn-check"
       uses: ./svn
       with:
        svn-config: ${{ steps.config-parser.outputs.checks-svn }}
        temp-dir: ${{ inputs.temp-dir }}
        repo-path: ${{ steps.config-parser.outputs.publisher-path }}

     - name: "Checksum check"
       id: "checksum-check"
       uses: ./checksum
       with:
        checksum-config: ${{ steps.config-parser.outputs.checks-checksum }}
        temp-dir: ${{ inputs.temp-dir }}
        repo-path: ${{ steps.config-parser.outputs.publisher-path }}

     - name: "Signature check"
       id: "signature-check"
       uses: ./signature
       with:
        signature-config: ${{ steps.config-parser.outputs.checks-signature }}
        temp-dir: ${{ inputs.temp-dir }}
        repo-path: ${{ steps.config-parser.outputs.publisher-path }}

     - name: "Find ${{ steps.config-parser.outputs.publisher-name }} packages"
       id: "upload-artifacts"
       uses: ./artifacts
       with:
        artifact-config: ${{ steps.config-parser.outputs.checks-artifact }}
        temp-dir: ${{ inputs.temp-dir }}
        mode: ${{ inputs.mode }}
        publisher-name: ${{ steps.config-parser.outputs.publisher-name }}
        repo-path: ${{ steps.config-parser.outputs.publisher-path }}
        if-no-files-found: ${{ inputs.if-no-files-found }}
        retention-days: ${{ inputs.retention-days }}
        compression-level: ${{ inputs.compression-level }}
        overwrite: ${{ inputs.overwrite }}
        artifact-name: ${{ inputs.artifact-name }}

  publish-to-pypi:
    name: Publish svn packages to PyPI
    runs-on: ubuntu-20.04
    if: inputs.mode == 'RELEASE' && success()
    needs:
      - release-checks
    permissions:
      id-token: write  # IMPORTANT: mandatory for trusted publishing

    steps:
      - name: "Download release distributions for ${{ needs.release-checks.outputs.publisher-name }}"
        uses: actions/download-artifact@v4
        with:
          name: ${{ inputs.artifact-name }}
          merge-multiple: true
          path: ./dist

      - name: "Publishing ${{ needs.release-checks.outputs.publisher-name }} to PyPI"
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: "./dist"
          
      - name: Publish summary
        uses: ./summary
        with:
          dist-file-path: "${{ github.workspace }}/dist"
          publisher-name: ${{ needs.release-checks.outputs.publisher-name }}
```

The `mode` input is used to run the action in different modes.
- **`VERIFY`**:  
  It will only validate the artifacts and not publish to PyPI.

- **`RELEASE`**:  
    It will validate the artifacts and publish to PyPI.

