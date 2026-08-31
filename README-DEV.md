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
  [build-public-release.yml](.github/workflows/build-public-release.yml), publishing it
  to https://pypi.org/project/actionlint-py-kjanat/
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

PyPI matches the OIDC token's `job_workflow_ref` claim, which names the workflow
file the publishing job actually runs in — not the workflow that called it.
Reusable workflows [cannot be registered as a trusted publisher][reusable], so
each publish job lives directly in its own workflow. The trusted publishers must
therefore be registered as:

| index    | workflow                    | environment |
| -------- | --------------------------- | ----------- |
| PyPI     | `build-public-release.yml`  | `PyPI`      |
| TestPyPI | `build-test-release.yml`    | `TestPyPI`  |

`tag-and-release.yml` calls `build-public-release.yml` via `workflow_call`, but
that does not change the claim: the publish job still runs in
`build-public-release.yml`, so that is the file to register either way.

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
