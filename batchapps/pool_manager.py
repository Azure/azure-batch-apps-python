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

import logging

from .config import Configuration
from .pool import Pool, PoolSpecifier
from .api import BatchAppsApi
from .exceptions import RestCallException

class PoolManager(object):
    """
    This is the only class that a user should need to import to access all
    pool manipulation. Currently only retrieves data on current pools.
    To be expanded to allow for creation and resizing of pools.
    """

    def __init__(self, credentials, cfg=None):
        """
        :Args:
            - credentials (:class:`.Credentials`): User credentials for REST
              API authentication.

        :Kwargs:
            - cfg (:class:`.Configuration`): Configuration of the Batch Apps
              client session. If not set, a default config will be used.
       """
        self._log = logging.getLogger('batch_apps')
        self._client = BatchAppsApi(
            credentials, cfg if cfg else Configuration())
        self.count = None

    def __len__(self):
        """Return the number of pools running in the service

        :Returns:
            - The number of jobs submitted to the cloud by the user. This value
              will only be populated once :meth:`.get_jobs()` has been called.
        """
        return self.count

    def create_pool(self, target_size=0, max_tasks=1,
                 communication=False):
        """
        Crete a new :class:`.PoolSpecifier` object, which can then be deployed
        and referenced for use on job submission.
        The minimum number of running instances for a pool with 1 task per TVM
        is 3 to prevent a deadlock.

        :Kwargs:
            - target_size (int): The target number of instances in the pool.
              Default is 0 (i.e. and empty pool).
            - max_tasks (int): Maximum number of tasks per TVM. Default is 1.
            - communication (bool): Whether tasks running on TVMs
              in the pool need to ba able to communicated directly with each
              other. Default is ``False``.

        :Returns:
            - A new :class:`.PoolSpecifier` object.
        """

        new_pool = PoolSpecifier(self._client, target_size, max_tasks, communication)
        return new_pool

    def get_pool(self, url=None, poolid=None):
        """
        Get details of single pool. Input can be either a URL, or a pool ID.
        If more than one option is set, they will be prioritized in that order.

        :Kwargs:
            - url (str): The URL to a the details of a pool, as returned by
              :meth:`.PoolSpecifier.deploy()`.
            - poolid (str): The ID of a submitted job, as retrieved from
              Mission Control or returned by :meth:`.PoolSpecifier.deploy()`.

        :Returns:
            - An updated or new :class:`.Pool` object.

        :Raises:
            - :exc:`AttributeError` if invalid parameters have been set.
            - :exc:`.RestCallException` if an error occured during the request.
        """
        resp = None

        if url:
            resp = self._client.get_pool(url=str(url))

        elif poolid:
            resp = self._client.get_pool(pool_id=str(poolid))

        else:
            raise ValueError("Call must be passed either a pool id or a URL")

        if resp.success:
            return Pool(self._client, **resp.result)
                                
        else:
            raise resp.result

    def get_pools(self):
        """
        Get a list of the user's pools.
        This call also sets the :attr:`.PoolManager.count` attribute to reflect
        the total number of pools in the service.

        :Returns:
            - A list of :class:`.Pool` objects.

        :Raises:
            - :exc:`.RestCallException` if an error occured during the request.
        """
        resp = self._client.list_pools()

        if resp.success:
            self.count = resp.result.get('totalCount', 0)

            try:
                resp_pools = [Pool(self._client, **_pool)
                              for _pool in resp.result['pools']]

                return resp_pools

            except (KeyError, TypeError) as excp:
                raise RestCallException(
                    type(excp),
                    "Malformed pool response object: {0}".format(excp),
                    excp)

        else:
            raise resp.result

    def clear_pools(self):
        """
        Delete all currently active pools. Starts by calling :meth:`.get_pools`
        to retrieve up-to-date pool list.
        
        :Returns:
            - A list of any pools that failed to delete. If the call was
              successfull this list will be empty, otherwise it will hold
              a tuple with the pool that errored, and the exception:
              ``[(poolA, exception), (poolB, exception)]``

        :Raises:
            - A :exc:`.RestCallException` if call to retrieve pool list fails.
        """
        pools = self.get_pools()
        undeleted = []

        for pool in pools:

            try:
                pool.delete()
            except RestCallException as exp:
                undeleted.append((pool, exp))

        self.count = len(undeleted)
        return undeleted