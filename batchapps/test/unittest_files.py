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
"""Unit tests for FileCollection and UserFile"""

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
    BUILTIN = "builtins"
except ImportError:
    BUILTIN = "__builtin__"

import os
import batchapps
from batchapps.api import Response
from batchapps.files import (
    UserFile,
    FileCollection)

from batchapps.exceptions import (
    FileMissingException,
    FileInvalidException,
    RestCallException)

class UFile(object):
    """Mock UserFile"""

    def __init__(self, arg_a=False):
        """Mock UserFile"""
        self.name = arg_a

    def upload(self, **kwargs):
        """Mock upload"""
        return Response(self.name, None)


# pylint: disable=W0212
class TestFileCollection(unittest.TestCase):
    """Unit tests for FileCollection"""

    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_create(self, mock_api, mock_add):
        """Test FileCollection object"""

        with self.assertRaises(TypeError):
            FileCollection(None)

        FileCollection(mock_api)
        self.assertFalse(mock_add.called)

        FileCollection(mock_api, "test")
        mock_add.assert_called_once_with("test")

        FileCollection(mock_api, "test1", "test2")
        mock_add.assert_any_call("test1")
        mock_add.assert_any_call("test2")

        FileCollection(mock_api, ["test1", "test2"])
        mock_add.assert_any_call("test1")
        mock_add.assert_any_call("test2")

        FileCollection(mock_api, None)
        mock_add.assert_any_call(None)

    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_str(self, mock_api, mock_add):
        """Test __str__"""

        col = FileCollection(mock_api)
        col._collection = [1, None, "test", [], {}]

        colstr = str(col)
        self.assertEqual(colstr, "['1', 'None', 'test', '[]', '{}']")

    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_len(self, mock_api, mock_add):
        """Test __len__"""

        col = FileCollection(mock_api)
        col._collection = [1, None, "test", [], {}]

        self.assertEqual(len(col), len(col._collection))

        col._collection.append("more")
        self.assertEqual(len(col), len(col._collection))

    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_iter(self, mock_api, mock_add):
        """Test __iter__"""

        col = FileCollection(mock_api)

        itr = iter(col)
        with self.assertRaises(StopIteration):
            next(itr)

        col._collection.append(None)
        for ufile in col:
            self.assertIsNone(ufile)

    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_getitem(self, mock_api, mock_add):
        """Test __getitem__"""

        test_file = mock.create_autospec(UserFile)
        test_file.name = "test"

        col = FileCollection(mock_api)
        with self.assertRaises(FileMissingException):
            print(col[1])

        self.assertEqual(col[:1], [])
        col._collection.append(test_file)

        self.assertEqual(col[0], test_file)
        self.assertEqual(col["test"], [test_file])
        self.assertEqual(col[-1], test_file)
        self.assertEqual(col[:1], [test_file])

        with self.assertRaises(FileMissingException):
            print(col[10])
        with self.assertRaises(FileMissingException):
            print(col["test2"])
        with self.assertRaises(FileMissingException):
            print(col[None])

    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_delitem(self, mock_api, mock_add):
        """Test __delitem__"""

        col = FileCollection(mock_api)
        col._collection = [1, None, "test", [], {}]

        del col[0]
        del col[-1]
        del col[1:]
        self.assertEqual(col._collection, [None])

        test_file = mock.create_autospec(UserFile)
        test_file.name = "test"
        col._collection = [test_file]

        del col["test"]
        self.assertEqual(col._collection, [])
        del col["something"]
        self.assertEqual(col._collection, [])

        del col[5]
        del col[None]
        del col[0:-1]


    @mock.patch.object(FileCollection, 'add')
    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_get_message(self, mock_api, mock_add):
        """Test _get_message"""

        col = FileCollection(mock_api)
        test_file = mock.create_autospec(UserFile)
        test_file.create_query_specifier.return_value = {"test_query":1}
        test_file.create_submit_specifier.return_value = {"test_submit":2}
        col._collection = [test_file]

        specs = col._get_message(None)
        self.assertEqual(specs, [])

        specs = col._get_message(1)
        self.assertEqual(specs, [])

        specs = col._get_message([])
        self.assertEqual(specs, [])

        specs = col._get_message("query")
        self.assertEqual(specs, [{"test_query":1}])
        specs = col._get_message("submit")
        self.assertEqual(specs, [{"test_submit":2}])

    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_add(self, mock_api):
        """Test add"""

        col = FileCollection(mock_api)
        test_file = mock.create_autospec(UserFile)

        with self.assertRaises(FileInvalidException):
            col.add("test")
        with self.assertRaises(FileInvalidException):
            col.add(1)
        with self.assertRaises(FileInvalidException):
            col.add(None)

        col.add(test_file)
        self.assertEqual(col._collection, [test_file])
        with self.assertRaises(FileInvalidException):
            col.add(test_file)

        col._collection = []
        col.add([test_file])
        self.assertEqual(col._collection, [test_file])
        col.add([test_file])
        self.assertEqual(col._collection, [test_file])

        col._collection = []
        col.add([test_file, test_file])

        col._collection = []
        col.add([1, "2", None])
        self.assertEqual(col._collection, [])


    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_extend(self, mock_api):
        """Test extend"""

        col = FileCollection(mock_api)
        col2 = FileCollection(mock_api)

        test_file = mock.create_autospec(UserFile)
        test_file2 = mock.create_autospec(UserFile)

        col._collection = [test_file]
        col2._collection = [test_file2, test_file]

        with self.assertRaises(AttributeError):
            col.extend(None)
        with self.assertRaises(AttributeError):
            col.extend("test")
        with self.assertRaises(AttributeError):
            col.extend([])

        col.extend(col2)
        self.assertEqual(len(col._collection), 2)
        self.assertTrue(all(i in [test_file, test_file2]
                            for i in col._collection))

        col2.extend(col)
        self.assertEqual(len(col._collection), 2)
        self.assertTrue(all(i in [test_file, test_file2]
                            for i in col._collection))

    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_index(self, mock_api):
        """Test index"""

        col = FileCollection(mock_api)

        test_file = mock.create_autospec(UserFile)
        test_file2 = mock.create_autospec(UserFile)
        test_file3 = mock.create_autospec(UserFile)

        col._collection = [test_file, test_file2]

        with self.assertRaises(TypeError):
            col.index(None)
        with self.assertRaises(TypeError):
            col.index("test")

        with self.assertRaises(ValueError):
            col.index(test_file3)

        self.assertEqual(col._collection.index(test_file2), 1)


    @mock.patch('batchapps.api.BatchAppsApi')
    def test_filecoll_remove(self, mock_api):
        """Test remove"""

        col = FileCollection(mock_api)
        test_file = mock.create_autospec(UserFile)
        test_file.name = "test"
        col._collection = [test_file, 1, "2", None, []]

        with self.assertRaises(TypeError):
            col.remove(None)
        with self.assertRaises(TypeError):
            col.remove(10)

        col.remove(1)
        col.remove(-1)
        col.remove(slice(1))
        self.assertEqual(col._collection, ["2", None])

        test_file2 = mock.create_autospec(UserFile)
        test_file2.name = "test2"
        test_file3 = mock.create_autospec(UserFile)
        test_file3.name = "test3"
        col._collection = [test_file, test_file2, test_file3]
        col.remove("test")
        self.assertEqual(col._collection, [test_file2, test_file3])
        col.remove(["test2", "test3"])
        self.assertEqual(col._collection, [])

    @mock.patch('batchapps.api.BatchAppsApi')
    @mock.patch('batchapps.files.UserFile')
    @mock.patch.object(FileCollection, '_get_message')
    @mock.patch.object(FileCollection, 'remove')
    def test_filecoll_is_uploaded(self,
                                  mock_rem,
                                  mock_mess,
                                  mock_ufile,
                                  mock_api):
        """Test is_uploaded"""

        def user_file_gen(u_name):
            """Mock UserFile generator"""
            ugen = mock.create_autospec(UserFile)
            ugen.name = str(u_name)
            ugen.compare_lastmodified.return_value = True
            return ugen

        def add(col, itm):
            """Mock add UserFile to collection"""
            col._collection.append(itm)

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom", None)
        mock_ufile.return_value = user_file_gen("1")
        FileCollection.add = add
        mock_api.query_files.return_value = resp
        mock_mess.return_value = ["1", "2", "3", "4", "5"]

        col = FileCollection(mock_api)
        upl = col.is_uploaded()
        self.assertIsInstance(upl, FileCollection)
        self.assertEqual(upl._collection, col._collection)
        self.assertFalse(mock_api.query_files.called)

        col._collection = [1, 2, 3, 4, 5]
        with self.assertRaises(RestCallException):
            col.is_uploaded()
        mock_api.query_files.assert_called_once_with(["1", "2", "3", "4", "5"])

        with self.assertRaises(RestCallException):
            col.is_uploaded(per_call=2)
        mock_api.query_files.assert_called_with(["1", "2"])

        col._collection = [user_file_gen("1"), user_file_gen("2")]
        mock_api.reset()
        resp.success = True
        resp.result = ["test1", "test2", "test3"]
        upl = col.is_uploaded()
        mock_api.query_files.assert_called_with(["1", "2", "3", "4", "5"])
        mock_rem.assert_called_with([mock.ANY])
        self.assertEqual(upl._collection, col._collection)

        col._collection = [user_file_gen("test1"), user_file_gen("test2")]
        upl = col.is_uploaded()
        mock_rem.assert_called_with([])
        self.assertEqual(upl._collection, col._collection)

    @mock.patch('batchapps.api.BatchAppsApi')
    @mock.patch.object(FileCollection, '_upload_forced')
    @mock.patch.object(FileCollection, 'is_uploaded')
    def test_filecoll_upload(self, mock_isup, mock_upload, mock_api):
        """Test upload"""

        _callback = mock.Mock()
        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom", None)
        mock_isup.return_value = []
        mock_upload.return_value = (False, "f", "Error!")

        mock_isup.called = False
        col = FileCollection(mock_api)
        failed = col.upload()
        self.assertTrue(mock_isup.called)
        self.assertFalse(mock_upload.called)
        self.assertEqual(failed, [])

        mock_isup.called = False
        failed = col.upload(force=True)
        self.assertFalse(mock_isup.called)
        self.assertFalse(mock_upload.called)
        self.assertEqual(failed, [])

        col._collection = [1, 2, 3, 4]
        failed = col.upload(force=True)
        mock_upload.assert_any_call(1, callback=None, block=4096)
        self.assertEqual(mock_upload.call_count, 4)

        self.assertEqual(failed, [("f", "Error!"),
                                  ("f", "Error!"),
                                  ("f", "Error!"),
                                  ("f", "Error!")])

        mock_upload.call_count = 0
        resp.success = True
        mock_upload.return_value = (True, "f", "All good!")
        failed = col.upload(force=True, threads=None, callback=_callback, block=1)
        mock_upload.assert_any_call(1, callback=_callback, block=1)
        self.assertEqual(mock_upload.call_count, 4)
        self.assertEqual(failed, [])

    @mock.patch('batchapps.api.BatchAppsApi')
    @mock.patch.object(batchapps.files.pickle, 'dumps')
    def test_filecoll_upload_thread(self, mock_pik, mock_api):
        """Test upload"""

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom", None)

        col = FileCollection(mock_api)
        col._api = None
        failed = col.upload(force=True, threads=1)
        self.assertFalse(mock_pik.called)
        self.assertEqual(failed, [])

        col._collection = [1, 2, 3, 4]
        failed = col.upload(force=True, threads=1)
        self.assertEqual(mock_pik.call_count, 1)
        self.assertEqual(failed, 
                         [(1, "'int' object has no attribute 'upload'"),
                          (2, "'int' object has no attribute 'upload'"),
                          (3, "'int' object has no attribute 'upload'"),
                          (4, "'int' object has no attribute 'upload'")])

        mock_pik.call_count = 0
        col._collection = [UFile()]
        failed = col.upload(force=True, threads=1)
        self.assertEqual(mock_pik.call_count, 1)
        self.assertEqual(len(failed), 1)
        self.assertIsInstance(failed[0], tuple)

        mock_pik.call_count = 0
        col._collection = [UFile(arg_a=True)]
        failed = col.upload(force=True, threads=1)
        self.assertEqual(mock_pik.call_count, 1)
        self.assertEqual(failed, [])

        mock_pik.call_count = 0
        col._collection = [UFile(arg_a=True)]
        failed = col.upload(force=True, threads=3)
        self.assertEqual(mock_pik.call_count, 1)
        self.assertEqual(failed, [])

        mock_pik.call_count = 0
        col._collection = [UFile() for a in range(15)]
        failed = col.upload(force=True, threads=3)
        self.assertEqual(mock_pik.call_count, 5)
        self.assertEqual(len(failed), 15)

        mock_pik.call_count = 0
        col._collection = [UFile(arg_a=True) for a in range(20)]
        failed = col.upload(force=True, threads=20)
        self.assertEqual(mock_pik.call_count, 2)
        self.assertEqual(failed, [])


# pylint: disable=W0212
class TestUserFile(unittest.TestCase):
    """Unit tests for UserFile"""

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.use_test_files = os.path.exists(os.path.join(self.cwd, "test_assets"))
        return super(TestUserFile, self).setUp()

    @mock.patch('batchapps.files.path')
    @mock.patch.object(UserFile, '_verify_path')
    @mock.patch.object(UserFile, 'get_last_modified')
    @mock.patch.object(UserFile, 'get_checksum')
    def test_userfile_create(self, mock_sum, mock_mod, mock_verify, mock_path):
        """Test UserFile object"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        mock_sum.return_value = "check_sum"
        mock_verify.return_value = False
        mock_mod.return_value = "2014-06-04T03:48:40.909998Z"

        with self.assertRaises(TypeError):
            UserFile(None, None)
        with self.assertRaises(TypeError):
            UserFile(api, None)
        with self.assertRaises(TypeError):
            UserFile(api, 42)

        u_file = UserFile(api, {'name':'test1'})
        x_file = UserFile(api, {'name':'test2'})
        self.assertFalse(mock_sum.called)
        self.assertFalse(mock_verify.called)
        self.assertFalse(mock_mod.called)
        self.assertEqual(str(u_file), "test1")
        self.assertEqual(sorted([x_file, u_file]), [u_file, x_file])

        u_file = UserFile(api, "test")
        mock_path.basename.assert_called_with("test")
        mock_path.normpath.assert_called_with("test")
        self.assertTrue(mock_sum.called)
        self.assertTrue(mock_verify.called)
        self.assertTrue(mock_mod.called)

    @mock.patch.object(batchapps.files.path, 'isfile')
    @mock.patch.object(batchapps.files.path, 'getsize')
    def test_userfile_exists(self, mock_size, mock_isfile):
        """Test _verify_path"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        mock_isfile.return_value = False
        u_file = UserFile(api, {})
        u_file.path = "c:\\test"
        self.assertFalse(u_file._verify_path())

        mock_isfile.return_value = True
        self.assertTrue(u_file._verify_path())

        self.assertFalse(u_file)

        u_file._exists = True
        self.assertTrue(u_file)

    @mock.patch.object(batchapps.files.path, 'getmtime')
    def test_userfile_last_modified(self, mock_mod):
        """Test get_last_modified"""

        mock_mod.return_value = 1407124410.692879
        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        u_file = UserFile(api, {})
        u_file.path = "c:\\test"
        mod = u_file.get_last_modified()
        self.assertEqual(mod, "")

        u_file._exists = True
        mod = u_file.get_last_modified()
        mock_mod.assert_called_once_with("c:\\test")
        self.assertTrue(mod.startswith("2014-08-04T03:53:30"))

    def test_userfile_get_windows_path(self):
        """Test _get_windows_path"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        u_file = UserFile(api, {})
        u_file.path = "c:\\test"
        w_path = u_file._get_windows_path()
        self.assertEqual(w_path, u_file.path)

        u_file.path = "/user/test"
        w_path = u_file._get_windows_path()
        self.assertEqual(w_path, "\\user\\test")

    @mock.patch.object(batchapps.files.path, 'getsize')
    def test_userfile_len(self, mock_size):
        """Test __len__"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        mock_size.return_value = 4096
        u_file = UserFile(api, {})
        u_file.path = "c:\\test"
        self.assertEqual(len(u_file), 0)

        u_file._exists = True
        self.assertEqual(len(u_file), 4096)

    def test_userfile_checksum(self):
        """Test get_checksum"""

        if not self.use_test_files:
            self.skipTest("No test files present")

        test_path = os.path.join(self.cwd, "test_assets", "star.png")
        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        u_file = UserFile(api, {'name':'star.png'})
        u_file.path = test_path
        chsum = u_file.get_checksum()
        self.assertEqual(chsum, "")

        u_file._exists = True
        chsum = u_file.get_checksum()
        u_file._checksum = chsum
        self.assertEqual(len(chsum), 16)

        u_file.path = None
        chsum = u_file.get_checksum()
        self.assertEqual(chsum, "")

        u_file.path = "c:\\test"
        chsum = u_file.get_checksum()
        self.assertEqual(chsum, "")

        x_file = UserFile(api, {'name':'star.png'})
        x_file.path = os.path.join(self.cwd, "test_assets", "same.png")

        self.assertFalse(x_file == u_file)
        x_file._exists = True
        x_file._checksum = x_file.get_checksum()

        self.assertTrue(u_file == x_file)

    @mock.patch.object(UserFile, 'get_last_modified')
    def test_userfile_compare_lastmodified(self, mock_mod):
        """Test compare_lastmodified"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        mock_mod.return_value = "2014-08-04T03:53:30Z"
        u_file = UserFile(api, {'name':'star.png'})
        u_file._last_modified = "2014-08-04T03:53:30Z"

        x_file = UserFile(api, {'name':'same.png'})
        x_file._exists = True
        self.assertTrue(x_file.compare_lastmodified(u_file))

        mock_mod.return_value = ""
        self.assertFalse(x_file.compare_lastmodified(u_file))

    @mock.patch.object(UserFile, '_get_windows_path')
    def test_userfile_create_query_specifier(self, mock_path):
        """Test create_query_specifier"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        u_file = UserFile(api, {})
        mock_path.return_value = "new_path"

        with self.assertRaises(FileMissingException):
            u_file.create_query_specifier()
        u_file._exists = True
        spec = u_file.create_query_specifier()
        self.assertEqual(spec, {'FileName':'Unknown',
                                'Timestamp':'',
                                'OriginalPath':'new_path'})

    @mock.patch.object(UserFile, '_get_windows_path')
    def test_userfile_create_submit_specifier(self, mock_path):
        """Test create_submit_specifier"""

        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        u_file = UserFile(api, {})
        mock_path.return_value = "new_path"

        with self.assertRaises(FileMissingException):
            u_file.create_submit_specifier()
        u_file._exists = True
        spec = u_file.create_submit_specifier()
        self.assertEqual(spec, {'Name':'Unknown',
                                'Timestamp':''})

    @mock.patch.object(UserFile, 'is_uploaded')
    def test_userfile_upload(self, mock_isup):
        """Test upload"""

        _callback = mock.Mock()
        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom", None)

        mock_isup.return_value = mock.create_autospec(UserFile)
        api.send_file.return_value = resp

        ufile = UserFile(api, {})
        self.assertIsNone(ufile.upload())
        self.assertEqual(ufile.upload(force=True), resp)
        api.send_file.assert_called_once_with(ufile, callback=None, block=4096)

        mock_isup.return_value = None
        self.assertEqual(ufile.upload(), resp)
        self.assertEqual(ufile.upload(force=True, callback=_callback, block=1), resp)
        api.send_file.assert_called_with(ufile, callback=_callback, block=1)

    @mock.patch('batchapps.files.UserFile')
    @mock.patch.object(UserFile, 'create_query_specifier')
    @mock.patch.object(UserFile, 'compare_lastmodified')
    def test_userfile_is_uploaded(self, mock_mod, mock_query, mock_ufile):
        """Test is_uploaded"""

        mock_mod.return_value = True
        result = mock.create_autospec(UserFile)
        result.name = "1"
        mock_ufile.return_value = result
        api = mock.create_autospec(batchapps.api.BatchAppsApi)

        ufile = UserFile(api, {'name':'1'})

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom", None)
        api.query_files.return_value = resp

        with self.assertRaises(RestCallException):
            ufile.is_uploaded()

        resp.success = True
        resp.result = ['1', '2', '3']
        self.assertIsInstance(ufile.is_uploaded(), UserFile)
        self.assertTrue(api.query_files.called)
        self.assertTrue(mock_query.called)
        self.assertEqual(mock_ufile.call_count, 3)
        mock_ufile.assert_called_with(mock.ANY, '3')

        result.name = "4"
        self.assertIsNone(ufile.is_uploaded())

    @mock.patch.object(UserFile, "is_uploaded")
    @mock.patch.object(batchapps.files.path, "getsize")
    def test_userfile_download(self, mock_size, mock_is_uploaded):
        """Test download"""

        _callback = mock.Mock()
        mock_size.return_value = 0
        api = mock.create_autospec(batchapps.api.BatchAppsApi)
        ufile = UserFile(api, {})
        download_dir = "test"

        mock_is_uploaded.side_effect = RestCallException(None, "Boom", None)
        with self.assertRaises(RestCallException):
            ufile.download(download_dir)
        
        mock_is_uploaded.side_effect = None
        mock_is_uploaded.return_value = None
        ufile.download(download_dir)
        self.assertFalse(api.props_file.called)

        ufile._exists = True
        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "Boom", None)
        api.props_file.return_value = resp
        mock_is_uploaded.return_value = ufile
        with self.assertRaises(RestCallException):
            ufile.download(download_dir)
            self.assertTrue(api.props_file.called)

        resp.success = True
        resp.result = 123
        api.props_file.return_value = resp
        r = mock.create_autospec(Response)
        r.success = False
        r.result = RestCallException(None, "Boom", None)
        api.get_file.return_value = r
        with self.assertRaises(RestCallException):
            ufile.download(download_dir)
        api.get_file.assert_called_with(ufile, resp.result, download_dir, callback=None, block=4096)
        
        r.success = True
        r.result = "test"
        ufile.download(download_dir, callback=_callback, block=1)
        api.get_file.assert_called_with(ufile, resp.result, download_dir, callback=_callback, block=1)

if __name__ == '__main__':
    unittest.main()
