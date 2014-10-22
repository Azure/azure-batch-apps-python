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
"""Unit tests for rest_client"""

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

import requests_oauthlib
import requests
from oauthlib import oauth2

from batch_apps import rest_client
from batch_apps.credentials import Credentials
from batch_apps.files import UserFile
from batch_apps.exceptions import RestCallException


# pylint: disable=W0212
class TestRestClient(unittest.TestCase):
    """Unit tests for rest_client"""

    def test_rest_client_call(self):
        """Test _call"""

        auth = mock.create_autospec(Credentials)
        session = mock.create_autospec(requests_oauthlib.OAuth2Session)
        auth.get_session.return_value = session
        session.request.return_value = mock.create_autospec(requests.Response)
        session.request.return_value.headers = {}
        session.request.return_value.encoding = 'UTF-8'
        session.request.return_value.content = "test"
        session.request.return_value.request = session.request.return_value
        session.request.return_value.url = ""
        for code in [200, 202]:
            session.request.return_value.status_code = code
            resp = rest_client._call(auth, "a", "b", c="c")
            self.assertIsNotNone(resp)
            self.assertTrue(auth.get_session.called)
            session.request.assert_called_with("a", "b", verify=True, c="c")

        for code in [400, 401, 403, 404, 500]:
            session.request.return_value.status_code = code
            with self.assertRaises(RestCallException):
                rest_client._call(auth, "a", "b", c="c")

        for exp in [requests.RequestException,
                    oauth2.rfc6749.errors.OAuth2Error]:

            session.request.side_effect = exp("Boom!")
            with self.assertRaises(RestCallException):
                rest_client._call(auth, "a", "b", c="c")

    @mock.patch.object(rest_client, '_call')
    def test_rest_client_get(self, mock_call):
        """Test get"""

        auth = mock.create_autospec(Credentials)
        rest_client.get(auth, "http://test", {})
        mock_call.assert_called_with(auth,
                                     'GET',
                                     "http://test",
                                     headers={},
                                     params=None)

        rest_client.get(auth, "http://test", {}, params={'a':1})
        mock_call.assert_called_with(auth,
                                     'GET',
                                     "http://test",
                                     headers={},
                                     params={'a':1})

        mock_call.return_value.json.side_effect = ValueError("Value Error!")
        with self.assertRaises(RestCallException):
            rest_client.get(auth, "http://test", {})

        mock_call.side_effect = RestCallException(None, "Boom!", None)
        with self.assertRaises(RestCallException):
            rest_client.get(auth, "http://test", {})

    @mock.patch.object(rest_client, '_call')
    def test_rest_client_head(self, mock_call):
        """Test head"""

        auth = mock.create_autospec(Credentials)
        val = rest_client.head(auth, "http://test", {})
        mock_call.assert_called_with(auth, 'HEAD', "http://test", headers={})

        with self.assertRaises(RestCallException):
            rest_client.head(auth, "http://test/{0}", {})

        val = rest_client.head(auth, "http://test/{name}", {})
        mock_call.assert_called_with(auth, 'HEAD', "http://test/", headers={})

        val = rest_client.head(auth,
                               "http://test/{name}",
                               {},
                               filename="test file.jpg")

        mock_call.assert_called_with(auth,
                                     'HEAD',
                                     "http://test/test%20file.jpg",
                                     headers={})

        mock_call.return_value.headers = {}
        with self.assertRaises(RestCallException):
            rest_client.head(auth, "http://test", {})

        mock_call.return_value.headers = {"content-length":"10"}
        val = rest_client.head(auth, "http://test", {})
        self.assertEqual(val, 10)

        mock_call.side_effect = RestCallException(None, "Boom!", None)
        with self.assertRaises(RestCallException):
            rest_client.head(auth, "http://test", {})

    @mock.patch.object(rest_client, '_call')
    def test_rest_client_post(self, mock_call):
        """Test post"""

        auth = mock.create_autospec(Credentials)

        with self.assertRaises(RestCallException):
            rest_client.post(auth, "http://test", {})


        mock_call.return_value.text = '{"key":"value"}'
        val = rest_client.post(auth, "http://test", {})
        mock_call.assert_called_with(auth, 'POST', "http://test",
                                     headers={},
                                     data=None)
        self.assertEqual(val, {"key":"value"})

        val = rest_client.post(auth, "http://test", {}, message={"msg":"test"})
        mock_call.assert_called_with(auth, 'POST', "http://test",
                                     headers={},
                                     data='{"msg": "test"}')

        del mock_call.return_value.text
        with self.assertRaises(RestCallException):
            rest_client.post(auth, "http://test", {})

        mock_call.side_effect = RestCallException(None, "Boom!", None)
        with self.assertRaises(RestCallException):
            rest_client.post(auth, "http://test", {})

    @mock.patch.object(rest_client, '_call')
    def test_rest_client_put(self, mock_call):
        """Test put"""

        auth = mock.create_autospec(Credentials)
        u_file = mock.create_autospec(UserFile)
        u_file.name = "test.jpg"

        with self.assertRaises(RestCallException):
            rest_client.put(auth,
                            "http://test//{0}",
                            {"Content-Type": "application/json"},
                            u_file,
                            {},
                            {})

        val = rest_client.put(auth,
                              "http://test//{name}",
                              {"Content-Type": "application/json"},
                              u_file,
                              {},
                              {})

        mock_call.assert_called_with(auth, 'PUT', "http://test//test.jpg",
                                     data={},
                                     files={},
                                     headers={})
        self.assertIsNotNone(val)
        mock_call.side_effect = RestCallException(None, "Boom!", None)

        with self.assertRaises(RestCallException):
            rest_client.put(auth,
                            "http://test//{name}",
                            {"Content-Type": "application/json"},
                            u_file,
                            {},
                            {})

    @mock.patch.object(rest_client.os.path, 'exists')
    @mock.patch.object(rest_client, '_call')
    @mock.patch(BUILTIN_OPEN)
    def test_rest_client_download(self, mock_open, mock_call, mock_path):
        """Test download"""

        auth = mock.create_autospec(Credentials)
        mock_path.return_value = True
        val = rest_client.download(auth,
                                   "http://host//something//test?a=b",
                                   {},
                                   "c:\\test",
                                   10,
                                   False)

        self.assertFalse(mock_call.called)
        self.assertTrue(val)

        #with self.assertRaises(TypeError):
        #    val = rest_client.download(auth,
        #                               "http://host//something//test?a=b",
        #                               {},
        #                               "c:\\test",
        #                               None,
        #                               True)
        val = rest_client.download(auth,
                                   "http://host//something//test?a=b",
                                   {},
                                   "c:\\test",
                                   0,
                                   True)

        mock_call.assert_called_with(auth,
                                     'GET',
                                     "http://host//something//test?a=b",
                                     headers={},
                                     stream=True)

        mock_path.return_value = False
        val = rest_client.download(auth,
                                   "http://host//something//test?a=b",
                                   {},
                                   "c:\\test",
                                   500,
                                   False,
                                   ext=".jpg")

        mock_call.assert_called_with(auth,
                                     'GET',
                                     "http://host//something//test?a=b",
                                     headers={},
                                     stream=True)

        mock_open.assert_called_with("c:\\test\\test.jpg", "wb")

        val = rest_client.download(auth,
                                   "http://host//something//test?a=b",
                                   {},
                                   "c:\\test",
                                   500,
                                   False,
                                   ext=".jpg",
                                   f_name="another.png")

        mock_call.assert_called_with(auth,
                                     'GET',
                                     "http://host//something//test?a=b",
                                     headers={},
                                     stream=True)

        mock_open.assert_called_with("c:\\test\\another.png", "wb")

        mock_open.side_effect = IOError('oops!')
        with self.assertRaises(RestCallException):
            rest_client.download(auth,
                                 "http://host//something//test?a=b",
                                 {},
                                 "c:\\test",
                                 0,
                                 True)

        mock_call.side_effect = RestCallException(None, "Boom!", None)
        with self.assertRaises(RestCallException):
            rest_client.download(auth,
                                 "http://host//something//test?a=b",
                                 {},
                                 "c:\\test",
                                 0,
                                 True)
