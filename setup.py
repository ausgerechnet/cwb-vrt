#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# description
with open(os.path.join(here, 'README.md'), mode='rt', encoding='utf-8') as f:
    long_description = f.read()

# version
version = {}
with open(os.path.join(here, 'vrt', 'version.py'), mode='rt', encoding='utf-8') as f:
    exec(f.read(), version)


setup(
    name="cwb-vrt",
    version=version["__version__"],
    description="Tools for processing VRT files and CWB import/export",
    license='GNU General Public License v3 or later (GPLv3+)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Philipp Heinrich",
    author_email="philipp.heinrich@fau.de",
    url="https://github.com/ausgerechnet/cwb-vrt",
    packages=[
        'vrt'
    ],
    scripts=[
        'bin/vrt-cohort',
        'bin/vrt-cqpweb',
        'bin/vrt-deduplicate',
        'bin/vrt-index',
        'bin/vrt-meta',
        'bin/vrt-merge'
    ],
    python_requires='>=3.7.0',
    install_requires=[
        "pandas>=2.0",
        "tqdm>=4.67.1",
    ],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
