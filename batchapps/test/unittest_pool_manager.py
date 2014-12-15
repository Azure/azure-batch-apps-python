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
