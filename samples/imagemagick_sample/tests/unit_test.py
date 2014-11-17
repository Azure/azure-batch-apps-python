#-------------------------------------------------------------------------
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

"""ImageMagick Sample Unit Test Suite"""

import unittest
from unittest import mock
import sys
import os

import ImageMagickSample as client
from batchapps import (
    Credentials,
    Configuration,
    AzureOAuth,
    JobManager,
    FileManager)
from batchapps.job import (
    SubmittedJob,
    Task,
    JobSubmission)
from batchapps.files import FileCollection
from batchapps.exceptions import (
    RestCallException,
    AuthenticationException,
    InvalidConfigException)

class TestSample(unittest.TestCase):
    """Unit tests for ImageProcessingSample"""

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        return super(TestSample, self).setUp()

    def test_check_valid_dir(self):
        """Test _check_valid_dir"""

        with self.assertRaises(RuntimeError):
            client._check_valid_dir(None)

        with self.assertRaises(RuntimeError):
            client._check_valid_dir("test")

        with self.assertRaises(RuntimeError):
            client._check_valid_dir(1)

        self.assertEqual(client._check_valid_dir(self.cwd), self.cwd)


    @mock.patch.object(client, '_download_task_outputs')
    def test_track_completed_tasks(self, mock_download_task_outputs):
        """Test _track_completed_tasks"""

        job = mock.create_autospec(SubmittedJob)
        job.get_tasks.return_value = None

        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(job)

        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(None)

        job.get_tasks.return_value = [1, 2, 3]

        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(job)

        task = mock.create_autospec(Task)
        task.status = "test"
        job.get_tasks.return_value = [task, task, task]

        client._track_completed_tasks(job)
        self.assertFalse(mock_download_task_outputs.called)

        task.status = "Complete"
        task.id = 2
        job.number_tasks = 5

        task.outputs = [{'name':'test'}]
        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(job)

        task.outputs = [{'type':'test'}]
        client._track_completed_tasks(job)

        mock_download_task_outputs.assert_called_with(task, [])
        self.assertEqual(mock_download_task_outputs.call_count, 3)

        mock_download_task_outputs.side_effect = RestCallException(None, "RestCallExceptionTEST", None)
        with self.assertRaises(RuntimeError):
            client._track_completed_tasks(job)

    @mock.patch.object(client, '_check_valid_dir')
    def test_download_task_outputs(self, mock_check_valid_dir):
        """Test _download_task_outputs"""

        mock_check_valid_dir.return_value = "C:\\valid_test_dir"
        task = None
        with self.assertRaises(TypeError):
            client._download_task_outputs(task, None)

        task = mock.create_autospec(Task)
        outputs = [{'type':'boo'}]
        with self.assertRaises(RuntimeError):
            client._download_task_outputs(task, outputs)

        outputs = [{'type': 'TaskOutput', 'name': 'test.png'}]
        task.get_output.return_value = True
        self.assertEqual(client._download_task_outputs(task, outputs), None)


    @mock.patch.object(client, '_retrieve_logs')
    #@mock.patch.object(client, '_download_job_output')
    def test_check_job_stopped(self, mock_retrieve_logs):
        """Test _check_job_stopped"""

        with self.assertRaises(RuntimeError):
            client._check_job_stopped(None)

        job = mock.create_autospec(SubmittedJob)
        job.status = "test"
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(job)
        self.assertFalse(mock_retrieve_logs.called)
        #self.assertFalse(mock_download_job_output.called)

        job.status = "OnHold"
        with self.assertRaises(RuntimeError):
            client._check_job_stopped(job)
        mock_retrieve_logs.assert_called_with(job)

        job.status = "Complete"
        self.assertTrue(client._check_job_stopped(job))
        #mock_download_job_output.assert_called_with(job)

    def test_retrieve_logs(self):
        """Test _retrieve_logs"""

        with self.assertRaises(RuntimeError):
            client._retrieve_logs(None)

        job = mock.create_autospec(SubmittedJob)

        job.get_logs.return_value = 3
        with self.assertRaises(RuntimeError):
            client._retrieve_logs(job)

        job.get_logs.return_value = {'upTo': None,
                                     'messages': [{'timestamp': '1800-09-23bla',
                                                   'text': 'This is a test message',
                                                   'taskId': 2}]}
        self.assertIsNone(client._retrieve_logs(job))

        job.get_logs.return_value = None
        with self.assertRaises(RuntimeError):
            client._retrieve_logs(job)

    @mock.patch.object(client, '_check_valid_dir')
    def test_download_job_output(self, mock_check_valid_dir):
        """Test _download_job_output"""

        mock_check_valid_dir.return_value = "C:\\valid_test_dir"

        with self.assertRaises(RuntimeError):
            client._download_job_output(None)

        job = mock.create_autospec(SubmittedJob)
        job.get_output.return_value = "C:\\test_dir"

        with self.assertRaises(RuntimeError):
            client._download_job_output("C:\\test_dir")

        job.get_output.return_value = os.path.join(self.cwd, __file__)
        self.assertIsNone(client._download_job_output(job))

        job.get_output.return_value = "test"
        with self.assertRaises(RuntimeError):
            client._download_job_output(job)

    @mock.patch.object(client.AzureOAuth, 'get_unattended_session')
    @mock.patch.object(client.AzureOAuth, 'get_session')
    @mock.patch.object(client.AzureOAuth, 'get_authorization_url')
    def test_authentication(self, mock_url, mock_session, mock_unattended):
        """Test authentication"""

        mock_unattended.return_value = "Auth"
        auth = client.authentication("test")
        self.assertEqual(auth, "Auth")

        mock_unattended.side_effect = InvalidConfigException(
            "InvalidConfigExceptionTEST")

        mock_session.return_value = "Done!"
        auth = client.authentication("test")
        self.assertEqual(auth, "Done!")
        mock_session.assert_called_with(config="test")

        config = mock.create_autospec(Configuration)

        mock_session.side_effect = InvalidConfigException(
            "InvalidConfigExceptionTEST")

        with self.assertRaises(RuntimeError):
            client.authentication(config)

        mock_session.side_effect = AuthenticationException(
            "AuthenticationExceptionTEST")

        mock_url.side_effect = InvalidConfigException(
            "InvalidConfigExceptionTEST")

        with self.assertRaises(RuntimeError):
            client.authentication(config)

        self.assertEqual(mock_url.call_count, 1)

    @mock.patch.object(client, '_check_valid_dir')
    @mock.patch.object(client, 'FileManager')
    def test_submit_job(self, mock_mgr, mock_check_dir):
        """Test submit_job"""

        mock_check_dir.return_value = "C:\\valid_dir"
        mock_mgr.return_value = mock.create_autospec(FileManager)

        config = mock.create_autospec(Configuration)
        auth = mock.create_autospec(Credentials)
        job_mgr = mock.create_autospec(JobManager)
        new_job = mock.create_autospec(JobSubmission)
        job_mgr.create_job.return_value = new_job
        new_job.required_files = mock.create_autospec(FileCollection)

        new_job.submit.side_effect = RestCallException(
            None, "RestCallExceptionTEST", None)

        with self.assertRaises(RuntimeError):
            client.submit_job(config, auth, job_mgr)

        self.assertTrue(new_job.submit.called)
        mock_mgr.assert_called_with(auth, cfg=config)
        mock_mgr.return_value.files_from_dir.assert_called_with(
            "C:\\valid_dir")


    @mock.patch.object(client, "_track_completed_tasks")
    @mock.patch.object(client, "_check_job_stopped")
    def test_track_job_progress(self, mock_check_job, mock_track_tasks):
        """Test _track_job_progress"""

        job_mgr = mock.create_autospec(JobManager)
        sub = {"jobId": "test", "url": "url_test"}

        with self.assertRaises(RuntimeError):
            client.track_job_progress(job_mgr, [])

        job_mgr.get_job.side_effect = RestCallException(
            None,"GetJobFailed", None)

        with self.assertRaises(RuntimeError):
            client.track_job_progress(job_mgr, sub)
        job_mgr.get_job.assert_called_with(jobid="test")

        job = mock.create_autospec(SubmittedJob)
        job_mgr.get_job.side_effect = None
        job_mgr.get_job.return_value = None
        with self.assertRaises(RuntimeError):
            client.track_job_progress(job_mgr, sub)

        client.TIMEOUT = "test"
        with self.assertRaises(RuntimeError):
            client.track_job_progress(job_mgr, sub)

        job_mgr.get_job.return_value = job
        job.status = "test"
        client.TIMEOUT = 3600
        with self.assertRaises(RuntimeError):
            client.track_job_progress(job_mgr, sub)

        job.name = "MyJob"
        job.status = "NotStarted"
        job.update.return_value = True
        job.percentage = 10

        mock_check_job.return_value = True
        client.track_job_progress(job_mgr, sub)
        self.assertTrue(mock_check_job.called_with(job))

        job.status = "Complete"
        client.track_job_progress(job_mgr, sub)

        job.status = "NotStarted"
        client.TIMEOUT = 20
        mock_check_job.reset_mock()
        mock_check_job.return_value = False
        with self.assertRaises(RuntimeError):
            client.track_job_progress(job_mgr, sub)

        self.assertTrue(mock_check_job.called_with(job))
        self.assertEqual(mock_check_job.call_count, 2)
        self.assertTrue(mock_track_tasks.called_with(job))
