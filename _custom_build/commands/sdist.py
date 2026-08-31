from setuptools.command.sdist import sdist as orig_sdist

from ..version import write_static_version


class sdist(orig_sdist):
    def run(self):
        # the sdist is the only distribution pypi serves, and it is unpacked
        # without any git history, so freeze the version before the file list
        # is collected - VERSION_STATIC.txt ships as package data
        write_static_version()
        orig_sdist.run(self)
