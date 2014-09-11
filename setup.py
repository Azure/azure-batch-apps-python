#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
"""PyPI Setup"""

from distutils.core import setup

setup(
    name='BatchAppsClient',
    version='0.0.1',
    author='Microsoft Corporation',
    author_email='anna.tisch@microsoft.com',
    packages=['batch_apps', 'batch_apps.test'],
    scripts=[],
    url='http://pypi.python.org/pypi/AzureBatchApps/',
    license='LICENSE.txt',
    description='Batch Apps Python Client.',
    long_description=open('README.txt').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: Apache Software License'],
    install_requires=[
        "requests==2.3.0",
        "keyring==3.8",
        "requests_oauthlib==0.4.1"
    ],
)
