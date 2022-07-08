import os

from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext


def create_cache_dir(dir):
    if not os.path.isdir(dir):
        os.mkdir(dir)


def configure_cache_dir(src, dest):
    if os.path.isdir(src) \
        and not os.path.isdir(dest):
        os.rename(src, dest)


cache_dir = os.path.join(os.path.expanduser('~'), '.allen2tract')
create_cache_dir(cache_dir)
configure_cache_dir("data", os.path.join(cache_dir, "data"))
configure_cache_dir("cache", os.path.join(cache_dir, "cache"))


with open('a2t_requirements.txt') as f:
    required_dependencies = f.read().splitlines()
    external_dependencies = []
    for dependency in required_dependencies:
        if dependency[0:2] == '-e':
            repo_name = dependency.split('=')[-1]
            repo_url = dependency[3:]
            external_dependencies.append('{} @ {}'.format(repo_name, repo_url))
        else:
            external_dependencies.append(dependency)


class CustomBuildExtCommand(build_ext):
    """ build_ext command to use when numpy headers are needed. """

    def run(self):
        # Now that the requirements are installed, get everything from numpy
        from Cython.Build import cythonize
        from numpy import get_include

        # Add everything requires for build
        self.swig_opts = None
        self.include_dirs = [get_include()]
        self.distribution.ext_modules[:] = cythonize(
            self.distribution.ext_modules)

        # Call original build_ext command
        build_ext.finalize_options(self)
        build_ext.run(self)


# Get version and release info, which is all stored in module/version.py
ver_file = os.path.join('allen2tract', 'version.py')
with open(ver_file) as f:
    exec(f.read())
opts = dict(name=NAME,
            maintainer=MAINTAINER,
            maintainer_email=MAINTAINER_EMAIL,
            description=DESCRIPTION,
            long_description=LONG_DESCRIPTION,
            url=URL,
            download_url=DOWNLOAD_URL,
            license=LICENSE,
            classifiers=CLASSIFIERS,
            author=AUTHOR,
            author_email=AUTHOR_EMAIL,
            platforms=PLATFORMS,
            version=VERSION,
            packages=find_packages(),
            setup_requires=['cython', 'numpy'],
            install_requires=external_dependencies,
            scripts=SCRIPTS,
            include_package_data=True)

setup(**opts)
