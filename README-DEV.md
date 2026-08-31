# Workflows

Workflows take care of (todo update):

- checking for updates every day: [check-for-update.yml](.github/workflows/check-for-update.yml)
  and [auto_update_main.py](_custom_build/auto_update_main.py)
- tagging a git commit and releasing it
  [tag-and-release.yml](.github/workflows/tag-and-release.yml), which tags, builds and
  publishes to https://pypi.org/project/actionlint-py-kjanat/
- making a test release on every PR
  [build-test-release.yml](.github/workflows/build-test-release.yml), publishing it
  to https://test.pypi.org/project/actionlint-py-kjanat/#history

# Versioning

The pip version is `<actionlint version>.<build system version>`, optionally with a
`.devN` suffix on test builds. Only the first part is stored:

| part                | where it comes from                                            |
| ------------------- | -------------------------------------------------------------- |
| actionlint version  | `_custom_build/VERSION_ACTIONLINT.txt`, bumped by the update job |
| build system version | the last `v*` tag's own build system version, plus the number of commits since that tag |
| `.devN`             | `ACTIONLINT_PY_DEV_VERSION`, set to the run number by the test release workflow |

So the build system version rises by one on every commit and is not written down
anywhere. `python ./_custom_build/version.py` prints what the current checkout
would release; `--release` additionally fails if the result carries a `.devN`
suffix. Recomputing on the tag that was just pushed gives the same answer,
because the distance to it is then zero.

This is why the release workflow no longer pushes anything to `main`: there is no
counter file to increment, so it only creates a tag, which branch protection does
not stand in the way of. It is also why every checkout in those workflows uses
`fetch-depth: 0` - without the tags there is nothing to measure the distance from.

An sdist has no git history to read, and an sdist is the only thing pypi serves
for this project. The `sdist` command therefore freezes the resolved version into
`_custom_build/VERSION_STATIC.txt` before the file list is collected, and
`version.py` falls back to that file when it is not looking at this repository.
The file is generated, gitignored, and only consulted outside a checkout, so a
stale one can never win over git.

One thing this gives up: the version references in `README.md` (the hook `rev:`,
the pinned `additional_dependencies` example) used to be rewritten by the release
job, which could only work because it pushed a commit. Update them by hand, or
with the daily actionlint update PR.

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
