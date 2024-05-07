#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, print_function


import io
from glob import glob
from os.path import basename, dirname, join, splitext
from setuptools import setup, find_packages
from pathlib import Path

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text()


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ).read()


setup(
    name="gridfanapi",
    version="0.1.0",
    license="GPL-3.0",
    description="For communicating with the NZXT Grid+ v2 fan controller on Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="saintnoodle",
    author_email="hi@noodle.moe",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    install_requires=["pyserial"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Hardware :: Universal Serial Bus (USB)",
        "Topic :: Utilities",
    ],
    python_requires=">=3.11",
)
