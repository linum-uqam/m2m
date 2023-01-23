# -*- coding: utf-8 -*-

import glob

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = ''
_version_extra = ''

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = ["Development Status :: 1 - Planning",
               "Environment :: Console",
               "Intended Audience :: Science/Research",
               "License :: OSI Approved :: MIT License",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering"]

# Short description:
description = "m2m: allen2avgt tools"
# Long description (for the pypi page)
long_description = """
Module
======
Allen2Tract is a small library containing tools and utilities to
quickly work with AllenSDK, Tractograms, MI-Brain, AVGT template.
"""

NAME = "m2m"
MAINTAINER = "Mahdi"
MAINTAINER_EMAIL = "mah.abha8@gmail.com"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "https://github.com/linum-uqam/stage-2022-mahdi"
DOWNLOAD_URL = ""
LICENSE = "MIT"
AUTHOR = "Mahdi"
AUTHOR_EMAIL = ""
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
SCRIPTS = glob.glob("scripts/*.py")

PREVIOUS_MAINTAINERS = []