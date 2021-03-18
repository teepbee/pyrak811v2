"""RAK811v2 library

Setup file for the project

Copyright 2021 Tim Brennan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""

from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rak811v2',
    version='0.0.1',
    description='Interface for RAK811 LoRa module',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/teepbee/pyrak811v2',
    author='Tim Brennan',
    author_email='80405873+teepbee@users.noreply.github.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
    packages=find_packages(),
    python_requires='>=3.5',
    install_requires=[
        'pyserial',
        'RPi.GPIO; platform_machine=="armv7l" or platform_machine=="armv6l"'
    ]
)
