#!/usr/bin/env python3

# pylint: disable=c0111

"""
Packaging and installation for the r2lab package
"""

from pathlib import Path

import setuptools

# https://packaging.python.org/guides/single-sourcing-package-version/
# set __version__ by read & exec of the python code
# this is better than an import that would otherwise try to
# import the whole package, and fail if a required module is not yet there
VERSION_FILE = Path(__file__).parent / "r2lab" / "version.py"
ENV = {}
with VERSION_FILE.open() as f:
    exec(f.read(), ENV)                                 # pylint: disable=w0122
__version__ = ENV['__version__']


LONG_DESCRIPTION = "See README at https://github.com/fit-r2lab/r2lab-python/blob/master/README.md"

REQUIRED_MODULES = [
    'websockets',
    'asynciojobs', 
    'apssh',
]

EXTRAS_REQUIRE = {
    'sidecar': ['websockets'],
    'prepare': ['apssh'],
    'mapdataframe': ['pandas'],
}

# pip3 install r2lab[all]
# installs all extras

from functools import reduce
EXTRAS_REQUIRE['all'] = list(set(
    reduce(lambda l1, l2: l1+l2, EXTRAS_REQUIRE.values())))

setuptools.setup(
    name="r2lab",
    version=__version__,
    author="Thierry Parmentelat",
    author_email="thierry.parmentelat@inria.fr",
    description="Basic utilities regarding the R2lab testbed",
    long_description=LONG_DESCRIPTION,
    license="CC BY-SA 4.0",
    url="http://r2lab.readthedocs.io",
    packages=['r2lab'],
    install_requires=REQUIRED_MODULES,
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3.5",
    ],
)
