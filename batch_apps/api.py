#-------------------------------------------------------------------------
# The Azure Batch Apps Python Client ver. 0.1.0
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
""" Client for the Batch Apps Managment API.
"""

from batch_apps import rest_client
from batch_apps.files import UserFile
from batch_apps import utils
from batch_apps.exceptions import (
    RestCallException,
    FileMissingException)

import logging

API_VERSION = "2014-10-01-preview"

class Response(object):
    """
    A simple container object for the response of the REST call.

    :Attributes:
        - success (bool)
        - result
    """

    def __init__(self, success, output=None):
        """
        :Args:
            - success (bool): Whether the REST call completed successfully and
              returned an applicable result.

        :Kwargs:
            - output: The response from the REST client. This could be the
              result of a successful api call, or it could hold exception
              information for a failed call. Defaults to None.
        """
        self.success = success
        self.result = output

class BatchAppsApi(object):
    """
    Specification of Batch Apps Management API, abstracted away
    from the implementation of the :mod:`rest_client`.
    This class should directly reflect the full functionality of the API,
    without adding any additional layers of data processing.

    :Attributes:
        - headers (dict)
    """

    def __init__(self, credentials, config):
        """
        :Args:
            - credentials (:class:`.Credentials`): Credentials with which all
              API calls will be authenticated.
            - config (:class:`.Configuration`): Configuration of the
              application the jobs will be submitted as, as well as endpoint
              and logging configuration.
        """
        self._config = config
        self._log = logging.getLogger('batch_apps')
        self._auth = credentials

        self.headers = {"Accept": "application/json",
                        "x-ms-version": API_VERSION,
                        "Content-Type": "application/json"}

    def app(self):
        """Retrieve the current jobtype from the :class:`.Configuration`.

        :Returns:
            - The current application from the configuration (str).
        """
        return self._config.application()

    def url(self, api_call):
        """Format API endpoint url.

        :Args:
            - api_call (str): the url of the method that will be appended to
              the root url provided by the :class:`.Configuration`.

        :Returns:
            - The complete, formatted url (str)
        """
        end_p = self._config.endpoint()
        self._log.debug("Formatting url: https://{endpoint}/api/{api}".format(
            endpoint=end_p,
            api=api_call))

        return "https://{endpoint}/api/{api}".format(
            endpoint=end_p,
            api=api_call)

    def default_params(self):
        """
        Get the default parameters for the application.
        Retrieves the parameters tied to the application from the
        :class:`.Configuration`

        :Returns:
            - Dictionary of strings of the configured parameters
        """
        return self._config.default_params()

    def list_jobs(self, index=0, per_call=10, name=None):
        """Lists the users jobs.

        :Kwargs:
            - index (int): The starting index from which the list of jobs will
              be returned. Default is 0, i.e. return all jobs from the start.
            - per_call (int): The number of job entries from ``index`` to
              return. Default is 10.
            - name (str): Return only the jobs whose name contains the given
              string. Default is None.

        :Returns:
            - :class:`.Response` object containing success of call. If
              successful, the ``Response.result`` will contain a list of
              jobs as dictionaries. If failed, ``Response.result`` will
              hold the :exc:`.RestCallException`.
        """
        self._log.debug("list_jobs, index={0}, per_call={1}, name={2}".format(
            index,
            per_call, name))

        url = self.url("jobs")
        req_set = {"maxResults": per_call, "startIndex": index}

        if name:
            req_set["nameContains"] = str(name)

        try:
            get_resp = rest_client.get(self._auth, url,
                                       self.headers,
                                       params=req_set)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            if utils.valid_keys(get_resp, ['totalCount', 'jobs']):
                return Response(True, get_resp)
            return Response(
                False,
                RestCallException(KeyError,
                                  "Key not in response message",
                                  get_resp))

    def get_job(self, job_id=None, url=None):
        """
        Gets information about a job.
        Job info can be retrieved by supplying **either** the job's ID
        **or** a url to the job. If both are supplied, url is used.

        :Kwargs:
            - job_id (str): Guid of the job on which info is requested.
            - url (str): A complete url to the job info.

        :Returns:
            - A :class:`.Response` object containing the job details as a
              dictionary, if successful. Otherwise the Response will
              contain the :exc:`.RestCallException`.

        :Raises:
            - :class:`.RestCallException` if neither job ID or url are
              supplied.
            - :class:`.RestCallException` if job details dictionary is
              malformed / missing necessary keys
        """
        self._log.debug("get_job, job_id={0}, url={1}".format(job_id, url))
        if not url and job_id:
            url = self.url("jobs/{jobid}").format(jobid=job_id)

        elif not url and not job_id:
            return Response(
                False,
                RestCallException(AttributeError,
                                  "Either job_id or url must be set",
                                  None))

        try:
            get_resp = rest_client.get(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            if utils.valid_keys(get_resp, ['id', 'name', 'type']):
                return Response(True, get_resp)
            return Response(
                False,
                RestCallException(KeyError,
                                  "incorrectly formatted job response",
                                  get_resp))

    def send_job(self, job_message):
        """Submits a job.

        :Args:
            - job_message (dict): A job specification formatted as a
              dictionary.

        :Returns:
            - A :class:`.Response` object containing a dictionary of the newly
              submitted job's ID and details url if successful. Otherwise the
              Response will contain the :exc:`.RestCallException`.

        :Raises:
            - :class:`.RestCallException` if new job dictionary is
              malformed / missing necessary keys.
        """
        self._log.debug("send_job, job_message={0}".format(job_message))
        url = self.url("jobs")

        try:
            post_resp = rest_client.post(self._auth,
                                         url,
                                         self.headers,
                                         message=job_message)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            if utils.valid_keys(post_resp, ['jobId', 'link']):
                return Response(True, post_resp)
            return Response(
                False,
                RestCallException(KeyError,
                                  "incorrectly formatted job response",
                                  post_resp))

    def get_log(self, job_id, start=None, max_lines=100):
        """
        Gets log messages for a job.
        These are the Batch Apps system logs, rather than those of the
        application.

        :Args:
            - job_id (str): The guid of the job on which to download the logs.

        :Kwargs:
            - start (str): The start time from which the logs will be
              downloaded. If not specified, the default is from the
              beginning of the job.
            - max_lines (int): The max number of logging messages to retrieve.
              Default is 100. If set to ``None``, all messages from start
              time will be retrieved.

        :Returns:
            - A :class:`.Response` object with a dictionary containing the
              timestamp of the most recent message returned and a list of
              the log messages, represented as dictionaries, with the message
              text, timestamp and task id that the message applies to.
            - If the call failed, the response contains the
              :class:`.RestCallException`.
        """
        self._log.debug("get_log, job_id={0}, start={1}, max_lines={2}".format(
            job_id,
            start,
            max_lines))

        url = self.url("jobs/{jobid}/log").format(jobid=job_id)
        get_params = {}
        if start:
            get_params['since'] = str(start)
        if max_lines:
            get_params['maxResults'] = int(max_lines)

        try:
            get_resp = rest_client.get(self._auth,
                                       url,
                                       self.headers,
                                       params=get_params)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            #TODO: Check for specific keys here.
            return Response(True, get_resp)

    def cancel(self, job_id):
        """Cancels a running job.

        :Args:
            - job_id (str): guid of the job to be cancelled.

        :Returns:
            - A :class:`.Response` object with the POST response, however this
              is not required if the call is successful. The call will only
              be successful if the job can be and is cancelled.
            - If the job is not running (and therefore cannot be cancelled),
              the call will fail and the :class:`.RestCallException` will be
              returned in the :class:`.Response` object.
            - Any other communication failures will also return a
              :class:`.RestCallException`.
        """
        self._log.debug("cancel, job_id={0}".format(job_id))
        url = self.url("jobs/{jobid}/actions/cancel").format(jobid=job_id)

        try:
            post_resp = rest_client.post(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, post_resp)

    def reprocess(self, job_id):
        """
        Reprocesses any failed tasks in the job.
        This call will also re-activate a job if it has a 'Failed' status.

        :Args:
            - job_id (str): ID of the job to be reprocessed.

        :Returns:
            - A :class:`.Response` object containing a dictionary with the job
              ID of the reprocessed job and a url to retrieve the job
              information (see :meth:`.BatchAppsApi.get_job()`).
            - If the call failed the response will hold the
              :class:`.RestCallException`.
        """
        self._log.debug("reprocess, job_id={0}".format(job_id))
        url = self.url("jobs/{jobid}/actions/reprocess").format(jobid=job_id)

        try:
            post_resp = rest_client.post(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, post_resp)

    def list_outputs(self, job_id):
        """
        Lists the output files produced by a job.
        This method will only list final outputs of the job, created by a
        Merge Task.
        To retrieve a list of all files created by all tasks of the job use
        :meth:`.list_output_files()`.
        Can be used to ascertain the output filenames before calling the
        generic output download url.

        :Args:
            - job_id (str): ID of the job whose outputs will be listed.

        :Returns:
            - A list of the outputs represented as dictionaries, each with
              the 'name' and 'type' of the output as well as a download
              'link'. Contained in a :class:`.Response`. If the call failed,
              Response will contain the :class:`.RestCallException`.
        """
        self._log.debug("list_outputs, job_id={0}".format(job_id))
        url = self.url("jobs/{jobid}/outputs").format(jobid=job_id)

        try:
            get_resp = rest_client.get(self._auth, url, self.headers)

        except  RestCallException as exp:
            return Response(False, exp)

        outputs = []
        if (not 'jobOutputs' in get_resp
            or not isinstance(get_resp['jobOutputs'], list)):

            return Response(
                False,
                RestCallException(KeyError,
                                  "jobOutputs key not in response message",
                                  get_resp))

        # Reformat output dictrionary to be more manageable
        for output in get_resp['jobOutputs']:
            outputs.append({
                'name': output.get('name'),
                'link': output.get('link', {'href':None}).get('href'),
                'type': output.get('kind')
                })
        return Response(True, outputs)

    def get_output(self,
                   download_dir,
                   size,
                   fname,
                   overwrite,
                   job_id=None,
                   otype='output',
                   url=None):
        """
        Gets the content of the job output or its thumbnail.
        Either ``url``, or both ``job_id`` and ``otype`` must be set.
        If all three are set, url will be used.

        :Args:
            - download_dir (str): The full path to the directory where the
              output will be downloaded to.
            - size (int): The size in bytes of the file to be downloaded.
              Used for progress reporting.
            - fname (str): The name of the output file to be downloaded.
            - overwrite (bool): Whether to overwrite an existing file if
              present.

        :Kwargs:
            - job_id (str): The ID of the job whose output will be downloaded.
              Default is None.
            - otype (str): The type of output to be downloaded, must be a
              string in ``['output', 'preview']``.
            - url (str): The url directly to the file to be downloaded. If
              supplied, ``job_id`` and ``otype`` will not be used.
              Default is None.

        :Returns:
            - :class:`.Response` with the GET response, however this is not
              required if the call was successful.
            - :class:`.Response` with :exc:`AttributeError` if the correct
              url arguments are not supplied.
            - :class:`.Response` with :class:`.RestCallException` if the
              download failed.
        """
        self._log.debug(
            "get_output, download_dir={dd}, size={sz}, fname={fn}, "
            "overwrite={ow}, job_id={ji}, url={ur}, otype={ot}".format(
                dd=download_dir,
                sz=size,
                fn=fname,
                ow=overwrite,
                ji=job_id,
                ur=url,
                ot=otype))

        if not url and job_id:
            if otype.lower() not in ['output', 'preview']:
                return Response(
                    False,
                    RestCallException(
                        ValueError,
                        "output type must be 'output' or 'preview'",
                        None))

            url = self.url("jobs/{jobid}/outputs/{type}").format(jobid=job_id,
                                                                 type=otype)

        elif not url and not job_id:
            return Response(
                False,
                RestCallException(AttributeError,
                                  "Either job_id or url must be set",
                                  None))

        try:
            get_resp = rest_client.download(self._auth,
                                            url,
                                            self.headers,
                                            download_dir,
                                            size,
                                            overwrite,
                                            f_name=fname)

        except RestCallException as exp:
            return Response(False, exp)
        else:
            return Response(True, get_resp)

    def props_output(self, job_id=None, otype='output', url=None):
        """
        Gets the properties of the job output or preview.
        Used to obtain the size of the final job output or its thumbnail,
        which is returned in the response Content Length header.
        Either ``url``, or both ``job_id`` and ``otype`` must be set (although
        ``otype`` is already set by default).
        If all three are set, url will be used.

        :Kwargs:
            - job_id (str): The ID of the job whose output will be checked.
              Default is None.
            - otype (str): The type of output to be checked, must be a
              string in ``['output', 'preview']``.
            - url (str): The url directly to the file to be checked. If
              supplied, ``job_id`` and ``otype`` will not be used.
              Default is None.

        :Returns:
            - :class:`.Response` with the requested output size in bytes (int)
              if the call was successful.
            - :class:`.Response` with :exc:`AttributeError` if the correct url
              arguments are not supplied.
            - :class:`.Response` with :class:`.RestCallException` if the
              download failed.
        """
        self._log.debug("props_output, job_id={0}, "
                        "otype={1}, url={2}".format(job_id, otype, url))

        if not url and job_id:
            if otype not in ['output', 'preview']:
                return Response(
                    False,
                    RestCallException(
                        ValueError,
                        "output type must be 'output' or 'preview'",
                        None))

            url = self.url("jobs/{jobid}/outputs/{type}").format(jobid=job_id,
                                                                 type=otype)

        elif not url and not job_id:
            return Response(
                False,
                RestCallException(AttributeError,
                                  "Either job_id or url must be set",
                                  None))

        try:
            head_resp = rest_client.head(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, head_resp)

    def list_output_files(self, job_id):
        """Lists the intermediate output files produced during a job.

        :Args:
            - job_id (str): The ID of the job whose outputs will be listed.

        :Returns:
            - A list of the outputs represented as dictionaries, each with the
              'name' and 'type' of the output as well as a download 'link'.
              Contained in a :class:`.Response`. If the call failed, Response
              will contain the :class:`.RestCallException`.
        """
        self._log.debug("list_output_files, job_id={0}".format(job_id))
        url = self.url("jobs/{jobid}/outputs/files").format(jobid=job_id)

        try:
            get_resp = rest_client.get(self._auth, url, self.headers)

        except  RestCallException as exp:
            return Response(False, exp)

        outputs = []
        if (not 'outputs' in get_resp
            or not isinstance(get_resp['outputs'], list)):

            return Response(False,
                            RestCallException(
                                KeyError,
                                "outputs key not in response message",
                                get_resp))

        for output in get_resp['outputs']:
            outputs.append({
                'name': output.get('name'),
                'link': output.get('link', {'href':None}).get('href'),
                'type': output.get('kind')
                })
        return Response(True, outputs)


    def get_output_file(self,
                        download_dir,
                        size,
                        overwrite,
                        job_id=None,
                        fname=None,
                        url=None):
        """
        Gets the content of a file created in a job.
        Either ``url``, or both ``job_id`` and ``fname`` must be set.
        If all three are set, job_id & fname will be used.

        :Args:
            - download_dir (str): The full path to the directory where the
              output will be downloaded to.
            - size (int): The size in bytes of the file to be downloaded.
              Used for progress reporting.
            - overwrite (bool): Whether to overwrite an existing file if
              present.

        :Kwargs:
            - job_id (str): The ID of the job whose output will be downloaded.
              Default is None.
            - fname (str): The name of the output file to be downloaded.
            - url (str): The url directly to the file to be downloaded.
              Default is None.

        :Returns:
            - :class:`.Response` with the GET response, however this is not
              required if the call was successful.
            - :class:`.Response` with :exc:`AttributeError` if the correct url
              arguments are not supplied.
            - :class:`.Response` with :class:`.RestCallException` if the
              download failed.
        """
        self._log.debug("get_output_file, download_dir={dd}, size={sz}, "
                        "overwrite={ow}, job_id={ji}, fname={fn}, "
                        "url={ur}".format(dd=download_dir,
                                          sz=size,
                                          ow=overwrite,
                                          ji=job_id,
                                          fn=fname,
                                          ur=url))

        name = fname if fname else None

        if job_id and name:
            url = self.url("jobs/{jobid}/outputs/files/{name}")
            url = url.format(jobid=job_id, name=name)

        elif url is None:
            return Response(
                False,
                RestCallException(
                    AttributeError,
                    "Either output url or job id and filename required.",
                    None))

        try:
            get_resp = rest_client.download(self._auth,
                                            url,
                                            self.headers,
                                            download_dir,
                                            size, overwrite,
                                            f_name=name)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, get_resp)

    def props_output_file(self, job_id=None, fname=None, url=None):
        """
        Get the file size of a given task output.
        Used to obtain the size of the requested file, which is returned in
        the response Content Length header. Either ``url``, or both ``job_id``
        and ``fname`` must be set. If all three are set, job_id & fname will
        be used.

        :Kwargs:
            - job_id (str): The ID of the job whose output will be checked.
              Default is None.
            - fname (str): The name of the output file to be downloaded.
            - url (str): The url directly to the file to be checked.
              Default is None.

        :Returns:
            - :class:`.Response` with the requested output size in bytes (int)
              if the call was successful.
            - :class:`.Response` with :exc:`AttributeError` if the correct
              url arguments are not supplied.
            - :class:`.Response` with :class:`.RestCallException` if the
              download failed.
        """
        self._log.debug("props_output_file, job_id={0}, "
                        "fname={1}, url={2}".format(job_id, fname, url))
        if job_id and fname:
            url = self.url("jobs/{jobid}/outputs/files/{name}")
            url = url.format(jobid=job_id, name=fname)

        elif not url:
            return Response(
                False,
                RestCallException(
                    AttributeError,
                    "Either output url or job id and filename required.",
                    None))

        try:
            head_resp = rest_client.head(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, head_resp)

    def list_tasks(self, job_id=None, url=None):
        """
        List the tasks of a job.
        Either ``job_id`` *or* ``url`` must be set. If both are set ``url``
        will be used.

        :Kwargs:
            - job_id (str): ID of of the job to list the tasks for.
              Default is None.
            - url (str): Direct url to the task list of the job
              (supplied by :meth:`.BatchAppsApi.get_job()`)

        :Returns:
            - A :class:`.Response` object containing the list of task
              dictionaries if the call is successfull.
            - A :class:`.Response` object containing the
              :class:`.RestCallException` is the call failed.
        """
        self._log.debug("list_tasks, job_id={0}, url={1}".format(job_id, url))
        if not url and job_id:
            url = self.url("jobs/{jobid}/tasks").format(jobid=job_id)

        elif not url and not job_id:
            return Response(False,
                            RestCallException(
                                AttributeError,
                                "Either job_id or url must get set",
                                None))

        try:
            resp = rest_client.get(self._auth, url, self.headers)

        except  RestCallException as exp:
            return Response(False, exp)

        else:
            if 'tasks' not in resp or not isinstance(resp['tasks'], list):
                return Response(False,
                                RestCallException(
                                    KeyError,
                                    "tasks key not in response message",
                                    resp))

            return Response(True, resp['tasks'])

    def list_task_outputs(self, job_id, task):
        """Lists the output files produced by a task.

        :Args:
            - job_id (str): The ID of the job the task outputs belong to.
            - task (int, str): The ID of the task whose outputs will be listed.

        :Returns:
            - A list of the outputs represented as dictionaries, each with the
              'name' and 'type' of the output as well as a download 'link'.
              Contained in a :class:`.Response`. If the call failed,
              Response will contain the :class:`.RestCallException`.
        """
        self._log.debug("list_task_outputs, job_id={0}, "
                        "task={1}".format(job_id, task))

        url = self.url("jobs/{jobid}/tasks/{taskid}/outputs/files")
        url = url.format(url, jobid=job_id, taskid=task)

        try:
            resp = rest_client.get(self._auth, url, self.headers)

        except  RestCallException as exp:
            return Response(False, exp)

        outputs = []
        if 'outputs' not in resp or not isinstance(resp['outputs'], list):
            return Response(False,
                            RestCallException(
                                KeyError,
                                "outputs key not in response message",
                                resp))

        for output in resp['outputs']:
            outputs.append({
                'name': output.get('name'),
                'link': output.get('link', {'href':None}).get('href'),
                'type': output.get('kind')
                })
        return Response(True, outputs)

    def cancel_task(self, job_id, task):
        """Cancel a running task of a job in progress.

        :Args:
            - job_id (str): The ID of the job whose task will be cancelled.
            - task (int, str): The ID of the task to be cancelled.

        :Returns:
            - A :class:`.Response` object with the POST response, however this
              is not required if the call is successful. The call will only
              be successful if the task can be and is cancelled.
            - If the task is not running (and therefore cannot be cancelled),
              the call will fail and the :class:`.RestCallException` will be
              returned in the :class:`.Response` object.
            - Any other communication failures will also return a
              :class:`.RestCallException`.
        """
        self._log.debug("cancel_task, job_id={0}, task={1}".format(job_id,
                                                                   task))
        url = self.url("jobs/{jobid}/tasks/{taskid}/actions/cancel")
        url = url.format(url, jobid=job_id, taskid=task)

        try:
            resp = rest_client.post(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, resp)

    def list_files(self):
        """
        Lists the users files.
        This refers to files loaded by the user (sometimes referred to as
        assets) as distinct from task or job outputs generated during
        task processing.

        :Returns:
            - A :class:`.Response` object containing a list of files as
              dictionaries, with data:
              ``['id','name','lastModifiedBy','lastModifiedTime','link']``
            - If the call failed or if the response is incomplete/malformed
              a :class:`.Response` object with a :class:`.RestCallException`.
        """
        self._log.debug("list_files, no params")
        url = self.url("files")

        try:
            resp = rest_client.get(self._auth, url, self.headers)

        except  RestCallException as exp:
            return Response(False, exp)

        if 'files' not in resp or not isinstance(resp['files'], list):
            return Response(False,
                            RestCallException(
                                KeyError,
                                "files key not in response message",
                                resp))

        return Response(True, resp['files'])

    def query_files(self, files):
        """
        Queries for user files matching specified criteria.
        This is used to detect whether user's files already exist in the cloud,
        and if they're up-to-date. Any number of files can be queried in a
        single call.

        :Args:
            - files (list, dict, str): The files to query.
              If this is in the form of a single filename, or list of
              filenames, the call will query for user files that match
              that filename. If this is in the form of a dict, or list of
              dicts, the call will query for a more specific match.
              Query dict should have the keys ``{'fileName', 'timestamp'}``
              and optionally ``{'originalPath'}``.

        :Returns:
            - If the query was by filename, a :class:`.Response` containing a
              list of all the files (as dicts) with that name will be
              returned.
            - If the query was by specification, a :class:`.Response`
              containing a list of all the matching files (as dicts) will
              be returned.
            - If the call failed, a :class:`.Response` object containing a
              :class:`.RestCallException` will be returned.
        """
        self._log.debug("query_files, files={0}".format(files))
        url = self.url("files/query/{queryby}")
        operations = {str:'byname', dict:'byspecification'}

        optype = type(files)
        if optype == list and len(files) >= 1:
            optype = type(files[0])
        elif optype == list and len(files) < 1:
            return Response(False,
                            RestCallException(
                                ValueError,
                                "File list empty",
                                ValueError("File list empty")))
        else:
            files = [files]

        if optype not in operations:
            error = ("File query can be done with single "
                     "file name, list of names, or userfile "
                     "spec dict. Not {t}".format(t=type(files)))

            return Response(False, RestCallException(TypeError,
                                                     error,
                                                     TypeError(error)))

        req_type = operations[optype]
        self._log.info("Querying files using {0}".format(req_type))
        url = url.format(queryby=req_type)

        if req_type == 'byspecification':
            message = {"Specifications": files}
        else:
            message = {"Names": files}

        self._log.debug("File query url={0}, message={1}".format(url, message))
        try:
            resp = rest_client.post(self._auth, url, self.headers, message)

        except  RestCallException as exp:
            return Response(False, exp)

        if 'files' not in resp or not isinstance(resp['files'], list):
            return Response(False,
                            RestCallException(
                                KeyError,
                                "files key not in response message",
                                resp))

        return Response(True, resp['files'])


    def query_missing_files(self, files):
        """
        Checks whether user files are present in the cloud.
        As opposed to :meth:`.query_files()`, this call returns the files that
        are **not** present in the cloud.

        :Args:
            - files (dict, list): Either a file specification dictionary, or a
              list of file spec dictionaries.

        :Returns:
            - A :class:`.Response` object containing a list of the files that
              don't yet exist in the cloud. The files are represented as a
              dict with only a 'name' key.
            - If the call failed, a :class:`.Response` object containing
              a :class:`.RestCallException` is returned.
        """
        #TODO: Check whether 'FileHash' is supported.
        self._log.debug("query_missing_files, files={0}".format(files))
        url = self.url("files/query/missing")

        if type(files) == dict:
            files = [files]

        elif not (type(files) == list
                  and len(files) >= 1
                  and type(files[0]) == dict):

            error = ("File query can be done with single userfile "
                     "spec dict, or list of userfile spec dicts. "
                     "Not {t}".format(t=type(files)))
            return Response(False, RestCallException(TypeError, error, None))

        message = {"Specifications": files}
        try:
            resp = rest_client.post(self._auth, url, self.headers, message)

        except  RestCallException as exp:
            return Response(False, exp)

        if 'files' not in resp or not isinstance(resp['files'], list):
            return Response(
                False,
                RestCallException(KeyError,
                                  "files key not in response message",
                                  resp))

        return Response(True, resp['files'])


    def get_file(self, userfile, size, download_dir, overwrite=False):
        """Gets the content of a file previously uploaded by the user.

        :Args:
            - userfile (:class:`.UserFile`): The userfile reference for the
              file to be downloaded. Could be generated from a
              :meth:`.FileManager.list_files()` call or file query.
              Must have url attr.
            - size (int): Size of the file in byte to be downloaded
              (see :meth:`.props_file()`).
            - download_dir (str): The full path to the destination directory.

        :Kwargs:
            - overwrite (bool): Whether to overwrite a destination file if it
              already exists. Default is ``False``.

        :Returns:
            - :class:`.Response` with the GET response, however this is not
              required if the call was successful.
            - :class:`.Response` with :class:`.RestCallException` if the
              download failed.
        """
        #TODO: Nothing uses this yet - maybe build into the FileManager?
        #      Or just UserFile?
        if not isinstance(userfile, UserFile):
            return Response(False, RestCallException(TypeError,
                                                     "Not a valid UserFile",
                                                     None))

        self._log.debug("get_file, file={0}, size={1}, "
                        "download_dir={2}, overwrite={3}".format(userfile,
                                                                 size,
                                                                 download_dir,
                                                                 overwrite))
        url = userfile.url
        self._log.debug("Get file url: {0}".format(url))
        try:
            get_resp = rest_client.download(self._auth,
                                            url,
                                            self.headers,
                                            download_dir,
                                            size,
                                            overwrite=overwrite)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            #TODO: Reconfigure original userfile?
            return Response(True, get_resp)

    def props_file(self, userfile):
        """Gets the properties of a file previously uploaded by the user.

        :Args:
            - userfile (:class:`.UserFile`): The userfile reference for the
              file to be checked. Could be generated from a
              :meth:`.FileManager.list_files()` call or file query.
              Must have url attr.

        :Returns:
            - :class:`.Response` with the requested file size in bytes (int) if
              the call was successful.
            - :class:`.Response` with :class:`.RestCallException` if the
              download failed.
        """
        #TODO: Nothing uses this yet - maybe build into the FileManager?
        #      Or just UserFile?
        if not isinstance(userfile, UserFile):
            return Response(False,
                            RestCallException(TypeError,
                                              "Not a valid UserFile",
                                              None))

        self._log.debug("props_file, file={0}".format(userfile))
        url = userfile.url
        try:
            head_resp = rest_client.head(self._auth, url, self.headers)

        except RestCallException as exp:
            return Response(False, exp)

        else:
            return Response(True, head_resp)

    def send_file(self, userfile):
        """Uploads a user file for use in a job.

        :Args:
            - userfile (:class:`.UserFile`): The userfile reference for the
              file to be uploaded. Must be created from a file that exists
              locally.

        :Returns:
            - :class:`.Response` with the PUT response, however this is not
              required if the call was successful.
            - :class:`.Response` with :class:`.RestCallException` if the
              upload failed of ``userfile`` was invalid.
        """
        #TODO: Get progress feedback working
        if not hasattr(userfile, "create_query_specifier"):
            return Response(
                False,
                RestCallException(TypeError,
                                  "Not a valid UserFile",
                                  None))

        self._log.debug("send_file, file={0}".format(userfile))
        url = self.url("files/{name}")

        try:
            file_spec = userfile.create_query_specifier()
            file_desc = {"OriginalFilePath": file_spec['OriginalPath'],
                         "ContentLength": len(userfile),
                         "ContentType": "application/octet-stream",
                         "LastModifiedTime": file_spec['Timestamp']}

            self._log.debug("File description: {0}".format(file_desc))

            with open(userfile.path, 'rb') as file_data:
                files = {"Filename": file_data}
                put_resp = rest_client.put(self._auth,
                                           url,
                                           self.headers,
                                           userfile,
                                           file_desc,
                                           files)

        except (RestCallException, FileMissingException) as exp:
            return Response(False, exp)

        except EnvironmentError as exp:
            self._log.error("Error reading from file: {0}".format(str(exp)))
            return Response(False, exp)

        else:
            return Response(True, put_resp)
