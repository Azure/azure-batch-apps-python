#-------------------------------------------------------------------------
# The Azure Batch Apps Python Client
#
# Copyright (c) Microsoft Corporation. All rights reserved. 
#
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#--------------------------------------------------------------------------
"""PyPI Setup"""

from distutils.core import setup

setup(
    name='azure-batch-apps',
    version='0.2.1',
    author='Microsoft Corporation',
    author_email='BigCompute@microsoft.com',
    packages=['batchapps',
              'batchapps.test'],
    scripts=[
        'samples/BatchAppsExample-cancel_job.py',
        'samples/BatchAppsExample-job_output.py',
        'samples/BatchAppsExample-job_status.py',
        'samples/BatchAppsExample-submit_job.py',
        'samples/BatchAppsExample-task_thumbnail.py',
        'samples/BatchAppsExample-update_job.py',
        'samples/BatchAppsExample-upload_files.py'],
    url='https://github.com/Azure/azure-batch-apps-python',
    license='MIT License',
    description='Batch Apps Python Client',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development'],
    install_requires=[
        "requests>=2.3.0",
        "keyring>=3.8",
        "requests_oauthlib>=0.4.1"],
)
