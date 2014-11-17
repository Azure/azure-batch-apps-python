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
"""Unit tests for JobSubmission, SubmittedJob and Task"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import tempfile
from operator import itemgetter
from batchapps.utils import Listener
from batchapps.api import (
    BatchAppsApi,
    Response)

from batchapps.job import (
    JobSubmission,
    SubmittedJob,
    Task)

from batchapps.files import (
    UserFile,
    FileCollection)

from batchapps.exceptions import (
    FileDownloadException,
    RestCallException)

# pylint: disable=W0212
class TestJobSubmission(unittest.TestCase):
    """Unit tests for JobSubmission"""

    def test_jobsubmission_create(self):
        """Test JobSubmission object"""

        with self.assertRaises(TypeError):
            JobSubmission(None, "")

        api = mock.create_autospec(BatchAppsApi)
        job = JobSubmission(api, "test_job")

        self.assertEqual(job.name, "test_job")
        self.assertFalse("type" in job.__dict__)
        self.assertTrue("params" in job.__dict__)
        self.assertEqual(job.required_files, None)
        self.assertEqual(job.source, "")
        self.assertEqual(job.instances, 0)

        job = JobSubmission(api, "test_job",
                            instances=10,
                            job_file="test.bat",
                            job_type="Animation")

        self.assertFalse("type" in job.__dict__)
        self.assertEqual(job.required_files, None)
        self.assertEqual(job.source, "test.bat")
        self.assertEqual(job.instances, 10)

    def test_jobsubmission_attr(self):
        """Test __getattr__"""

        api = mock.create_autospec(BatchAppsApi)
        job = JobSubmission(api, "test_job", params={})

        job.test = "my_param"
        job.data = "my_data"
        job.number = 42

        #with self.assertRaises(AttributeError):
        job.none_obj = None

        #with self.assertRaises(AttributeError):
        job.dict_obj = {"a":[]}

        self.assertEqual(job.params["test"], "my_param")
        self.assertEqual(job.params["data"], "my_data")
        self.assertEqual(job.params["number"], "42")
        self.assertEqual(job.test, "my_param")
        self.assertEqual(job.data, "my_data")
        self.assertEqual(job.number, "42")
        self.assertEqual(job.none_obj, "None")
        self.assertEqual(job.dict_obj, "{'a': []}")

        with self.assertRaises(AttributeError):
            print(job.other_obj)

        job.source = "my_file.txt"
        del job.source
        with self.assertRaises(AttributeError):
            self.assertEqual(job.source, "")

        del job.test
        with self.assertRaises(AttributeError):
            print(job.test)

        with self.assertRaises(AttributeError):
            del job.new_data


    def test_jobsubmission_filter_params(self):
        """Test _filter_params"""

        api = mock.create_autospec(BatchAppsApi)
        api.default_params.return_value = {}

        job = JobSubmission(api, "test_job", params={})
        self.assertEqual(list(job._filter_params()), [])

        job.params = {"k1":"v1", "k2":"v2"}
        self.assertEqual(sorted(job._filter_params(), key=itemgetter('Name')),
                         sorted([{"Name":"k2", "Value":"v2"},
                                 {"Name":"k1", "Value":"v1"}],
                                key=itemgetter('Name')))

        api.default_params.return_value = {"k2":"v0", "k3":"v3"}
        self.assertEqual(sorted(job._filter_params(), key=itemgetter('Name')),
                         sorted([{"Name":"k3", "Value":"v3"},
                                 {"Name":"k2", "Value":"v2"},
                                 {"Name":"k1", "Value":"v1"}],
                                key=itemgetter('Name')))

    @mock.patch.object(JobSubmission, '_filter_params')
    def test_jobsubmission_create_job_message(self, mock_filter):
        """Test _create_job_message"""

        api = mock.create_autospec(BatchAppsApi)
        api.jobtype.return_value = "TestApp"
        files = mock.create_autospec(FileCollection)
        files._get_message.return_value = ["file1", "file2"]
        files.__len__.return_value = 2

        mock_filter.return_value = [{"Name":"k1", "Value":"v1"}]
        job = JobSubmission(api, "test_job", params={})

        #with self.assertRaises(ValueError):
        msg = job._create_job_message()
        self.assertEqual(msg, {'Name':'test_job',
                               'Type': 'TestApp',
                               'RequiredFiles':[],
                               'Pool': {'InstanceCount':'0'},
                               'Parameters':[{"Name":"k1", "Value":"v1"}],
                               'JobFile':'',
                               'Settings':'',
                               'Priority':'Medium'})

        job.required_files = files
        msg = job._create_job_message()
        self.assertEqual(msg, {'Name':'test_job',
                               'Type': 'TestApp',
                               'RequiredFiles':["file1", "file2"],
                               'Pool': {'InstanceCount':'0'},
                               'Parameters':[{"Name":"k1", "Value":"v1"}],
                               'JobFile':'',
                               'Settings':'',
                               'Priority':'Medium'})

        job.source = None
        job.instances = []
        job.type = 42
        job.name = {}

        with self.assertRaises(TypeError):
            job._create_job_message()

        job.instances = "100"
        msg = job._create_job_message()
        self.assertEqual(msg, {'Name':'{}',
                               'Type': 'TestApp',
                               'RequiredFiles':["file1", "file2"],
                               'Pool': {'InstanceCount':'100'},
                               'Parameters':[{"Name":"k1", "Value":"v1"}],
                               'JobFile':'None',
                               'Settings':'',
                               'Priority':'Medium'})

    @mock.patch('batchapps.job.FileCollection')
    def test_jobsubmission_add_collection(self, mock_coll):
        """Test add_file_collection"""

        api = mock.create_autospec(BatchAppsApi)
        files = mock.create_autospec(FileCollection)

        job = JobSubmission(api, "test_job")
        job.add_file_collection()
        mock_coll.assert_called_with(api)
        mock_coll.called = False

        job = JobSubmission(api, "test_job")
        with self.assertRaises(TypeError):
            job.add_file_collection("test")

        job = JobSubmission(api, "test_job")
        job.add_file_collection(files)
        self.assertEqual(job.required_files, files)
        self.assertFalse(mock_coll.called)

    @mock.patch('batchapps.job.FileCollection')
    def test_jobsubmission_add_file(self, mock_coll):
        """Test add_file"""

        coll = mock.create_autospec(FileCollection)
        api = mock.create_autospec(BatchAppsApi)
        mock_coll.return_value = coll

        job = JobSubmission(api, "test_job")
        job.add_file("test_file")
        mock_coll.assert_called_with(api)
        coll.add.assert_called_with("test_file")
        mock_coll.called = False

        job = JobSubmission(api, "test_job")
        job.required_files = coll
        job.add_file("test_file")
        self.assertFalse(mock_coll.called)
        coll.add.assert_called_with("test_file")

    def test_jobsubmission_job_file(self):
        """Test set_job_file"""

        jfile = mock.create_autospec(UserFile)
        coll = mock.create_autospec(FileCollection)
        api = mock.create_autospec(BatchAppsApi)
        jfile.name = "test"

        job = JobSubmission(api, "test_job")
        with self.assertRaises(ValueError):
            job.set_job_file(2)

        with self.assertRaises(ValueError):
            job.set_job_file(None)

        with self.assertRaises(ValueError):
            job.set_job_file("Something")

        with self.assertRaises(ValueError):
            job.set_job_file(jfile)

        job.required_files = coll
        job.set_job_file(jfile)
        self.assertEqual(job.source, "test")
        coll.add.assert_called_with(jfile)

        coll.__len__.return_value = 1
        job = JobSubmission(api, "test_job")
        job.required_files = coll
        job.set_job_file(0)

    @mock.patch.object(JobSubmission, '_create_job_message')
    def test_jobsubmission_submit(self, mock_message):
        """Test submit"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom!", None)
        api = mock.create_autospec(BatchAppsApi)
        api.send_job.return_value = resp
        mock_message.return_value = "{message}"
        job = JobSubmission(api, "test_job")

        with self.assertRaises(RestCallException):
            job.submit()
        api.send_job.assert_called_with("{message}")

        resp.success = True
        resp.result = {'jobId':'abc'}
        sub = job.submit()
        self.assertEqual(sub, {'jobId':'abc'})


# pylint: disable=W0212
class TestSubmittedJob(unittest.TestCase):
    """Unit tests for SubmittedJob"""

    def test_submittedjob_create(self):
        """Test __getattr__"""

        api = mock.create_autospec(BatchAppsApi)
        job = SubmittedJob(api, None, None, None)
        self.assertIsNone(job.name)
        self.assertIsNone(job.percentage)
        self.assertEqual(job.status, 'NotStarted')

        job = SubmittedJob(api, "abc", "test", "type",
                           status="InProgress",
                           instanceCount="5",
                           outputFileName="output",
                           settings="some_data")

        self.assertEqual(job.submission['status'], "InProgress")
        self.assertEqual(job.submission['requested_instances'], 5)
        self.assertEqual(job.submission['output_filename'], "output")
        self.assertEqual(job.submission['xml_settings'], "some_data")

        self.assertEqual(job.status, "InProgress")
        self.assertEqual(job.requested_instances, 5)
        self.assertEqual(job.output_filename, "output")
        self.assertEqual(job.xml_settings, "some_data")

        with self.assertRaises(AttributeError):
            print(job.endpoint)

        with self.assertRaises(AttributeError):
            del job.start

        with self.assertRaises(ValueError):
            job.status = 'Complete'

        with self.assertRaises(ValueError):
            del job.status

        self.assertEqual(job.name, "test")

    def test_submittedjob_get_final_output(self):
        """Test _get_final_output"""

        resp_a = mock.create_autospec(Response)
        resp_a.success = False
        resp_a.result = RestCallException(None, "test", None)
        resp_b = mock.create_autospec(Response)
        resp_b.success = False
        resp_b.result = RestCallException(None, "test", None)

        api = mock.create_autospec(BatchAppsApi)
        api.props_output.return_value = resp_a
        api.get_output.return_value = resp_b

        job = SubmittedJob(api, None, None, None)
        output = job._get_final_output("", True)
        api.props_output.assert_called_with(url=None)
        self.assertFalse(api.get_output.called)

        job = SubmittedJob(api,
                           None,
                           None,
                           None,
                           outputLink={'href':'http://output'})
        output = job._get_final_output("", True)
        api.props_output.assert_called_with(url='http://output')
        self.assertFalse(api.get_output.called)

        resp_a.success = True
        resp_a.result = 42
        output = job._get_final_output("", True)
        api.props_output.assert_called_with(url='http://output')
        api.get_output.assert_called_with("",
                                          42,
                                          None,
                                          True,
                                          url='http://output')

        self.assertEqual(output, resp_b)

    def test_submittedjob_get_final_preview(self):
        """Test _get_final_preview"""

        resp = mock.create_autospec(Response)
        api = mock.create_autospec(BatchAppsApi)
        api.get_output.return_value = resp

        job = SubmittedJob(api, None, None, None)
        output = job._get_final_preview("dir", "name", True)
        api.get_output.assert_called_with("dir", 0, "name", True, url=None)
        self.assertEqual(output, resp)

        job = SubmittedJob(api,
                           None,
                           None,
                           None,
                           previewLink={'href':'http://thumb'})
        output = job._get_final_preview("dir", "name", False)
        api.get_output.assert_called_with("dir",
                                          0,
                                          "name",
                                          False,
                                          url='http://thumb')
        self.assertEqual(output, resp)

    def test_submittedjob_get_intermediate_output(self):
        """Test _get_intermediate_output"""

        resp_a = mock.create_autospec(Response)
        resp_a.success = False
        resp_a.result = RestCallException(None, "test", None)
        resp_b = mock.create_autospec(Response)

        api = mock.create_autospec(BatchAppsApi)
        api.props_output_file.return_value = resp_a
        api.get_output_file.return_value = resp_b

        job = SubmittedJob(api, None, None, None)
        output = job._get_intermediate_output({}, "dir", True)
        api.props_output_file.assert_called_with(url=None)
        self.assertFalse(api.get_output_file.called)
        self.assertEqual(output, resp_a)

        job = SubmittedJob(api, None, None, None)
        output = job._get_intermediate_output({'link':'http://output'},
                                              "dir",
                                              True)
        api.props_output_file.assert_called_with(url='http://output')
        self.assertFalse(api.get_output_file.called)
        self.assertEqual(output, resp_a)

        resp_a.success = True
        resp_a.result = 42
        output = job._get_intermediate_output({'link':'http://output'},
                                              "dir",
                                              True)
        api.props_output_file.assert_called_with(url='http://output')
        api.get_output_file.assert_called_with("dir",
                                               42,
                                               True,
                                               url='http://output',
                                               fname=None)

        self.assertEqual(output, resp_b)

    @mock.patch('batchapps.job.Task')
    def test_submittedjob_get_tasks(self, mock_task):
        """Test get_tasks"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.list_tasks.return_value = resp

        job = SubmittedJob(api, "abc", None, None)
        with self.assertRaises(RestCallException):
            job.get_tasks()
        api.list_tasks.assert_called_once_with(job_id="abc")

        resp.success = True
        resp.result = [{"a":1, "b":2, "c":3}]
        job.get_tasks()
        api.list_tasks.assert_called_with(job_id="abc")
        mock_task.assert_called_once_with(api, "abc", **{"a":1, "b":2, "c":3})

    @mock.patch.object(SubmittedJob, '_get_intermediate_output')
    @mock.patch.object(SubmittedJob, '_get_final_output')
    def test_submittedjob_get_output(self, mock_final, mock_int):
        """Test get_output"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)

        mock_final.return_value = resp
        mock_int.return_value = resp

        job = SubmittedJob(api, "abc", None, None)

        with self.assertRaises(FileDownloadException):
            job.get_output("dir")

        job = SubmittedJob(api, "abc", None, None,
                           outputLink={'href':'http://'},
                           outputFileName="filename")
        with self.assertRaises(RestCallException):
            output = job.get_output("dir")
        mock_final.assert_called_with("dir", False)
        self.assertFalse(mock_int.called)

        resp.success = True
        output = job.get_output("dir")
        self.assertEqual(output, "dir\\filename")

        mock_final.called = False
        output = job.get_output("dir", output={'name':'test'}, overwrite=True)
        self.assertFalse(mock_final.called)
        mock_int.assert_called_with({'name':'test'}, "dir", True)
        self.assertEqual(output, "dir\\test")

    def test_submittedjob_list_all_outputs(self):
        """Test list_all_outputs"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.list_output_files.return_value = resp

        job = SubmittedJob(api, "abc", None, None)
        with self.assertRaises(RestCallException):
            job.list_all_outputs()

        resp.success = True
        outputs = job.list_all_outputs()
        api.list_output_files.assert_called_with("abc")
        self.assertEqual(outputs, resp.result)

    @mock.patch.object(SubmittedJob, '_get_final_preview')
    def test_submittedjob_get_thumbnail(self, mock_prev):
        """Test get_thumbnail"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mock_prev.return_value = resp
        api = mock.create_autospec(BatchAppsApi)

        job = SubmittedJob(api, "abc", None, None)

        with self.assertRaises(FileDownloadException):
            job.get_thumbnail()
        self.assertFalse(mock_prev.called)

        job = SubmittedJob(api,
                           "abc",
                           None,
                           None,
                           previewLink={'href':'http://'})

        with self.assertRaises(RestCallException):
            job.get_thumbnail()
        self.assertTrue(mock_prev.called)

        resp.success = True
        thumb = job.get_thumbnail(filename="thumb.png")
        mock_prev.assert_called_with(tempfile.gettempdir(), "thumb.png", True)

        thumb = job.get_thumbnail(download_dir="dir",
                                  filename="thumb.png",
                                  overwrite=False)
        mock_prev.assert_called_with("dir", "thumb.png", False)
        self.assertEqual(thumb, "dir\\thumb.png")

    def test_submittedjob_get_logs(self):
        """Test get_logs"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.get_log.return_value = resp

        job = SubmittedJob(api, "abc", None, None)
        logs = job.get_logs()
        api.get_log.assert_called_with("abc", None, 100)
        self.assertIsNone(logs)

        resp.success = True
        logs = job.get_logs(start=10, max_lines=None)
        api.get_log.assert_called_with("abc", 10, None)
        self.assertEqual(logs, resp.result)

    @mock.patch.object(SubmittedJob, '_format_submission')
    def test_submittedjob_update(self, mock_format):
        """Test update"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.get_job.return_value = resp

        job = SubmittedJob(api, "abc", None, None)
        mock_format.called = False
        with self.assertRaises(RestCallException):
            updated = job.update()
        api.get_job.assert_called_with("abc")
        self.assertFalse(mock_format.called)

        resp.success = True
        resp.result = {'status':'Complete'}
        updated = job.update()
        self.assertTrue(updated)
        mock_format.assert_called_with({'status':'Complete'})

    def test_submittedjob_cancel(self):
        """Test cancel"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.cancel.return_value = resp

        job = SubmittedJob(api, "abc", None, None)
        cancelled = job.cancel()
        api.cancel.assert_called_with("abc")
        self.assertFalse(cancelled)

        resp.result = RestCallException(TypeError, "Boom!", None)
        with self.assertRaises(RestCallException):
            job.cancel()

        resp.success = True
        cancelled = job.cancel()
        self.assertTrue(cancelled)

    def test_submittedjob_reprocess(self):
        """Test reprocess"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.reprocess.return_value = resp

        job = SubmittedJob(api, "abc", None, None)
        working = job.reprocess()
        api.reprocess.assert_called_with("abc")
        self.assertFalse(working)

        resp.result = RestCallException(TypeError, "Boom!", None)
        with self.assertRaises(RestCallException):
            job.reprocess()

        resp.success = True
        working = job.reprocess()
        self.assertTrue(working)


# pylint: disable=W0212
class TestTask(unittest.TestCase):
    """Unit tests for Task"""

    def test_task_create(self):
        """Test Task object"""

        api = mock.create_autospec(BatchAppsApi)
        with self.assertRaises(TypeError):
            task = Task(None, None)

        task = Task(api, None)
        self.assertEqual(task._job, 'None')
        self.assertIsNone(task.status)

        task = Task(api,
                    "job_id",
                    status='Complete',
                    cores='8',
                    instance='sample_0')
        self.assertEqual(task.id, 0)
        self.assertEqual(task._job, 'job_id')
        self.assertEqual(task.status, 'Complete')
        self.assertIsNone(task.deployment)

        task = Task(api, None, outputs=[{}, {}])
        self.assertEqual(task.outputs,
                         [{'name':None, 'link':None, 'type':None},
                          {'name':None, 'link':None, 'type':None}])

    def test_task_get_files(self):
        """Test _get_file"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.props_output_file.return_value = resp
        api.get_output_file.return_value = resp

        task = Task(api, None)
        with self.assertRaises(RestCallException):
            task._get_file({}, "dir", False)
        api.props_output_file.assert_called_with(url=None)
        resp.success = True
        resp.result = 42

        task._get_file({}, "dir", False)
        api.props_output_file.assert_called_with(url=None)
        api.get_output_file.assert_called_with("dir",
                                               42,
                                               False,
                                               fname=None,
                                               url=None)
        api.props_output_file.called = False

        task._get_file({'type':'TaskPreview',
                        'link':'http://',
                        'name':'file.txt'}, "dir", True)
        self.assertFalse(api.props_output_file.called)
        api.get_output_file.assert_called_with("dir",
                                               None,
                                               True,
                                               fname="file.txt",
                                               url="http://")

    @mock.patch.object(Task, '_get_file')
    def test_task_get_thumbnail(self, mock_get):
        """Test get_thumbnail"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        mock_get.return_value = resp

        task = Task(api, None)
        with self.assertRaises(FileDownloadException):
            task.get_thumbnail()

        task = Task(api, None, outputs=[{'kind':'TaskPreview'}])
        with self.assertRaises(RestCallException):
            task.get_thumbnail()
        self.assertTrue(mock_get.called)

        resp.success = True
        thumb = task.get_thumbnail(download_dir="dir",
                                   filename="name",
                                   overwrite=False)
        mock_get.assert_called_with({'name':'name',
                                     'type':'TaskPreview',
                                     'link':None}, "dir", False)
        self.assertEqual(thumb, "dir\\name")

        task = Task(api, None, outputs=[{'kind':'TaskPreview',
                                         'name':'thumb.png'}])
        thumb = task.get_thumbnail(download_dir="dir", overwrite=False)
        mock_get.assert_called_with({'name':'thumb.png',
                                     'type':'TaskPreview',
                                     'link':None}, "dir", False)
        self.assertEqual(thumb, "dir\\thumb.png")

        thumb = task.get_thumbnail(download_dir="dir",
                                   filename="name",
                                   overwrite=False)
        mock_get.assert_called_with({'name':'name',
                                     'type':'TaskPreview',
                                     'link':None}, "dir", False)
        self.assertEqual(thumb, "dir\\name")

    def test_task_list_outputs(self):
        """Test list_task_outputs"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.list_task_outputs.return_value = resp

        task = Task(api, "job", id="5")
        with self.assertRaises(RestCallException):
            task.list_outputs()
        api.list_task_outputs.assert_called_with("job", 5)

        resp.success = True
        outputs = task.list_outputs()
        self.assertEqual(outputs, resp.result)

    @mock.patch.object(Task, '_get_file')
    def test_task_get_output(self, mock_get):
        """Test get_output"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        mock_get.return_value = resp

        task = Task(api, None)
        with self.assertRaises(RestCallException):
            task.get_output(None, None)
        resp.success = True
        output = task.get_output({}, "dir")
        mock_get.assert_called_with({}, "dir", False)
        self.assertEqual(output, "dir\\")

        output = task.get_output({'name':'test.txt'}, "dir", overwrite=True)
        mock_get.assert_called_with({'name':'test.txt'}, "dir", True)
        self.assertEqual(output, "dir\\test.txt")

    def test_task_cancel(self):
        """Test cancel_task"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        api = mock.create_autospec(BatchAppsApi)
        api.cancel_task.return_value = resp

        task = Task(api, "abc")
        cancelled = task.cancel()
        api.cancel_task.assert_called_with("abc", 0)
        self.assertFalse(cancelled)

        resp.result = RestCallException(TypeError, "Boom!", None)
        with self.assertRaises(RestCallException):
            task.cancel()

        resp.success = True
        cancelled = task.cancel()
        self.assertTrue(cancelled)
