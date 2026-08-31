# Workflows

Workflows take care of (todo update):

- checking for updates every day: [check-for-update.yml](.github/workflows/check-for-update.yml)
  and [auto_update_main.py](_custom_build/auto_update_main.py)
- tagging a git commit using only version in file: `_custom_build/VERSION_ACTIONLINT.txt`
  in [tag.yml](.github/workflows/tag-and-release.yml)
    - todo: it is not ideal that pip version and tag is different...
- making a test release using version on branch `release*`
  [build-test-release.yml](.github/workflows/build-test-release.yml), publishing it
  to https://test.pypi.org/project/actionlint-py-kjanat/#history
    - test version is set to `python -m "_custom_build" --version` + `.devN` (development version is updated
      automatically when PR is created)
- making a public release using version _custom_build/VERSION_ACTIONLINT.txt
  [tag-and-release.yml](.github/workflows/tag-and-release.yml), which tags, builds and
  publishes it to https://pypi.org/project/actionlint-py-kjanat/
    - public version is set to `python -m "_custom_build" --version`
- after `release*` branch is merged development version is reset to 0
  [version-dev.yml](.github/workflows/version-dev-reset.yml)
- after `release*` branch is merged build system version is incremented
  [version-build-system.yml](.github/workflows/version-build-system.yml)
- todo: those workflow means I can not write protect main branch...

## Use actionlint from test mirror

Specify precise version of use `--pre`, or both :)

```shell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --pre actionlint-py-kjanat==1.13.0.24.dev.1
```

# Change actionlint version

All details about actionlint source (and checksums) are stored in [setup.cfg](setup.cfg).
The script [auto_update_main.py](_custom_build/auto_update_main.py) scraps the release page of
[kjanat/actionlint](https://github.com/kjanat/actionlint) and sets the checksums to the newest release. It is not great quality script, but it works. Just run:

```shell
python auto_update_main.py
```

# Publishing

Both release workflows upload with [PyPI trusted publishing][trusted-publishing] (OIDC).
No API token is stored in the repository: the `publish-*` jobs request an
`id-token` and `pypa/gh-action-pypi-publish` exchanges it for a short lived
upload token.

Publishing reads *two* different claims, and both have to match the one
registered workflow:

| step                    | claim                             | names                          |
| ----------------------- | --------------------------------- | ------------------------------ |
| minting the upload token | `job_workflow_ref`                | the workflow the job runs in   |
| verifying the attestation | certificate build config uri (`workflow_ref`) | the workflow that was triggered |

Behind a `workflow_call` those two name different files, so no single registered
trusted publisher can satisfy both — the token is minted and the upload is then
rejected with `Invalid attestations supplied during upload`. This is why
reusable workflows [cannot be used as a trusted publisher][reusable], and why
build and publish live directly in the workflow that gets triggered rather than
in a shared one. Register:

| index    | repository                        | workflow                 | environment |
| -------- | --------------------------------- | ------------------------ | ----------- |
| PyPI     | `renefritze/actionlint-py-kjanat` | `tag-and-release.yml`    | `PyPI`      |
| TestPyPI | `renefritze/actionlint-py-kjanat` | `build-test-release.yml` | `TestPyPI`  |

The `repository` claim is matched as a literal string, so **renaming this
repository invalidates both registrations**. The token exchange then fails with
`invalid-publisher: valid token, but no corresponding publisher`, and the error
helpfully prints the claims it did receive — the `repository` line there is the
name the registration has to be edited to. Fix it on the trusted publisher
itself; nothing in this repository can.

Do not reintroduce a `workflow_call` hop in front of either publish job without
moving the registration to whichever workflow is triggered.

Only the source distribution is uploaded. `python -m build` also produces a
wheel, but `_custom_build/commands/bdist_wheel.py` marks it as platform specific
(`root_is_pure = False`), and pypi rejects the resulting `linux_x86_64` tag.

[trusted-publishing]: https://docs.pypi.org/trusted-publishers/

[reusable]: https://docs.pypi.org/trusted-publishers/troubleshooting/#reusable-workflows-on-github

# Manual release

https://test.pypi.org/manage/project/actionlint-py-kjanat/releases/

https://pypi.org/manage/project/actionlint-py-kjanat/releases/

Install dependencies:

```shell
pip install --upgrade build twine
```

Build and check:

```shell
# python .\setup.py sdist bdist_wheel # deprecated
# python -c "from setuptools import setup; setup()" build # deprecated
python -m build
python -m twine check .\dist\*
```

If using token, create file `.pypirc`:

```
[pypi]
username = __token__
password = <PyPI token>
```

Provide file or insert creds when prompted:

```shell
python -m twine upload .\dist\* # --config-file .pypirc
```
