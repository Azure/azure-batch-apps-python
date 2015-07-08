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
"""Unit tests for PoolManager"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from batchapps.pool_manager import PoolManager
from batchapps.api import Response
from batchapps.exceptions import RestCallException
from batchapps.files import FileCollection
from batchapps.pool import (
    Pool,
    PoolSpecifier)

# pylint: disable=W0212
class TestPoolManager(unittest.TestCase):
    """Unit tests for PoolManager"""

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.pool_manager.BatchAppsApi')
    @mock.patch('batchapps.pool_manager.PoolSpecifier')
    @mock.patch.object(PoolManager, 'get_pool')
    def test_poolmgr_create(self, mock_get, mock_pool, mock_api, mock_creds, mock_cfg):
        """Test create_spec"""

        spec = mock.create_autospec(PoolSpecifier)
        mgr = PoolManager(mock_creds, cfg=mock_cfg)

        pool = mgr.create(spec)
        self.assertFalse(mock_pool.called)
        self.assertTrue(spec.start.called)

        pool = mgr.create()
        mock_pool.assert_called_with(mock.ANY, 0, 1, False)
        self.assertTrue(mock_get.called)
        
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.pool_manager.BatchAppsApi')
    @mock.patch('batchapps.pool_manager.PoolSpecifier')
    def test_poolmgr_create_spec(self, mock_pool, mock_api, mock_creds, mock_cfg):
        """Test create_spec"""

        mgr = PoolManager(mock_creds, cfg=mock_cfg)
        spec = mgr.create_spec()
        mock_pool.assert_called_with(mock.ANY, 0, 1, False)

        spec = mgr.create_spec(target_size=3, max_tasks=3, communication=True)
        mock_pool.assert_called_with(mock.ANY, 3, 3, True)

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.pool_manager.BatchAppsApi')
    @mock.patch('batchapps.pool_manager.Pool')
    def test_poolmgr_get_pool(self, mock_pool, mock_api, mock_creds, mock_cfg):
        """Test get_pool"""

        mgr = PoolManager(mock_creds, cfg=mock_cfg)

        with self.assertRaises(ValueError):
            mgr.get_pool()

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.get_pool.return_value = resp

        with self.assertRaises(RestCallException):
            mgr.get_pool(url="http://test")
        mgr._client.get_pool.assert_called_with(url="http://test")

        resp.success = True
        resp.result = {'id':'1', 'autoPool':False, 'state':'test'}
        job = mgr.get_pool(url="http://test")
        mgr._client.get_pool.assert_called_with(url="http://test")
        mock_pool.assert_called_with(mgr._client, id='1', autoPool=False, state="test")

        resp.result = {'id':'1', 'name':'2', 'type':'3', 'other':'4'}
        job = mgr.get_pool(poolid="test_id")
        mgr._client.get_pool.assert_called_with(pool_id="test_id")
        
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.pool_manager.BatchAppsApi')
    @mock.patch('batchapps.pool_manager.Pool')
    def test_poolmgr_get_pools(self, mock_pool, mock_api, mock_creds, mock_cfg):
        """Test get_pools"""

        mgr = PoolManager(mock_creds, cfg=mock_cfg)

        resp = mock.create_autospec(Response)
        resp.success = False
        resp.result = RestCallException(None, "test", None)
        mgr._client.list_pools.return_value = resp

        with self.assertRaises(RestCallException):
            mgr.get_pools()
        mgr._client.list_pools.assert_called_with()

        resp.success = True
        resp.result = {'pools':[]}
        pools = mgr.get_pools()
        mgr._client.list_pools.assert_called_with()
        self.assertEqual(pools, [])
        self.assertEqual(len(mgr), 0)

        resp.result = {'totalCount':1,
                       'pools':[{'id':'abc', 'targetDedicated':'1', 'state':'active'}]}

        pools = mgr.get_pools()
        mock_pool.assert_called_with(mgr._client, **resp.result['pools'][0])
        self.assertEqual(len(pools), 1)

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.pool_manager.BatchAppsApi')
    @mock.patch.object(PoolManager, 'get_pools')
    def test_poolmgr_clear_pools(self, mock_pool, mock_api, mock_creds, mock_cfg):
        """Test clear_pools"""

        mgr = PoolManager(mock_creds, cfg=mock_cfg)
        mgr.count = 1
        poolA = mock.create_autospec(Pool)
        mock_pool.return_value = [poolA]

        failed = mgr.clear_pools()
        self.assertEqual(failed, [])
        self.assertEqual(len(mgr), 0)
        self.assertTrue(poolA.delete.called)

        poolA.delete.side_effect = RestCallException(None, "test", None)
        mgr.count = 1
        failed = mgr.clear_pools()
        self.assertEqual(failed, [(poolA, poolA.delete.side_effect)])
        self.assertEqual(len(mgr), 1)

        mock_pool.side_effect = RestCallException(None, "test", None)
        with self.assertRaises(RestCallException):
            mgr.clear_pools()

if __name__ == '__main__':
    unittest.main()