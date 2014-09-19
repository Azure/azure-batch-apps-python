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
"""Unit tests for JobManager"""

import sys

if sys.version_info[:2] <= (2, 7, ):
    import unittest2 as unittest

else:
    import unittest

if sys.version_info[:2] >= (3, 3, ):
    from unittest import mock

else:
    import mock

from batch_apps.job_manager import JobManager
from batch_apps.api import Response
from batch_apps.exceptions import RestCallException
from batch_apps.job import (
    JobSubmission,
    SubmittedJob)

# pylint: disable=W0212
class TestJobManager(unittest.TestCase):
    """Unit tests for JobManager"""

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.job_manager.BatchAppsApi')
    @mock.patch('batch_apps.job_manager.SubmittedJob')
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

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.job_manager.BatchAppsApi')
    @mock.patch('batch_apps.job_manager.SubmittedJob')
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

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.job_manager.BatchAppsApi')
    @mock.patch('batch_apps.job_manager.JobSubmission')
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

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.job_manager.BatchAppsApi')
    def test_jobmgr_submit(self, mock_api, mock_creds, mock_cfg):
        """Test submit"""

        job = mock.create_autospec(JobSubmission)
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
