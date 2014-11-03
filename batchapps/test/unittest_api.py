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
"""Unit tests for BatchAppsApi"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

try:
    from builtins import open
    BUILTIN_OPEN = "builtins.open"
except ImportError:
    BUILTIN_OPEN = "__builtin__.open"

from batchapps import api
from batchapps.exceptions import RestCallException
from batchapps.files import UserFile
from batchapps.api import (
    BatchAppsApi,
    Response)


API_VERSION = "2014-10-01-preview"

# pylint: disable=W0212
class TestBatchAppsApi(unittest.TestCase):
    """Unit tests for BatchAppsApi"""

    def setUp(self):
        self.headers = {"Accept": "application/json",
                        "x-ms-version": API_VERSION,
                        "Content-Type": "application/json"}
        return super(TestBatchAppsApi, self).setUp()

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    def test_api_app(self, mock_creds, mock_config):
        """Test app"""

        _api = BatchAppsApi(mock_creds, mock_config)
        _api.app()
        self.assertTrue(mock_config.application.called)

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    def test_api_url(self, mock_creds, mock_config):
        """Test url"""

        mock_config.endpoint.return_value = "test_endpoint.com"
        _api = BatchAppsApi(mock_creds, mock_config)
        val = _api.url("jobs")
        self.assertTrue(mock_config.endpoint.called)
        self.assertEqual(val, "https://test_endpoint.com/api/jobs")

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    def test_api_default_params(self, mock_creds, mock_config):
        """Test default_params"""

        _api = BatchAppsApi(mock_creds, mock_config)
        _api.default_params()
        self.assertTrue(mock_config.default_params.called)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_list_jobs(self, mock_url, mock_creds, mock_config, mock_get):
        """Test list_jobs"""

        _api = BatchAppsApi(mock_creds, mock_config)

        mock_url.return_value = "https://test_endpoint.com/api/jobs"
        mock_get.return_value = None
        val = _api.list_jobs()
        self.assertIsInstance(val, Response)
        self.assertFalse(val.success)

        mock_get.return_value = {'totalCount':1, 'jobs':2}
        val = _api.list_jobs()
        self.assertIsInstance(val, Response)
        self.assertTrue(val.success)
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/api/jobs",
                                    self.headers,
                                    params={"maxResults": 10, "startIndex": 0})

        val = _api.list_jobs(index=8, per_call=15, name=20)
        self.assertIsInstance(val, Response)
        self.assertTrue(val.success)
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/api/jobs",
                                    self.headers,
                                    params={"maxResults": 15,
                                            "startIndex": 8,
                                            "nameContains":"20"})
        mock_get.side_effect = RestCallException(None, "Boom!", None)
        val = _api.list_jobs()
        self.assertIsInstance(val, Response)
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_get_job(self, mock_url, mock_creds, mock_config, mock_get):
        """Test get_job"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test_endpoint.com/api/jobs"
        mock_get.return_value = None
        val = _api.get_job()
        self.assertIsInstance(val, Response)
        self.assertFalse(val.success)

        val = _api.get_job(url="https://job_url")
        mock_get.assert_called_with(mock_creds,
                                    "https://job_url",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'id':'1', 'name':'2', 'type':'3'}
        val = _api.get_job(url="https://job_url")
        mock_get.assert_called_with(mock_creds,
                                    "https://job_url",
                                    self.headers)
        self.assertTrue(val.success)

        mock_url.return_value = "https://test_endpoint.com/api/{jobid}"
        val = _api.get_job(job_id="abcdef")
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/api/abcdef",
                                    self.headers)
        self.assertTrue(val.success)
        self.assertTrue(mock_url.called)

        mock_get.side_effect = RestCallException(None, "Boom~", None)
        val = _api.get_job(job_id="abcdef")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'post')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_send_job(self, mock_url, mock_creds, mock_config, mock_post):
        """Test send_job"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test_endpoint.com/api/jobs"
        mock_post.return_value = {}

        val = _api.send_job({})
        mock_post.assert_called_with(mock_creds,
                                     "https://test_endpoint.com/api/jobs",
                                     self.headers,
                                     message={})
        self.assertFalse(val.success)
        mock_post.return_value = {'jobId':'1', 'link':'2'}
        val = _api.send_job({})
        mock_post.assert_called_with(mock_creds,
                                     "https://test_endpoint.com/api/jobs",
                                     self.headers,
                                     message={})
        self.assertTrue(val.success)
        mock_post.side_effect = RestCallException(None, "Boom~", None)
        val = _api.send_job({})
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_get_log(self, mock_url, mock_creds, mock_config, mock_get):
        """Test get_log"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test_endpoint.com/api/{jobid}/log"
        mock_get.return_value = {}

        val = _api.get_log("abcdef")
        self.assertTrue(val.success)
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/api/abcdef/log",
                                    self.headers,
                                    params={'maxResults':100})
        val = _api.get_log("abcdef", start=1, max_lines=None)
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/api/abcdef/log",
                                    self.headers,
                                    params={'since':'1'})
        mock_get.side_effect = RestCallException(None, "Boom~", None)
        val = _api.get_log("test")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'post')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_cancel(self, mock_url, mock_creds, mock_config, mock_post):
        """Test cancel"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test_endpoint.com/api/{jobid}"
        mock_post.return_value = {}

        val = _api.cancel("test_id")
        mock_post.assert_called_with(mock_creds,
                                     "https://test_endpoint.com/api/test_id",
                                     self.headers)
        self.assertTrue(val.success)

        mock_post.side_effect = RestCallException(None, "Boom~", None)
        val = _api.cancel("test_id")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'post')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_reprocess(self, mock_url, mock_creds, mock_config, mock_post):
        """Test reprocess"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test_endpoint.com/api/{jobid}"
        mock_post.return_value = {}

        val = _api.reprocess("test_id")
        mock_post.assert_called_with(mock_creds,
                                     "https://test_endpoint.com/api/test_id",
                                     self.headers)
        self.assertTrue(val.success)

        mock_post.side_effect = RestCallException(None, "Boom~", None)
        val = _api.cancel("test_id")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_list_outputs(self,
                              mock_url,
                              mock_creds,
                              mock_config,
                              mock_get):
        """Test list_outputs"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test_endpoint.com/{jobid}"
        mock_get.return_value = {}

        val = _api.list_outputs("test_id")
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/test_id",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'jobOutputs':None}
        val = _api.list_outputs("test_id")
        mock_get.assert_called_with(mock_creds,
                                    "https://test_endpoint.com/test_id",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'jobOutputs':[]}
        val = _api.list_outputs("test_id")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_get.return_value = {'jobOutputs':[{'name':'output.zip',
                                                'link':{'href':'http://url'},
                                                'kind':'output'}]}
        val = _api.list_outputs("test_id")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [{'name':'output.zip',
                                       'link':'http://url',
                                       'type':'output'}])
        mock_get.return_value = {'jobOutputs':[{'name':'output.zip'}]}
        val = _api.list_outputs("test_id")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [{'name':'output.zip',
                                       'link':None,
                                       'type':None}])

        mock_get.side_effect = RestCallException(None, "Boom~", None)
        val = _api.list_outputs("test_id")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'download')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_get_output(self,
                            mock_url,
                            mock_creds,
                            mock_config,
                            mock_download):
        """Test get_output"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}/{type}"
        mock_download.return_value = {}

        val = _api.get_output("c:\\dir", 500, "output.zip", False)
        self.assertFalse(mock_download.called)
        self.assertFalse(val.success)

        val = _api.get_output("c:\\dir",
                              500,
                              "output.zip",
                              False,
                              url="http://url")

        mock_download.assert_called_with(mock_creds,
                                         "http://url",
                                         self.headers, "c:\\dir",
                                         500,
                                         False,
                                         f_name="output.zip")
        self.assertTrue(val.success)

        val = _api.get_output("c:\\dir",
                              500,
                              "output.zip",
                              False,
                              url="http://url",
                              job_id="test_id")

        mock_download.assert_called_with(mock_creds,
                                         "http://url",
                                         self.headers,
                                         "c:\\dir",
                                         500,
                                         False,
                                         f_name="output.zip")
        self.assertTrue(val.success)

        val = _api.get_output("c:\\dir",
                              500,
                              "output.zip",
                              False,
                              job_id="test_id")

        mock_download.assert_called_with(mock_creds,
                                         "https://test.com/test_id/output",
                                         self.headers,
                                         "c:\\dir",
                                         500,
                                         False,
                                         f_name="output.zip")
        self.assertTrue(val.success)

        val = _api.get_output("c:\\dir",
                              500,
                              "output.zip",
                              False,
                              job_id="test_id",
                              otype="test")

        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'head')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_props_output(self,
                              mock_url,
                              mock_creds,
                              mock_config,
                              mock_head):
        """Test props_output"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}/{type}"
        mock_head.return_value = {}

        val = _api.props_output()
        self.assertFalse(mock_head.called)
        self.assertFalse(val.success)

        val = _api.props_output(job_id="test")
        mock_head.assert_called_with(mock_creds,
                                     "https://test.com/test/output",
                                     self.headers)
        self.assertTrue(val.success)

        mock_head.side_effect = RestCallException(None, "Boom~", None)
        val = _api.props_output(job_id="test")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_list_output_files(self,
                                   mock_url,
                                   mock_creds,
                                   mock_config,
                                   mock_get):
        """Test list_output_files"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}"
        mock_get.return_value = {}

        val = _api.list_output_files("test_id")
        mock_get.assert_called_with(mock_creds,
                                    "https://test.com/test_id",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'outputs':None}
        val = _api.list_output_files("test_id")
        mock_get.assert_called_with(mock_creds,
                                    "https://test.com/test_id",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'outputs':[]}
        val = _api.list_output_files("test_id")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_get.return_value = {'outputs':[{'name':'output.zip',
                                             'link':{'href':'http://url'},
                                             'kind':'output'}]}
        val = _api.list_output_files("test_id")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [{'name':'output.zip',
                                       'link':'http://url',
                                       'type':'output'}])
        mock_get.return_value = {'outputs':[{'name':'output.zip'}]}
        val = _api.list_output_files("test_id")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [{'name':'output.zip',
                                       'link':None,
                                       'type':None}])

        mock_get.side_effect = RestCallException(None, "Boom~", None)
        val = _api.list_output_files("test_id")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'download')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_get_output_file(self,
                                 mock_url,
                                 mock_creds,
                                 mock_config,
                                 mock_download):
        """Test get_output_file"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}/{name}"
        mock_download.return_value = {}

        val = _api.get_output_file("c:\\dir", 500, False)
        self.assertFalse(mock_download.called)
        self.assertFalse(val.success)

        val = _api.get_output_file("c:\\dir",
                                   500,
                                   False,
                                   url="http://url")

        mock_download.assert_called_with(mock_creds,
                                         "http://url",
                                         self.headers,
                                         "c:\\dir",
                                         500,
                                         False,
                                         f_name=None)
        self.assertTrue(val.success)

        val = _api.get_output_file("c:\\dir",
                                   500,
                                   False,
                                   url="http://url",
                                   job_id="test_id")

        mock_download.assert_called_with(mock_creds,
                                         "http://url",
                                         self.headers,
                                         "c:\\dir",
                                         500,
                                         False,
                                         f_name=None)
        self.assertTrue(val.success)

        mock_url.reset()
        mock_download.called = False
        val = _api.get_output_file("c:\\dir", 500, False, job_id="test_id")
        self.assertFalse(mock_url.called)
        self.assertFalse(mock_download.called)
        self.assertFalse(val.success)

        val = _api.get_output_file("c:\\dir",
                                   500,
                                   False,
                                   job_id="test_id",
                                   fname="test.zip")

        self.assertTrue(val.success)

    @mock.patch.object(api.rest_client, 'head')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_props_output_file(self,
                                   mock_url,
                                   mock_creds,
                                   mock_config,
                                   mock_head):
        """Test props_output_file"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}/{name}"
        mock_head.return_value = 0

        val = _api.props_output_file()
        self.assertFalse(val.success)
        self.assertFalse(mock_head.called)

        val = _api.props_output_file(job_id="test_abc")
        self.assertFalse(val.success)
        self.assertFalse(mock_head.called)

        val = _api.props_output_file(job_id="test_abc", fname="file.zip")
        mock_head.assert_called_with(mock_creds,
                                     "https://test.com/test_abc/file.zip",
                                     self.headers)
        self.assertTrue(mock_url.called)

        val = _api.props_output_file(job_id="test_abc",
                                     fname="file.zip",
                                     url="http://test")
        mock_head.assert_called_with(mock_creds,
                                     "https://test.com/test_abc/file.zip",
                                     self.headers)
        self.assertTrue(val.success)

        val = _api.props_output_file(url="http://test")
        mock_head.assert_called_with(mock_creds,
                                     "http://test",
                                     self.headers)
        self.assertTrue(val.success)

        mock_head.side_effect = RestCallException(None, "Boom!", None)
        val = _api.props_output_file(url="http://test")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_list_tasks(self, mock_url, mock_creds, mock_config, mock_get):
        """Test list_tasks"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}"
        mock_get.return_value = {}

        val = _api.list_tasks()
        self.assertFalse(val.success)
        self.assertFalse(mock_get.called)

        val = _api.list_tasks(url="http://test")
        self.assertFalse(mock_url.called)
        self.assertFalse(val.success)
        mock_get.assert_called_with(mock_creds, "http://test", self.headers)

        mock_get.return_value = {'tasks':None}
        val = _api.list_tasks(job_id="test")
        mock_get.assert_called_with(mock_creds,
                                    "https://test.com/test",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'tasks':[]}
        val = _api.list_tasks(job_id="test")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_get.side_effect = RestCallException(None, "Boom!", None)
        val = _api.list_tasks(job_id="test")
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_list_task_outputs(self,
                                   mock_url,
                                   mock_creds,
                                   mock_config,
                                   mock_get):
        """Test list_task_outputs"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}/{taskid}"
        mock_get.return_value = {}

        val = _api.list_task_outputs("test_id", None)
        mock_get.assert_called_with(mock_creds,
                                    "https://test.com/test_id/None",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'outputs':None}
        val = _api.list_task_outputs(None, 3)
        mock_get.assert_called_with(mock_creds,
                                    "https://test.com/None/3",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'outputs':[]}
        val = _api.list_task_outputs("test_id", "0")
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_get.return_value = {'outputs':[{'name':'output.zip',
                                             'link':{'href':'http://url'},
                                             'kind':'output'}]}
        val = _api.list_task_outputs("test_id", 1)
        self.assertTrue(val.success)
        self.assertEqual(val.result, [{'name':'output.zip',
                                       'link':'http://url',
                                       'type':'output'}])
        mock_get.return_value = {'outputs':[{'name':'output.zip'}]}
        val = _api.list_task_outputs("test_id", 5)
        self.assertTrue(val.success)
        self.assertEqual(val.result, [{'name':'output.zip',
                                       'link':None,
                                       'type':None}])

        mock_get.side_effect = RestCallException(None, "Boom~", None)
        val = _api.list_task_outputs("test_id", -1)
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'post')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_cancel_task(self,
                             mock_url,
                             mock_creds,
                             mock_config,
                             mock_post):
        """Test cancel_task"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com/{jobid}/{taskid}"
        mock_post.return_value = {}

        val = _api.cancel_task("test_id", None)
        mock_post.assert_called_with(mock_creds,
                                     "https://test.com/test_id/None",
                                     self.headers)
        self.assertTrue(val.success)

        mock_post.side_effect = RestCallException(None, "Boom~", None)
        val = _api.cancel_task("test_id", 1)
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'get')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_list_files(self, mock_url, mock_creds, mock_config, mock_get):
        """Test list_files"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com"
        mock_get.return_value = {}

        val = _api.list_files()
        self.assertFalse(val.success)

        mock_get.return_value = {'files':None}
        val = _api.list_files()
        mock_get.assert_called_with(mock_creds,
                                    "https://test.com",
                                    self.headers)
        self.assertFalse(val.success)

        mock_get.return_value = {'files':[]}
        val = _api.list_files()
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_get.side_effect = RestCallException(None, "Boom!", None)
        val = _api.list_files()
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'download')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_get_file(self,
                          mock_url,
                          mock_creds,
                          mock_config,
                          mock_download):
        """Test get_file"""

        _api = BatchAppsApi(mock_creds, mock_config)

        val = _api.get_file("a", "b", "c")
        self.assertFalse(val.success)
        self.assertFalse(mock_download.called)

        test_file = mock.create_autospec(UserFile)
        test_file.url = "http://test"

        val = _api.get_file(test_file, 500, "c:\\dir", True)
        self.assertTrue(val.success)
        mock_download.assert_called_with(mock_creds,
                                         "http://test",
                                         self.headers,
                                         "c:\\dir",
                                         500,
                                         overwrite=True)

        mock_download.side_effect = RestCallException(None, "test", None)
        val = _api.get_file(test_file, 500, "c:\\dir", True)
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'head')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_props_file(self,
                            mock_url,
                            mock_creds,
                            mock_config,
                            mock_head):
        """Test props_file"""

        _api = BatchAppsApi(mock_creds, mock_config)

        val = _api.props_file("file")
        self.assertFalse(mock_head.called)
        self.assertFalse(val.success)

        test_file = mock.create_autospec(UserFile)
        test_file.url = "http://test"
        val = _api.props_file(test_file)
        mock_head.assert_called_with(mock_creds, "http://test", self.headers)
        self.assertTrue(val.success)

        mock_head.side_effect = RestCallException(None, "test", None)
        val = _api.props_file(test_file)
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'put')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    @mock.patch(BUILTIN_OPEN)
    def test_api_send_file(self,
                           mock_open,
                           mock_url,
                           mock_creds,
                           mock_config,
                           mock_put):
        """Test send_file"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "https://test.com"

        val = _api.send_file("file")
        self.assertFalse(mock_open.called)
        self.assertFalse(val.success)

        test_file = mock.create_autospec(UserFile)
        test_file.path = "c:\\file.txt"
        val = _api.send_file(test_file)
        self.assertTrue(mock_open.called)
        spec = {"OriginalFilePath": mock.ANY,
                "ContentLength": 0,
                "ContentType": "application/octet-stream",
                "LastModifiedTime": mock.ANY}
        mock_put.assert_called_with(mock_creds,
                                    "https://test.com",
                                    self.headers,
                                    test_file,
                                    spec,
                                    {'Filename':mock.ANY})
        self.assertTrue(val.success)

        mock_open.side_effect = OSError("test")
        val = _api.send_file(test_file)
        self.assertFalse(val.success)
        mock_open.side_effect = None

        mock_put.side_effect = RestCallException(None, "test", None)
        val = _api.send_file(test_file)
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'post')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_query_files(self,
                             mock_url,
                             mock_creds,
                             mock_config,
                             mock_post):
        """Test query_files"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "http://test.com/{queryby}"
        mock_post.return_value = {}

        val = _api.query_files(0)
        self.assertFalse(val.success)
        self.assertFalse(mock_post.called)

        val = _api.query_files([0])
        self.assertFalse(val.success)
        self.assertFalse(mock_post.called)

        val = _api.query_files([])
        self.assertFalse(val.success)
        self.assertFalse(mock_post.called)

        val = _api.query_files({})
        mock_post.assert_called_with(mock_creds,
                                     "http://test.com/byspecification",
                                     self.headers,
                                     {"Specifications": [{}]})
        self.assertFalse(val.success)

        val = _api.query_files([{}])
        mock_post.assert_called_with(mock_creds,
                                     "http://test.com/byspecification",
                                     self.headers,
                                     {"Specifications": [{}]})
        self.assertFalse(val.success)

        val = _api.query_files("")
        mock_post.assert_called_with(mock_creds,
                                     "http://test.com/byname",
                                     self.headers,
                                     {"Names": [""]})
        self.assertFalse(val.success)

        val = _api.query_files([""])
        mock_post.assert_called_with(mock_creds,
                                     "http://test.com/byname",
                                     self.headers,
                                     {"Names": [""]})
        self.assertFalse(val.success)

        mock_post.return_value = {'files':None}
        val = _api.query_files([""])
        self.assertFalse(val.success)

        mock_post.return_value = {'files':[]}
        val = _api.query_files([""])
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_post.side_effect = RestCallException(None, "test", None)
        val = _api.query_files([""])
        self.assertFalse(val.success)

    @mock.patch.object(api.rest_client, 'post')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch.object(BatchAppsApi, 'url')
    def test_api_query_missing_files(self,
                                     mock_url,
                                     mock_creds,
                                     mock_config,
                                     mock_post):
        """Test query_missing_files"""

        _api = BatchAppsApi(mock_creds, mock_config)
        mock_url.return_value = "http://test.com"
        mock_post.return_value = {}

        val = _api.query_missing_files("files")
        self.assertFalse(val.success)
        self.assertFalse(mock_post.called)

        val = _api.query_missing_files({})
        self.assertFalse(val.success)
        mock_post.assert_called_with(mock_creds,
                                     "http://test.com",
                                     self.headers,
                                     {"Specifications":[{}]})
        mock_post.reset()
        val = _api.query_missing_files([{}])
        self.assertFalse(val.success)
        mock_post.assert_once_called_with(mock_creds,
                                          "http://test.com",
                                          self.headers,
                                          {"Specifications":[{}]})
        mock_post.called = False
        val = _api.query_missing_files([])
        self.assertFalse(val.success)
        self.assertFalse(mock_post.called)

        val = _api.query_missing_files([0])
        self.assertFalse(val.success)
        self.assertFalse(mock_post.called)

        mock_post.return_value = {'files':None}
        val = _api.query_missing_files({})
        self.assertFalse(val.success)

        mock_post.return_value = {'files':[]}
        val = _api.query_missing_files({})
        self.assertTrue(val.success)
        self.assertEqual(val.result, [])

        mock_post.side_effect = RestCallException(None, "test", None)
        val = _api.query_missing_files({})
        self.assertFalse(val.success)
