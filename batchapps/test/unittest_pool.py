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
"""Unit tests for Pool and PoolSpecifier"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from batchapps.pool import (
    Pool,
    PoolSpecifier)
from batchapps.api import (
    BatchAppsApi,
    Response)

from batchapps.exceptions import RestCallException

# pylint: disable=W0212
class TestPool(unittest.TestCase):
    """Unit tests for Pool"""

    def test_pool_create(self):
        """Test Pool object"""

        api = mock.create_autospec(BatchAppsApi)
        pool = Pool(api)
        self.assertIsNone(pool.id)
        self.assertIsNone(pool.created)
        self.assertEqual(pool.target_size, 0)

        pool_spec = {
            'id': 'abc',
            'creationTime': '',
            'targetDedicated': '5',
            'state': 'active',
            'communication': True
            }

        pool = Pool(api, **pool_spec)
        self.assertEqual(pool.id, 'abc')
        self.assertEqual(pool.created, '')
        self.assertEqual(pool.target_size, 5)
        self.assertEqual(pool.communication, True)

    def test_pool_delete(self):
        """Test delete"""

        api = mock.create_autospec(BatchAppsApi)
        api.delete_pool.return_value = mock.create_autospec(Response)
        api.delete_pool.return_value.success = True
        pool = Pool(api)

        pool.delete()
        api.delete_pool.assert_called_with(None)
        api.delete_pool.return_value.success = False
        api.delete_pool.return_value.result = RestCallException(None, "Test", None)

        with self.assertRaises(RestCallException):
            pool.delete()

    @mock.patch.object(Pool, 'update')
    def test_pool_resize(self, mock_update):
        """Test resize"""

        api = mock.create_autospec(BatchAppsApi)
        api.resize_pool.return_value = mock.create_autospec(Response)
        api.resize_pool.return_value.success = True
        pool = Pool(api)

        pool.resize(5)
        api.resize_pool.assert_called_with(None, 5)
        mock_update.assert_called_with()

        with self.assertRaises(ValueError):
            pool.resize("test")

        api.resize_pool.return_value.success = False
        api.resize_pool.return_value.result = RestCallException(None, "Test", None)

        mock_update.called = False
        with self.assertRaises(RestCallException):
            pool.resize(1)
        self.assertFalse(mock_update.called)

    def test_pool_update(self):
        """Test delete"""

        api = mock.create_autospec(BatchAppsApi)
        pool = Pool(api)
        api.get_pool.return_value = mock.create_autospec(Response)
        api.get_pool.return_value.success = True
        api.get_pool.return_value.result = {
            'targetDedicated':'5',
            'currentDedicated':'4',
            'state':'active',
            'allocationState':'test',
            }

        self.assertEqual(pool.target_size, 0)
        self.assertEqual(pool.current_size, 0)
        self.assertEqual(pool.state, None)
        self.assertEqual(pool.allocation_state, None)
        self.assertEqual(pool.resize_error, '')
        pool.update()
        api.get_pool.assert_called_with(pool_id=None)
        self.assertEqual(pool.target_size, 5)
        self.assertEqual(pool.current_size, 4)
        self.assertEqual(pool.state, 'active')
        self.assertEqual(pool.allocation_state, 'test')
        self.assertEqual(pool.resize_error, '')

        api.get_pool.return_value.success = False
        api.get_pool.return_value.result = RestCallException(None, "Test", None)

        with self.assertRaises(RestCallException):
            pool.update()

class TestPoolSpecifier(unittest.TestCase):
    """Unit tests for PoolSpecifier"""

    def test_poolspecifier_create(self):
        """Test PoolSpecifier object"""

        api = mock.create_autospec(BatchAppsApi)
        pool = PoolSpecifier(api)
        self.assertEqual(pool.target_size, 0)
        self.assertEqual(pool.max_tasks, 1)
        self.assertEqual(pool.communication, False)
        self.assertEqual(pool.certificates, [])

        pool = PoolSpecifier(api, target_size=5, max_tasks=2, communication=True)
        self.assertEqual(pool.target_size, 5)
        self.assertEqual(pool.max_tasks, 2)
        self.assertEqual(pool.communication, True)
        self.assertEqual(pool.certificates, [])

    def test_poolspecifier_start(self):
        """Test start"""

        api = mock.create_autospec(BatchAppsApi)
        api.add_pool.return_value.success = True
        api.add_pool.return_value.result = {
            'poolId':'abc', 'link':{'href':'test.com'}}

        pool = PoolSpecifier(api)
        new_pool = pool.start()
        self.assertEqual(new_pool, {'id':'abc', 'link':'test.com'})
        api.add_pool.assert_called_with(0, 1, False, [])

        api.add_pool.return_value.success = False
        api.add_pool.return_value.result = RestCallException(None, "Test", None)
        with self.assertRaises(RestCallException):
            pool.start()

    def test_poolspecifier_add_cert(self):

        api = mock.create_autospec(BatchAppsApi)
        pool = PoolSpecifier(api)
        pool.add_cert("test_thumb")

        self.assertEqual(pool.certificates, [{
            'thumbprint':'test_thumb',
            'thumbprintAlgorithm':'SHA1',
            'storeLocation':'CurrentUser',
            'storeName':'My'}])

        pool.add_cert("test_thumb", store_location="test", store_name=None)

        self.assertEqual(pool.certificates, [{
            'thumbprint':'test_thumb',
            'thumbprintAlgorithm':'SHA1',
            'storeLocation':'CurrentUser',
            'storeName':'My'},{
            'thumbprint':'test_thumb',
            'thumbprintAlgorithm':'SHA1',
            'storeLocation':'test',
            'storeName':'None'}])

        pool.id = None
        pool.certificates = [0,1,2,3,4,5,6,7,8,9]
        pool.add_cert("new_cert")
        self.assertEqual(pool.certificates, [0,1,2,3,4,5,6,7,8,9])

if __name__ == '__main__':
    unittest.main()