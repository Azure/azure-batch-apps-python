#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://opensource.org/licenses/MIT
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
    version='0.1.0',
    author='Microsoft Corporation',
    packages=['batch_apps', 'batch_apps.test'],
    scripts=[
        'samples/BatchAppsExample-cancel_job.py',
        'samples/BatchAppsExample-job_output.py',
        'samples/BatchAppsExample-job_status.py',
        'samples/BatchAppsExample-submit_job.py',
        'samples/BatchAppsExample-task_thumbnail.py',
        'samples/BatchAppsExample-update_job.py',
        'samples/BatchAppsExample-upload_files.py'],
    url='http://pypi.python.org/pypi/AzureBatchApps/',
    license='LICENSE.txt',
    description='Batch Apps Python Client.',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    install_requires=[
        "requests==2.3.0",
        "keyring==3.8",
        "requests_oauthlib==0.4.1"
    ],
)
