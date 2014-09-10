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
"""Unit tests for FileManager"""

import sys

if sys.version_info[:2] <= (2, 7, ):
    import unittest2 as unittest

else:
    import unittest

if sys.version_info[:2] >= (3, 3, ):
    from unittest import mock

else:
    import mock

import os
import batch_apps.file_manager
from batch_apps import FileManager
from batch_apps.api import Response
from batch_apps.exceptions import RestCallException

# pylint: disable=W0212
class TestFileManager(unittest.TestCase):
    """Unit tests for FileManager"""

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.test_dir = os.path.join(self.cwd, "test_assets")
        return super(TestFileManager, self).setUp()

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.api.BatchAppsApi')
    @mock.patch('batch_apps.file_manager.UserFile')
    def test_filemgr_create_file(self,
                                 mock_file,
                                 mock_api,
                                 mock_creds,
                                 mock_cfg):
        """Test create_file"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)
        ufile = mgr.create_file("c:\\test.txt")
        mock_file.assert_called_with(mock.ANY, "c:\\test.txt")
        self.assertIsNotNone(ufile)

        ufile = mgr.create_file(None)
        mock_file.assert_called_with(mock.ANY, 'None')
        self.assertIsNotNone(ufile)

        ufile = mgr.create_file(42)
        mock_file.assert_called_with(mock.ANY, "42")
        self.assertIsNotNone(ufile)

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.api.BatchAppsApi')
    @mock.patch('batch_apps.file_manager.FileCollection')
    def test_filemgr_create_file_set(self,
                                     mock_file,
                                     mock_api,
                                     mock_creds,
                                     mock_cfg):
        """Test create_file_set"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)
        coll = mgr.create_file_set()
        self.assertIsNotNone(coll)
        mock_file.assert_called_with(mock.ANY, *[])

        coll = mgr.create_file_set(None)
        mock_file.assert_called_with(mock.ANY, *[None])

        coll = mgr.create_file_set(1, 2, 3)
        mock_file.assert_called_with(mock.ANY, *[1, 2, 3])

        coll = mgr.create_file_set("a", "a", "a")
        mock_file.assert_called_with(mock.ANY, *['a'])

    @mock.patch.object(batch_apps.file_manager.os.path, 'isfile')
    @mock.patch.object(batch_apps.file_manager.os.path, 'isdir')
    @mock.patch('batch_apps.file_manager.glob')
    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.api.BatchAppsApi')
    @mock.patch.object(batch_apps.file_manager.FileManager, "create_file_set")
    def test_filemgr_files_from_dir_a(self,
                                      mock_file,
                                      mock_api,
                                      mock_creds,
                                      mock_cfg,
                                      mock_glob,
                                      mock_isdir,
                                      mock_isfile):
        """Test files_from_dir"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)
        mock_isdir.return_value = False
        mock_isfile.return_value = True

        with self.assertRaises(OSError):
            mgr.files_from_dir(None)
        with self.assertRaises(OSError):
            mgr.files_from_dir("")
        with self.assertRaises(OSError):
            mgr.files_from_dir(42)

        mock_isdir.return_value = True
        mgr.files_from_dir(os.path.join(self.test_dir, "test_config"))
        mock_glob.glob.assert_called_with(os.path.join(self.test_dir,
                                                       "test_config",
                                                       '*'))

        mgr.files_from_dir(os.path.join(self.test_dir, "test_config"),
                           recursive=True)

        mock_glob.glob.assert_any_call(os.path.join(self.test_dir,
                                                    "test_config",
                                                    '*'))

        mock_glob.glob.assert_any_call(os.path.join(self.test_dir,
                                                    "test_config",
                                                    "batch_apps.ini",
                                                    '*'))


        mock_glob.reset()
        mock_glob.glob.call_count = 0
        mgr.files_from_dir(self.test_dir, recursive=False)
        mock_glob.glob.assert_any_call(self.test_dir + "\\*")
        self.assertEqual(mock_glob.glob.call_count, 1)

        mock_glob.reset()
        mock_glob.glob.call_count = 0
        mgr.files_from_dir(self.test_dir,
                           recursive=True,
                           pattern="*.png")

        self.assertEqual(mock_glob.glob.call_count, 6)
        mock_glob.glob.assert_any_call(self.test_dir + "\\*.png")
        mock_glob.glob.assert_any_call(self.test_dir + "\\test_config\\*.png")

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.file_manager.BatchAppsApi')
    def test_filemgr_files_from_dir_b(self, mock_api, mock_creds, mock_cfg):
        """Test files_from_dir"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)
        collection = mgr.files_from_dir(self.test_dir)

        collection._collection.sort()
        self.assertEqual(str(collection),
                         "['same.png', 'speech_bubble.png', 'star.png']")

        collection = mgr.files_from_dir(self.cwd, pattern="*.png")
        self.assertEqual(str(collection), "[]")

        collection = mgr.files_from_dir(self.cwd,
                                        recursive=True,
                                        pattern="*.png")
        collection._collection.sort()
        self.assertEqual(str(collection),
                         "['same.png', 'speech_bubble.png', 'star.png']")

        with self.assertRaises(OSError):
            mgr.files_from_dir(os.path.join(self.test_dir, "not a dir"))

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.file_manager.BatchAppsApi')
    @mock.patch('batch_apps.file_manager.UserFile')
    def test_filemgr_list_files(self,
                                mock_file,
                                mock_api,
                                mock_creds,
                                mock_cfg):
        """Test list_files"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.list_files.return_value = resp

        test = mgr.list_files()
        self.assertTrue(mgr._client.list_files.called)
        self.assertEqual(test, resp.result)
        self.assertFalse(mock_file.called)

        resp.success = True
        resp.result = ["test", True, 42, None]
        test = mgr.list_files()
        self.assertIsInstance(test, list)
        mock_file.assert_any_call(mgr._client, "test")
        mock_file.assert_any_call(mgr._client, "True")
        mock_file.assert_any_call(mgr._client, "42")
        mock_file.assert_any_call(mgr._client, "None")
        self.assertEqual(mock_file.call_count, 4)

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.file_manager.BatchAppsApi')
    @mock.patch('batch_apps.file_manager.UserFile')
    def test_filemgr_find_file(self,
                               mock_file,
                               mock_api,
                               mock_creds,
                               mock_cfg):
        """Test find_file"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.query_files.return_value = resp

        res = mgr.find_file("test", "date")
        mgr._client.query_files.assert_called_with({'FileName':'test',
                                                    'Timestamp':'date'})
        self.assertEqual(res, resp.result)

        res = mgr.find_file("test", "date", full_path="path")
        mgr._client.query_files.assert_called_with({'FileName':'test',
                                                    'Timestamp':'date',
                                                    'OriginalPath':'path'})
        resp.success = True
        resp.result = []
        res = mgr.find_file("test", "date")
        self.assertEqual(res, [])
        self.assertFalse(mock_file.called)

        resp.result = ["testFile", None]
        res = mgr.find_file("test", "date")
        self.assertEqual(len(res), 2)
        mock_file.assert_any_call(mgr._client, "testFile")
        mock_file.assert_any_call(mgr._client, "None")

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.file_manager.BatchAppsApi')
    @mock.patch('batch_apps.file_manager.UserFile')
    def test_filemgr_find_files(self,
                                mock_file,
                                mock_api,
                                mock_creds,
                                mock_cfg):
        """Test find_files"""

        mgr = FileManager(mock_creds, cfg=mock_cfg)

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.query_files.return_value = resp

        res = mgr.find_files("test")
        mgr._client.query_files.assert_called_with("test")
        self.assertEqual(res, resp.result)

        res = mgr.find_files([None])
        mgr._client.query_files.assert_called_with([None])

        resp.success = True
        resp.result = []
        res = mgr.find_files("test")
        self.assertEqual(res, [])
        self.assertFalse(mock_file.called)

        resp.result = ["testFile", None]
        res = mgr.find_files("test")
        self.assertEqual(len(res), 2)
        mock_file.assert_any_call(mgr._client, "testFile")
        mock_file.assert_any_call(mgr._client, "None")
 