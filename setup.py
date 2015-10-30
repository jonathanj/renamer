#!/usr/bin/env python
import os
import sys
from inspect import cleandoc

from setuptools import setup


def get_version():
    """
    Get the version from version module without importing more than
    necessary.
    """
    version_module_path = os.path.join(
        os.path.dirname(__file__), "renamer", "_version.py")
    # The version module contains a variable called __version__
    with open(version_module_path) as version_module:
        exec(version_module.read())
    return locals()["__version__"]


def scripts():
    if sys.platform == 'win32':
        yield 'bin/rn.cmd'
    yield 'bin/rn'



setup(
    name="renamer",
    version=get_version(),
    maintainer="Jonathan Jacobs",
    url="https://github.com/jonathanj/renamer",
    license="MIT",
    platforms=["any"],
    description=cleandoc("""
    A mass file renamer with plugin support.
    """),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Topic :: Utilities"],
    install_requires=["zope.interface>=3.6.0",
                      "twisted>=13.2.0",
                      "PyMeta>=0.5.0",
                      "mutagen>=1.31"],
    scripts=list(scripts()))
