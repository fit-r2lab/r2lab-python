#!/usr/bin/env python3

import sys
import setuptools

# don't try to import the r2lab package at this early point
# as this would require asyncssh which might not be installed yet
from r2lab.version import version as __version__

long_description = "See README at https://github.com/fit-r2lab/r2lab-python/blob/master/README.md"

required_modules = []

setuptools.setup(
    name             = "r2lab",
    version          = __version__,
    author           = "Thierry Parmentelat",
    author_email     = "thierry.parmentelat@inria.fr",
    description      = "Basic utilities regarding the R2lab testbed",
    long_description = long_description,
    license          = "CC BY-SA 4.0",
    url              = "http://r2lab.readthedocs.io",
    packages         = ['r2lab'],
    install_requires = required_modules,
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3.5",
    ],
)

