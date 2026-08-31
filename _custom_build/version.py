import os
import subprocess
from argparse import ArgumentParser

_this_dir = os.path.dirname(__file__)
# VERSION_ACTIONLINT.txt is version of actionlint library
VERSION_ACTIONLINT_TXT = os.path.join(_this_dir, "VERSION_ACTIONLINT.txt")
# the build system version is derived from git, so a distribution built outside
# a checkout - an unpacked sdist, which is what pypi serves - carries the value
# resolved at build time instead. Written by the sdist command, never committed.
VERSION_STATIC_TXT = os.path.join(_this_dir, "VERSION_STATIC.txt")
# set by the test release workflow to the run number, which is unique and
# monotonic per workflow, so a dev version never has to be stored either
DEV_VERSION_ENV = "ACTIONLINT_PY_DEV_VERSION"


def get_actionlint_version():
    with open(VERSION_ACTIONLINT_TXT) as r:
        return r.read().strip()


def _git(*args):
    return subprocess.run(
        ("git",) + args,
        cwd=_this_dir,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _in_own_checkout():
    """an unpacked sdist can sit inside an unrelated repository, whose tags say
    nothing about this package - only trust git when it found *this* project"""
    try:
        toplevel = _git("rev-parse", "--show-toplevel")
    except (OSError, subprocess.CalledProcessError):
        return False
    return os.path.exists(os.path.join(toplevel, "_custom_build", "VERSION_ACTIONLINT.txt"))


def get_build_version():
    """build system version = the last release tag's own build version, plus the
    number of commits made since it. Monotonic on every commit, identical when
    recomputed on the tag that was just pushed, and stored nowhere."""
    if not _in_own_checkout():
        return None
    try:
        described = _git("describe", "--tags", "--long", "--match", "v[0-9]*")
    except (OSError, subprocess.CalledProcessError):
        # no release tag yet: count from the root commit instead
        try:
            return int(_git("rev-list", "--count", "HEAD"))
        except (OSError, subprocess.CalledProcessError, ValueError):
            return 0
    tag, distance, _commit = described.rsplit("-", 2)
    try:
        return int(tag.rsplit(".", 1)[1]) + int(distance)
    except ValueError:
        return int(_git("rev-list", "--count", "HEAD"))


def has_release_tag():
    """a checkout with no reachable v* tag - a shallow one, typically, since
    actions/checkout fetches no tags by default - has nothing to measure from"""
    if not _in_own_checkout():
        return False
    try:
        _git("describe", "--tags", "--long", "--match", "v[0-9]*")
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def get_pip_version():
    build_version = get_build_version()
    if build_version is None:
        try:
            with open(VERSION_STATIC_TXT) as f:
                return f.read().strip()
        except OSError:
            raise RuntimeError(
                f"not a git checkout and {VERSION_STATIC_TXT} is missing, so there is no version to report"
            )
    v = f"{get_actionlint_version()}.{build_version}"
    dev_version = os.environ.get(DEV_VERSION_ENV)
    if dev_version:
        v += f".dev{int(dev_version)}"
    return v


def write_static_version():
    """freeze the resolved version into the source tree so it survives into an
    sdist, where there is no git history left to derive it from"""
    version = get_pip_version()
    with open(VERSION_STATIC_TXT, "w") as f:
        f.write(f"{version}\n")
    return version


VERSION = get_pip_version()


def main():
    args = ArgumentParser()
    args.add_argument("--release", help="error if the version contains a '.devN' suffix", action="store_true")
    return args.parse_args()


if __name__ == "__main__":
    args = main()
    if args.release and _in_own_checkout() and not has_release_tag():
        # without a tag the build version falls back to counting from the root
        # commit, which would quietly release something below the last version
        print("ERROR: no v* tag is reachable, so the version cannot be derived - check out with fetch-depth: 0")
        exit(1)
    version = get_pip_version()
    if args.release and ".dev" in version:
        print(f"ERROR: the version is {version} and should not contain .devN")
        exit(1)
    print(version)
