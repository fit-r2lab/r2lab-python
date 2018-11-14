#!/usr/bin/env python3

# pylint: disable=c0111

import setuptools

# don't try to import the r2lab package at this early point
# as this would require asyncssh which might not be installed yet
from r2lab.version import __version__

LONG_DESCRIPTION = "See README at https://github.com/fit-r2lab/r2lab-python/blob/master/README.md"

REQUIRED_MODULES = [
    'socketIO-client',
    'apssh',
]

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
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3.5",
    ],
)
