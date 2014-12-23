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
import multiprocessing

from .config import Configuration
from .job import JobSubmission, SubmittedJob
from .api import BatchAppsApi
from .utils import Listener
from .exceptions import RestCallException

class JobManager(object):
    """
    This is the only class that a user should need to import to access all
    job manipulation. Contains general functionality for the creation
    of new job submissions and retrieveing data on submitted jobs.
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
        """Return the number of cloud jobs available to the manager

        :Returns:
            - The number of jobs submitted to the cloud by the user. This value
              will only be populated once :meth:`.get_jobs()` has been called.
        """
        return self.count

    def get_job(self, job=None, url=None, jobid=None):
        """
        Get details of single job. Input can be either a
        :class:`.SubmittedJob` object, a URL, or a job ID.
        If more than one option is set, they will be prioritized in that order.

        :Kwargs:
            - job (:class:`.SubmittedJob`): A job object to be updated.
            - url (str): The URL to a the details of a job, as returned by
              :meth:`.JobSubmission.submit()`.
            - jobid (str): The ID of a submitted job, as retrieved from
              Mission Control or returned by :meth:`.JobSubmission.submit()`.

        :Returns:
            - An updated or new :class:`.SubmittedJob` object.

        :Raises:
            - :exc:`AttributeError` if invalid parameters have been set.
            - :exc:`.RestCallException` if an error occured during the request.
        """
        resp = None
        if hasattr(job, 'update'):
            resp = job.update()
            if resp:
                return job

        elif url:
            resp = self._client.get_job(url=str(url))

        elif jobid:
            resp = self._client.get_job(job_id=str(jobid))

        else:
            raise ValueError("Call must be passed either a jobid, "
                             "url or a SubmittedJob object")

        if resp.success:
            return SubmittedJob(self._client,
                                resp.result.pop('id'),
                                resp.result.pop('name'),
                                resp.result.pop('type'),
                                **resp.result)
        else:
            raise resp.result

    def get_jobs(self, index=0, per_call=10, name=None):
        """
        Get a list of the user's jobs.
        This call also sets the :attr:`.JobManager.count` attribute to reflect
        the total jobs submitted by the user.

        :Kwargs:
            - index (int): The start index of the list of jobs to be returned.
              Default is 0, i.e. return all jobs from the beginning.
            - per_call (int): Number of jobs to be returned. Default is 10.
            - name (str): Only return jobs whose names contain this string.

        :Returns:
            - A list of :class:`.SubmittedJob` objects.

        :Raises:
            - :exc:`.RestCallException` if an error occured during the request.
        """
        if name:
            resp = self._client.list_jobs(int(index),
                                          int(per_call),
                                          name=str(name))
        else:
            resp = self._client.list_jobs(int(index), int(per_call))

        if resp.success:
            self.count = resp.result.get('totalCount', 0)

            try:
                resp_jobs = [SubmittedJob(
                    self._client,
                    _job.pop('id'),
                    _job.pop('name'),
                    _job.pop('type'),
                    **_job) for _job in resp.result['jobs']]

                return resp_jobs

            except (KeyError, TypeError) as excp:
                raise RestCallException(
                    type(excp),
                    "Malformed job response object: {0}".format(excp),
                    excp)

        else:
            raise resp.result

    def create_job(self, name, **jobdetails):
        """Create a new job submission.

        :Args:
            - name (str): The name for the new job.

        :Kwargs:
            - jobdetails (dict): Additional job settings or parameters can be
              added as keyword arguments. These include:

                - 'params': A string dict of job parameters to add to the
                  submission.
                - 'files': A :class:`.FileCollection` of required files to
                  include with the job.
                - 'job_file': The name (str) of the source file that should
                  be used to start the job. This filename should be
                  included in the above ``files`` collection.
                - 'instances': The number (int) of instances to allocate
                  to the job on submission.

        :Returns:
            - A new :class:`.JobSubmission` object.
        """
        return JobSubmission(self._client, str(name), **jobdetails)

    def submit(self, submitjob, upload_threads=None):
        """Submit a job, and upload all its assets

        :Args:
            - submitjob (:class:`.JobSubmission`): The job to be submitted.

        :Kwargs:
            - upload_threads (int): Number of concurrent asset uplaods.
              Default is 1.

        :Returns:
            - A job susbmission response dictionary in the format:
              ``{'jobId': '', 'link': ''}``

              .. warning:: Dictionary response will be deprecated to be replaced
                 by a :class:`.SubmittedJob` object in 1.0 release.

        :Raises:
            - :exc:`TypeError` if ``submitjob`` is not a JobSubmission.
            - :exc:`.RestCallException` if job submission failed.
        """
        if not hasattr(submitjob, 'submit'):
            raise TypeError("Must submit a JobSubmission object.")

        self._log.debug("Processing job: {0}".format(submitjob.name))

        if submitjob.source not in submitjob.required_files:
            self._log.warning("The job file for job {0} has not been included "
                              "in the required files list. "
                              "Consider revising.")

        failed_uploads = submitjob.required_files.upload(
            threads=upload_threads)

        if len(failed_uploads) > 0:
            raise Exception(
                "Some required files failed to upload. "
                "Discontinuing submission of job {0}.".format(submitjob.name))

        return submitjob.submit()
