#-------------------------------------------------------------------------
# The Azure Batch Apps Python Client ver. 0.1.0
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
"""Unit tests for JobManager"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from batchapps.job_manager import JobManager
from batchapps.api import Response
from batchapps.exceptions import RestCallException
from batchapps.files import FileCollection
from batchapps.job import (
    JobSubmission,
    SubmittedJob)

# pylint: disable=W0212
class TestJobManager(unittest.TestCase):
    """Unit tests for JobManager"""

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.job_manager.BatchAppsApi')
    @mock.patch('batchapps.job_manager.SubmittedJob')
    def test_jobmgr_get_job(self, mock_job, mock_api, mock_creds, mock_cfg):
        """Test get_job"""

        mgr = JobManager(mock_creds, cfg=mock_cfg)

        with self.assertRaises(ValueError):
            mgr.get_job()

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.get_job.return_value = resp

        with self.assertRaises(RestCallException):
            mgr.get_job(url="http://test")
        mgr._client.get_job.assert_called_with(url="http://test")

        resp.success = True
        resp.result = {'id':'1', 'name':'2', 'type':'3'}
        job = mgr.get_job(url="http://test")
        mgr._client.get_job.assert_called_with(url="http://test")
        mock_job.assert_called_with(mgr._client, '1', '2', '3')

        resp.result = {'id':'1', 'name':'2', 'type':'3', 'other':'4'}
        job = mgr.get_job(jobid="test_id")
        mgr._client.get_job.assert_called_with(job_id="test_id")
        mock_job.assert_called_with(mgr._client, '1', '2', '3', other='4')

        with self.assertRaises(ValueError):
            mgr.get_job("test")
        with self.assertRaises(ValueError):
            mgr.get_job(job="test")

        sub = mock.create_autospec(SubmittedJob)
        job = mgr.get_job(sub)
        self.assertEqual(job, sub)
        job = mgr.get_job(job=sub)
        self.assertEqual(job, sub)

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.job_manager.BatchAppsApi')
    @mock.patch('batchapps.job_manager.SubmittedJob')
    def test_jobmgr_get_jobs(self, mock_job, mock_api, mock_creds, mock_cfg):
        """Test get_jobs"""

        mgr = JobManager(mock_creds, cfg=mock_cfg)

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.list_jobs.return_value = resp

        with self.assertRaises(RestCallException):
            mgr.get_jobs()
        mgr._client.list_jobs.assert_called_with(0, 10)

        resp.success = True
        resp.result = {'totalCount':10, 'jobs':[]}
        jobs = mgr.get_jobs(10, "5", 5)
        mgr._client.list_jobs.assert_called_with(10, 5, name='5')
        self.assertEqual(jobs, [])
        self.assertEqual(len(mgr), 10)

        resp.result = {'totalCount':10, 'jobs':[{'id':'1', 'name':'2'}]}
        with self.assertRaises(RestCallException):
            mgr.get_jobs(name="test")

        resp.result = {'totalCount':10,
                       'jobs':[{'id':'1',
                                'name':'2',
                                'type':'3',
                                'other':'4'}]}

        jobs = mgr.get_jobs(index="10")
        mock_job.assert_called_with(mgr._client, '1', '2', '3', other='4')
        self.assertEqual(len(jobs), 1)

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.job_manager.BatchAppsApi')
    @mock.patch('batchapps.job_manager.JobSubmission')
    def test_jobmgr_create_job(self, mock_job, mock_api, mock_creds, mock_cfg):
        """Test create_job"""

        mgr = JobManager(mock_creds, cfg=mock_cfg)
        mgr.create_job("my_job", a='a', b='None', c=[], d=42)
        mock_job.assert_called_with(mgr._client,
                                    "my_job",
                                    a='a',
                                    b='None',
                                    c=[],
                                    d=42)

        mgr.create_job(None)
        mock_job.assert_called_with(mgr._client, "None")

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.job_manager.BatchAppsApi')
    def test_jobmgr_submit(self, mock_api, mock_creds, mock_cfg):
        """Test submit"""

        job = mock.create_autospec(JobSubmission)
        job.name = "test"
        job.source = "test"
        job.required_files = mock.create_autospec(FileCollection)

        mgr = JobManager(mock_creds, cfg=mock_cfg)
        mgr.submit(job)
        self.assertTrue(job.submit.called)
        job.required_files.upload.assert_called_with(threads=None)

        mgr.submit(job, upload_threads=10)
        self.assertTrue(job.submit.called)
        job.required_files.upload.assert_called_with(threads=10)

        with self.assertRaises(TypeError):
            mgr.submit("test")

        job.required_files.upload.return_value = ["oops"]
        with self.assertRaises(Exception):
            mgr.submit(job)
