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

class Pool(object):
    """Reference for a Batch VM Pool"""

    def __init__(self, client, **kwargs):
        """New pool reference

        :Args:
            - client (:class:`.BatchAppsApi`): A configured and
              authenticated api client.
        
        :Kwargs:
            - id (str): The pool guid.
            - creationTime (str): Time the pool was created.
            - targetDedicated (int): The target size of the pool.
            - currentDedicated (int): The current pool size.
            - state (str): The current state of the pool. Value can be:
              "active", "upgrading" or "deleting".
            - allocationState (str): The allocation state of the pool.
              Value can be: "steady", "resizing", or "stopping".
            - maxTasksPerTVM (int): Max tasks that can run on a single TVM.
            - resizeError (str): Specifies the resize error encountered
              while performing the last resize on the pool. Otherwise ``None``.
            - communication (bool): Indicates whether tasks running on TVMs in
              the pool need to be able to communicate directly with each other.
            - certificateReferences (list): A list of certificates that need
              to be installed on the TVMs of the pool. Max 10.
            - jobs (list): A list of dictionaries refering to the jobs
              currently running on the pool.
            - poolDetailLink (dict): A dictiory with url info to pool details.
        """
        self._api = client
        self._log = logging.getLogger('batch_apps')

        self.id = kwargs.get('id')
        self.created = kwargs.get('creationTime')
        self.auto = kwargs.get('autoPool', False)
        self.target_size = int(kwargs.get('targetDedicated', 0))
        self.current_size = int(kwargs.get('currentDedicated', 0))
        self.state = kwargs.get('state')
        self.allocation_state = kwargs.get('allocationState')
        self.max_tasks = int(kwargs.get('maxTasksPerTVM', '0'))
        self.resize_error = str(kwargs.get('resizeError', ''))
        self.communication = kwargs.get('communication')
        self.certificates = list(kwargs.get('certificateReferences', []))
        self.jobs = list(kwargs.get('activeJobs', []))
        self.url = kwargs.get('poolDetailLink', {'href':None})['href']

    def __eq__(self, compare_to):
        """
        Compare two :class:`.Pool` objects to see if
        they reference the same pool.

        :Args:
            - compare_to (:class:`.Pool`): The pool to check against.

        :Returns:
            - ``True`` if the pools are the same, else ``False``.
        """

        try:
            checks = []
            checks.append(self.id == compare_to.id)
            checks.append(self.created == compare_to.created)
            checks.append(self.max_tasks == compare_to.max_tasks)
            checks.append(self.target_size == compare_to.target_size)
            return all(checks)

        except AttributeError:
            return False

    def delete(self):
        """
        Delete the pool.

        :Raises:
            - :class:`.RestCallException` if delete failed.
        """
        delete = self._api.delete_pool(self.id)

        if not delete.success:
            raise delete.result

        self._log.info("Deleted pool {0}".format(self.id))

    def resize(self, target):
        """
        Resize the pool. This will fail with status 409 if the pool attempts
        to resize beyond the core allocation of the Batch Apps service.
        After the call to resize, the pool object will be updated.

        :Args:
            - target (int): The new target instance count to update the
              pool to.

        :Raises:
            - :class:`.RestCallException` if resize failed.

        """
        resize = self._api.resize_pool(self.id, int(target))

        if not resize.success:
            raise resize.result
        self._log.info("Initiated pool resize to new target: "
                       "{0}".format(target))
        self.update()

    def update(self):
        """
        Update the reference to the pool.

        :Raises:
            - :class:`.RestCallException` if resize failed.

        """
        updated = self._api.get_pool(pool_id=self.id)
        if not updated.success:
            raise updated.result

        self.created = updated.result.get('creationTime')
        self.target_size = int(updated.result.get('targetDedicated', 0))
        self.current_size = int(updated.result.get('currentDedicated', 0))
        self.state = updated.result.get('state')
        self.allocation_state = updated.result.get('allocationState')
        self.resize_error = str(updated.result.get('resizeError', ''))
        self.jobs = list(updated.result.get('jobs', []))

        self._log.info("Updated pool reference.")

        


class PoolSpecifier(Pool):
    """
    A new user-created Pool. This class can be used to create a pool on-the-fly
    during job submission, or can be used to create a pool manually before
    submission.
    """

    def __init__(self, client, target_size=0, max_tasks=1,
                 communication=False):
        """
        :Args:
            - client (:py:class:`.BatchAppsApi`): A configured and
              authenticated API instance.
        
        :Kwargs:
            - target_size (int): The target size of the pool. Default is 0.
            - max_tasks (int): Max tasks that can run on a single TVM.
              Default is 1.
            - communication (bool): Indicates whether tasks running on TVMs
              in the pool need to ba able to communicated directly with each
              other. Default is ``False``.
        """
        self._api = client
        self._log = logging.getLogger('batch_apps')

        self.target_size = int(target_size)
        self.max_tasks = int(max_tasks)
        self.communication = communication
        self.certificates = []

    def add_cert(self, thumbprint, algorithm='SHA1',
                 store_location='CurrentUser', store_name='My'):
        """
        Add a certificate reference to the PoolSpecifier. The certificate will
        only be added to the Pool if it has not yet been started, or if
        it does not yet have 10 certificates.

        :Args:
            - thumbprint (str): The X509 certificate thumbprint property of
              the certificate. 

        :Kwargs:
            - algorithm (str): The algorithm that was used to hash the
              certificate. Currently SHA1 is the only supported algorithm.
            - store_location (str): The location of the certificate store where
              the certificate needs to be installed on the TVM. Possible values
              are CurrentUser and LocalMachine. Default is 'CurrentUser'.
            - store_name (str): The name of the certificate store where the
              certificate needs to be installed on the TVM. Possible values
              include the built-in store names My, Root, CA, Trust, Disallowed,
              TrustedPeople, TrustedPublisher, AuthRoot, AddressBook or any
              custom store name. If a custom store name is specified, the store
              is automatically created. Default is 'My'.

        :Returns:
            - ``True`` if the certificate was added, else ``False``.

        """

        if len(self.certificates) >= 10:
            self._log.warning('Max number of certificates has been reached.')
            return False

        self.certificates.append({
                'thumbprint': str(thumbprint),
                'thumbprintAlgorithm': str(algorithm),
                'storeLocation': str(store_location),
                'storeName': str(store_name)
                })

        return True


    def start(self):
        """
        Start a pool according to this specification.
        The call will fail with status 409 if the new pool
        exceeds the maximum number of allocated pools.

        :Returns:
            - A dictionary with the new pool details:
              ``{'id': Pool ID, 'link': Pool URL}``

        :Raises:
            - A :class:`.RestCallException` if the call failed.

        """
        pool = self._api.add_pool(self.target_size, self.max_tasks,
                                self.communication, self.certificates)

        if not pool.success:
            raise pool.result

        return {'id': pool.result['poolId'],
                'link': pool.result['link']['href']}

        



