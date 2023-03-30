#!/usr/bin/env python3
"""
Created on Tue Sep 11 08:05:22 2018

@author: a002028
"""
import os
import setuptools
import pathlib


root = pathlib.Path(__file__).parent.resolve()

requirements = []
with open(pathlib.Path(root, 'requirements.txt')) as fh:
    for line in fh:
        requirements.append(line.strip())

with open(pathlib.Path(root, 'README.md')) as fid:
    README = fid.read()


setuptools.setup(
    name='file_explorer',
    version='0.1.0',
    author="Magnus Wenzer",
    author_email="magnus.wenzer@smhi.se",
    description="Package to handle and bundle files with same file stem",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sharksmhi/file_explorer",
    packages=setuptools.find_packages(exclude=('tests*', 'gui*', 'htmlcov*', 'log*')),
    package_data={'file_explorer': [
        os.path.join('file_data', '*.yaml'),
        os.path.join('file_handler', 'config', '*.yaml'),
    ]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
)
