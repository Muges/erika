#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Muges
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# pylint: disable=invalid-name

import os
import sys
from setuptools import setup, find_packages

from erika.__version__ import __appname__, __version__

# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine upload dist/*')
    sys.exit()

with open('README.rst') as f:
    long_description = f.read()


setup(
    name=__appname__.lower(),
    version=__version__,
    description='A GTK podcast manager',
    long_description=long_description,
    license='MIT',
    url='https://github.com/Muges/erika',
    author='Muges',
    author_email='git@muges.fr',

    packages=find_packages(),
    package_data={
        'erika.frontend': [
            'data/icons/hicolor/*/*/*.png',
            'data/icons/hicolor/*/*/*.svg',
            'data/*.glade',
            'data/*.html'
        ],
    },

    install_requires=[
        'feedparser',
        'lxml',
        'mutagen',
        'mygpoclient',
        'peewee',
        'pillow',
        'requests',
        'setuptools'
    ],
    tests_require=[
        'pytest'
    ],

    entry_points={
        'console_scripts': [
            'erika = erika.main:run',
        ],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: GTK',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Multimedia :: Sound/Audio :: Players'
    ]
)
