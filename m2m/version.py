# -*- coding: utf-8 -*-

import glob

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 1
_version_minor = 0
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
               "License :: OSI Approved :: GPLv3 License",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering"]

# Short description:
description = "m2m: Meso to Macro Toolkit"
# Long description (for the pypi page)
long_description = """
Module
======
m2m are tools to merge Allen Mouse Connectivity experiments with neurophotonic, diffusion MRI and tractography data of the mouse brain
"""

NAME = "m2m"
MAINTAINER = "Joel Lefebvre"
MAINTAINER_EMAIL = "lefebvre.joel@uqam.ca"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "https://github.com/linum-uqam/m2m"
DOWNLOAD_URL = ""
LICENSE = "GPLv3"
AUTHOR = "Mahdi Abou-Hamdan"
AUTHOR_EMAIL = ""
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
SCRIPTS = glob.glob("scripts/*.py")

PREVIOUS_MAINTAINERS = []