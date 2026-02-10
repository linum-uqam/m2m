"""
Setup script for m2m package.

This setup.py is maintained for backward compatibility.
Modern configuration is in pyproject.toml.

For installation, use:
    pip install -e .
or:
    python setup.py develop
"""
import os
import shutil
import sys

from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext


def create_cache_dir(dir_path):
    """Create cache directory if it doesn't exist."""
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def configure_cache_dir(src, dest):
    """Move cache directory to user home if needed."""
    if os.path.isdir(src) and not os.path.isdir(dest):
        shutil.copytree(src, dest)
        shutil.rmtree(src)


# Set up cache directories
cache_dir = os.path.join(os.path.expanduser('~'), '.m2m')
try:
    create_cache_dir(cache_dir)
    configure_cache_dir("data", os.path.join(cache_dir, "data"))
    configure_cache_dir("cache", os.path.join(cache_dir, "cache"))
except (OSError, PermissionError) as e:
    print(f"Warning: Could not set up cache directory: {e}", file=sys.stderr)


def parse_requirements(filename):
    """Parse requirements from requirements.txt file."""
    dependencies = []
    try:
        with open(filename) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle editable installs
                    if line.startswith('-e'):
                        repo_name = line.split('=')[-1]
                        repo_url = line[3:].strip()
                        dependencies.append(f'{repo_name} @ {repo_url}')
                    else:
                        dependencies.append(line)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using minimal dependencies.",
              file=sys.stderr)
    return dependencies


class CustomBuildExtCommand(build_ext):
    """Build extension command that handles numpy headers for Cython."""

    def run(self):
        # Import numpy and cython only when needed (after installation)
        try:
            from Cython.Build import cythonize
            from numpy import get_include

            # Add everything required for build
            self.swig_opts = None
            self.include_dirs = [get_include()]
            if self.distribution.ext_modules:
                self.distribution.ext_modules[:] = cythonize(
                    self.distribution.ext_modules)

            # Call original build_ext command
            build_ext.finalize_options(self)
            build_ext.run(self)
        except ImportError as e:
            print(f"Warning: Could not import build dependencies: {e}",
                  file=sys.stderr)
            print("Skipping Cython extension build. Install numpy and cython first.",
                  file=sys.stderr)


# Get version and release info from m2m/version.py
ver_file = os.path.join('m2m', 'version.py')
version_info = {}
try:
    with open(ver_file) as f:
        exec(f.read(), version_info)
except FileNotFoundError:
    print(f"Warning: {ver_file} not found. Using default version.", file=sys.stderr)
    version_info = {
        'NAME': 'm2m',
        'VERSION': '0.1.0',
        'DESCRIPTION': "LINUM's Meso to Macro Toolkit",
        'AUTHOR': 'LINUM Lab',
        'AUTHOR_EMAIL': 'info@linum.uqam.ca',
        'MAINTAINER': 'LINUM Lab',
        'MAINTAINER_EMAIL': 'info@linum.uqam.ca',
        'URL': 'https://linum.info.uqam.ca',
        'DOWNLOAD_URL': '',
        'LICENSE': 'MIT',
        'CLASSIFIERS': [],
        'PLATFORMS': ['Linux', 'macOS', 'Windows'],
        'SCRIPTS': [],
        'LONG_DESCRIPTION': ''
    }

# Parse requirements
install_requires = parse_requirements('requirements.txt')

# Setup configuration
setup(
    name=version_info.get('NAME', 'm2m'),
    version=version_info.get('VERSION', '0.1.0'),
    description=version_info.get('DESCRIPTION', ''),
    long_description=version_info.get('LONG_DESCRIPTION', ''),
    author=version_info.get('AUTHOR', ''),
    author_email=version_info.get('AUTHOR_EMAIL', ''),
    maintainer=version_info.get('MAINTAINER', ''),
    maintainer_email=version_info.get('MAINTAINER_EMAIL', ''),
    url=version_info.get('URL', ''),
    download_url=version_info.get('DOWNLOAD_URL', ''),
    license=version_info.get('LICENSE', ''),
    classifiers=version_info.get('CLASSIFIERS', []),
    platforms=version_info.get('PLATFORMS', []),
    packages=find_packages(),
    install_requires=install_requires,
    scripts=version_info.get('SCRIPTS', []),
    include_package_data=True,
    python_requires='>=3.9,<3.12',
    cmdclass={
        'build_ext': CustomBuildExtCommand,
    },
)
