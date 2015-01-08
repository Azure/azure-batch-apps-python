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

from batchapps.exceptions import FileDownloadException
from batchapps import utils
from batchapps.pool import PoolSpecifier
from batchapps.utils import Listener
from batchapps.files import (
    UserFile,
    FileCollection)

import multiprocessing
import time
import os
import tempfile
import random
import string
import logging


class JobSubmission(object):
    """
    Description of a new processing request to be sent to the cloud.
    Specifies application to be used, the files required for processing and
    any additional parameters required for the processing.
    It also specifies the requested compute resources to be dedicated to the
    job on submission.

    :Attributes:
        - name (str)
        - required_files (:py:class:`.FileCollection`)
        - source (str)
        - instances (int)
        - pool (:py:class:`.Pool`)
        - params (dict)
    """

    def __init__(self, client, job_name, **job_settings):
        """
        :Args:
            - client (:py:class:`.BatchAppsApi`): A configured and
              authenticated API instance.
            - job_name (str): A name for the new job.

        :Kwargs:
            - job_settings (dict): *Optional* Additional job settings or
              parameters can be added as keyword arguments. These include:

                  - 'params': A string dict of job parameters to add to the
                    submission.
                  - 'files': A :py:class:`.FileCollection` of required files
                    to include with the job.
                  - 'job_file': The name (str) of the file that should be
                    used to start the job. This filename should be
                    included in the above ``files`` collection.
                  - 'instances': The number (int) of instances to allocate
                    to the job on submission.
                  - 'pool': A :py:class:`.Pool` to submit the job to. Default
                    is ``None``, i.e. create an auto-pool.
        """
        if not hasattr(client, 'send_job'):
            raise TypeError(
                "client must be an authenticated BatchAppsApi object.")

        super(JobSubmission, self).__setattr__(
            '_api', client)
        super(JobSubmission, self).__setattr__(
            '_log', logging.getLogger('batch_apps'))

        super(JobSubmission, self).__setattr__(
            'name', str(job_name))
        super(JobSubmission, self).__setattr__(
            'params', job_settings.get('params', self.get_default_params()))
        super(JobSubmission, self).__setattr__(
            'required_files', job_settings.get('files', None))
        super(JobSubmission, self).__setattr__(
            'source', str(job_settings.get('job_file', "")))
        super(JobSubmission, self).__setattr__(
            'instances', int(job_settings.get('instances', 0))) #DEP
        super(JobSubmission, self).__setattr__(
            'pool', job_settings.get('pool', None))

    def __str__(self):
        """Job submission as a string

        Returns:
            - A string of the jobsubmission object as dict
        """
        return str(self.__dict__)

    def __getattr__(self, name):
        """
        Get job attribute, or job parameter.
        This will only be called if :py:class:`.JobSubmission` object does
        not have the requested attribute, in which case the job parameters
        dictionary will be searched for a matching key.

        :Returns:
            - The value (str) of the parameter if it is found.

        :Raises:
            - :py:exc:`AttributeError` if the requested attribute/parameter
              does not exist.
        """
        #TODO: Make all parameters case-insensitive.
        try:
            return super(
                JobSubmission,
                self).__getattribute__('params')[str(name)]

        except KeyError:
            raise AttributeError("'JobSubmission' object has no attribute or "
                                 "parameter: {atr}".format(atr=name))

    def __setattr__(self, name, value):
        """
        Set job attribute if it exists, or add job parameter.
        If the :py:class:`.JobSubmission` object has the named attribute
        this will be set. If no such attribute exists, the key and value will
        be added as a string pair to the job parameters dictionary.

        :Args:
            - name (str): The name of the attribute/parameter to be set.
            - value: The value of the attribute/parameter to set to. If this
              value is added as a parameter, it will be converted to a string
              regardless of its initial type.

        """
        if hasattr(self, name):
            super(JobSubmission, self).__setattr__(name, value)

        else:
            self.params[str(name)] = str(value) #TODO: resolve parameter cases

    def __delattr__(self, name):
        """Clear job attribute or delete parameter if it exists

        :Args:
            - name (str): The name of the attribute/parameter to wipe.

        :Raises:
            - :py:class:`AttributeError` if the :py:class:`.JobSubmission`
              object has no attribute or parameter of that name.
        """
        try:
            super(JobSubmission, self).__delattr__(name)
            return

        except AttributeError:
            pass

        try:
            del self.params[str(name)] # TODO: resolve parameter cases

        except KeyError:
            raise AttributeError("'JobSubmission' object has no attribute or "
                                 "parameter: {atr}".format(atr=name))

    def _filter_params(self):
        """
        Parses job parameters before submission.
        Checks the job submission parameters against the defaults for that
        application, and adds additional parameters where necessary.
        The new dictionary is formatted for the REST client (See
        :py:func:`batchapps.utils.format_dictionary()`).

        :Returns:
            - Updated, formatted, parameters dictionary after cross-referencing
              against defaults.
        """
        default_params = self.get_default_params()
        complete_params = dict(self.get_default_params())
        complete_params.update(self.params)

        return utils.format_dictionary(complete_params)

    def _auto_pool(self, size):
        """
        Create an autopoolspecification reference for use in job
        submission.

        :Returns:
            - A dictionary.
        """
        pool = PoolSpecifier(self._api, target_size=size)

        return {
            'targetDedicated': str(pool.target_size),
            'maxTasksPerTVM': str(pool.max_tasks),
            'communication': pool.communication,
            'certificateReferences': pool.certificates
            }

    def _create_job_message(self):
        """
        Create job message for submitting to the REST API.
        Only used internally on job submission (see :py:meth:.submit()).

        :Returns:
            - Dictionary of the job submission formatted for the REST API.
        """
        #TODO: Final check of source file, add xml settings, allow for user
        #      to set priority, verify all job data is correct format

        if not hasattr(self.required_files, '_get_message'):
            self.add_file_collection()

        if self.pool and hasattr(self.pool, 'id'):
            pool_options = {'poolId': self.pool.id}

        elif self.pool:
            pool_options = {'poolId': str(self.pool)}

        else:
            size = max(int(self.instances), 3)
            pool_options = {'autoPoolSpecification': self._auto_pool(size)}

        job_message = {
            'Name': str(self.name),
            'Type': self._api.jobtype(),
            'RequiredFiles': self.required_files._get_message("submit"),
            'Parameters': list(self._filter_params()),
            'JobFile': str(self.source),
            'Settings': '',
            'Priority': 'Medium'
        }
        job_message.update(pool_options)

        self._log.debug("Job message: {0}".format(job_message))
        return job_message

    def add_file_collection(self, file_collection=None):
        """
        Assign a file collection to the job.
        The userfiles assigned to a job submission will be loaded onto each
        node prior to the job being executed.

        :Kwargs:
            - file_collection (:py:class:`.FileCollection`): If set, this will
              be assigned as the :py:class:`.FileCollection` of the job. If
              not set, a new :py:class:`.FileCollection` will be created.

        :Raises:
            - :py:exc:`TypeError` if a non-:py:class:`.FileCollection` is
              passed in.
        """
        if file_collection is None:
            self._log.info("Assigning empty FileCollection to job")
            self.required_files = FileCollection(self._api)

        elif hasattr(file_collection, 'add'):
            self._log.debug("Assigning FileCollection with {0} "
                            "userfiles to job".format(len(file_collection)))

            self.required_files = file_collection

        else:
            raise TypeError("Can only assign an object of type FileCollection"
                            ", not {type}".format(type=type(file_collection)))

    def get_default_params(self):
        """
        Get default parameters.
        Get the parameters specified in the :class:`.Configuration` for the
        current application.

        :Returns:
            - The parameters as a dictionary of strings.
        """
        return self._api.default_params()

    def add_file(self, userfile):
        """
        Add userfile to required files list.
        If the job does not have an :class:`.FileCollection` already assigned,
        a new one will be created.

        :Args:
            - userfile (:class:`.UserFile`): The userfile to be added to
              the job.
        """
        if self.required_files is None:
            self.required_files = FileCollection(self._api)

        self.required_files.add(userfile)

    def set_job_file(self, jobfile):
        """
        Set file as the source from which the job will be started.
        This will be the file that is executed to started the job.

        :Args:
            - jobfile (:class:`.UserFile`, int): The userfile to be used. This
              can also be the index of a userfile in the collection, or it
              can be an :class:`.UserFile` object.
              If a new :class:`.UserFile` object is passed in, it will also
              be added to the required files collection.

        :Raises:
            - :exc:`ValueError` if ``jobfile`` is not an in-range index,
              or of an invalid type.
        """
        if self.required_files is None:
            raise ValueError("This job has no associated FileCollection.")

        if hasattr(jobfile, "create_query_specifier"):

            if jobfile not in self.required_files:
                self._log.info("Assigned job file not in collection, "
                               "adding to required files")

                self.required_files.add(jobfile)
            self.source = jobfile.name

        elif isinstance(jobfile, int) and jobfile < len(self.required_files):
            self.source = self.required_files[jobfile].name

        else:
            raise ValueError(
                "No job file to match {0} could be found.".format(jobfile))

        self._log.debug(
            "Assigned file: {0} as starting job file".format(self.source))

    def submit(self):
        """Submit the job.

        :Returns:
            - If successful, a dictionary holding the new job's ID and a URL
              to get the job details (See: :meth:`.SubmittedJob.update()`).
              Dictionary has the keys: ``['jobId', 'link']``

              .. warning:: 'jobId' key will be deprecated to be replaced with 'id'.

        :Raises:
            - :class:`.RestCallException` if job submission failed.
        """
        resp = self._api.send_job(self._create_job_message())
        
        if resp.success:
            self._log.info("Job successful submitted with ID: "
                           "{0}".format(resp.result['jobId']))

            return {'jobId':resp.result['jobId'], #DEP
                    'id': resp.result['jobId'],
                    'link': resp.result['link']['href']}

        else:
            raise resp.result

class SubmittedJob(object):
    """
    Representation of a job that has been submitted for processing in
    the cloud. Can be used to track the process of the job and to collect
    it's outputs.

    :Attributes:
        - type (str)
        - name (str)
        - tasks (list of :class:`.Task`)
        - percentage
        - xml_settings (str)
        - status (str)
        - time_submitted
        - time_started
        - time_completed
        - requested_instances
        - number_tasks
        - output_filename (str)
        - output_url (str)
        - thumb_url (str)
        - tasks_url (str)
        - pool_id (str)
    """

    def __init__(self, client, job_id, job_name, job_type, **job_settings):
        """
        :Args:
            - client (:class:`.BatchAppsApi`): A configured and authenticated
              Batch Apps Management API instance.
            - job_id (str): The ID of the job.
            - job_name (str): The name of the job.
            - job_type (str): The job type.

        :Kwargs:
            - job_settings (dict): Additional job submission settings.
              Will vary depending on what stage during processing the job
              is at when the data is collected.
              See :meth:`._format_submission()`
        """
        super(SubmittedJob, self).__setattr__(
            '_api', client)
        super(SubmittedJob, self).__setattr__(
            '_log', logging.getLogger('batch_apps'))

        super(SubmittedJob, self).__setattr__(
            'id', job_id)
        super(SubmittedJob, self).__setattr__(
            'name', job_name)
        super(SubmittedJob, self).__setattr__(
            'type', job_type)
        super(SubmittedJob, self).__setattr__(
            'tasks', [])
        super(SubmittedJob, self).__setattr__(
            'submission', self._format_submission(job_settings))

    def __str__(self):
        """String representation of job.

        :Returns:
            - The dict of the job object.
        """
        return str(self.__dict__)

    def __len__(self):
        """Length of a job.

        :Returns:
            -The number of tasks in the job is available.
             Otherwise 0.
        """
        try:
            return self.number_tasks
        except AttributeError:
            return 0

    def __getattr__(self, name):
        """
        Get job attribute, or job submission value.
        This will only be called if :class:`.SubmittedJob` object does not
        have the requested attribute, in which case the job submission
        dictionary will be searched for a matching key.

        :Returns:
            - The value (str) of the parameter if it is found.

        :Raises:
            - :exc:`AttributeError` if the requested attribute/parameter does
              not exist.
        """
        try:
            return super(
                SubmittedJob,
                self).__getattribute__('submission')[str(name)]

        except KeyError:
            raise AttributeError("'SubmittedJob' object has no attribute or "
                                 "parameter: {atr}".format(atr=name))

    def __setattr__(self, name, value):
        """
        Set job attribute if it exists.
        The submission data cannot be overwritten except through using the
        :meth:`.update()` call to collect updated date from the server.

        :Args:
            - name (str): Name of the attribute to be set.
            - value: Value to set to the attribute.

        :Raises:
            - :exc:`ValueError` if attempts to overwrite submission data.
            - :exc:`AttributeError` if attribute or submission key of that
              name does not exist.
        """

        if name in self.submission:
            raise ValueError("Can't override job submission data: "
                             "{data}".format(data=self.submission[name]))

        else:
            super(SubmittedJob, self).__setattr__(name, value)

    def __delattr__(self, name):
        """
        Prevent clearing of jobs submission data.
        Job submission can only be cleared by deleting the object, or changed
        by using :meth:`.update()` to update the status of the job from
        the server.

        :Args:
            - name (str): Name of the attribute to be cleared.

        :Raises:
            - :exc:`ValueError` if attribute exists, and deleting is not
              allowed.
            - :exc:`AttributeError` if attribute or submission data does
              not exist.
        """
        if hasattr(SubmittedJob, name) or name in self.submission:
            raise ValueError("Can't clear job submission data: "
                             "{data}".format(data=name))

        else:
            raise AttributeError("'SubmittedJob' object has no attribute: "
                                 "{atr}".format(atr=name))

    def _format_submission(self, sub):
        """
        Format the job submission details dict to be more usable.
        The specific data parameters present in submission will vary depending
        on the status of the job. Calling :meth:`.update()` will keep the
        submission data up-to-date as the job progress in the cloud.

        :Args:
            - sub (dict): Submission dictionary retrieved from calling
              :meth:`.update()` or :meth:`.JobManager.get_job()`.

        :Returns:
            - String dictionary. And values not present in ``sub`` are
              set to None.
        """
        #TODO: Format time strings to datetime objects
        formatted = {}
        formatted['percentage'] = sub.get('percentComplete', None)
        formatted['xml_settings'] = sub.get('settings', None)
        formatted['status'] = sub.get('status', 'NotStarted')
        formatted['time_submitted'] = sub.get('submissionTime', None)
        formatted['time_started'] = sub.get('startTime', None)
        formatted['time_completed'] = sub.get('completionTime', None)
        formatted['requested_instances'] = int(sub.get('instanceCount', 0)) #DEP
        formatted['number_tasks'] = int(sub.get('taskCount', 0))
        formatted['output_filename'] = sub.get('outputFileName', None)
        formatted['output_url'] = sub.get('outputLink', {'href':None})['href']
        formatted['thumb_url'] = sub.get('previewLink', {'href':None})['href']
        formatted['tasks_url'] = sub.get('taskListLink', {'href':None})['href']
        formatted['pool_id'] = sub.get('poolId', None)

        self._log.debug("Extracted job submission data: {0}".format(formatted))
        return formatted

    def _get_final_output(self, download_dir, overwrite):
        """Internal method to download jobs final output.

        :Args:
            - download_dir (str): The directory the output file will be
              written to.
            - overwrite (bool): Whether to overwrite the file is it already
              exists.

        :Returns:
            - :class:`.Response` object returned directly from
              :class:`.BatchAppsApi`.
        """
        self._log.info(
            "About to check size of requested output file before downloading")

        output_props = self._api.props_output(url=self.output_url)

        if output_props.success:
            self._log.debug("Successfully retrieved output size data: "
                            "{0}".format(output_props.result))

            size = output_props.result

        else:
            self._log.error("Failed to retrieve output size: "
                            "{0}".format(output_props.result))
            return output_props

        return self._api.get_output(download_dir,
                                    size,
                                    self.output_filename,
                                    overwrite,
                                    url=self.output_url)

    def _get_final_preview(self, download_dir, filename, overwrite):
        """Internal method to download jobs final thumbnail.
        We don't bother to check file size for download feedback, as it's
        assumed to be very small.

        :Args:
            - download_dir (str): The directory the output file will be
              written to.
            - filename (str): The thumbnail filename to use.
            - overwrite (bool): Whether to overwrite the file is it already
              exists.

        :Returns:
            - :class:`.Response` object returned directly from
              :class:`.BatchAppsApi`.
        """
        return self._api.get_output(download_dir,
                                    0,
                                    filename,
                                    overwrite,
                                    url=self.thumb_url)

    def _get_intermediate_output(self, output, download_dir, overwrite):
        """Internal method to download any file from the job output.

        :Args:
            - output (dict): The output specification dictionary as created
              by :meth:`.list_all_outputs()`.
            - download_dir (str): The directory the output file will be
              written to.
            - overwrite (bool): Whether to overwrite the file is it already
              exists.

        :Returns:
            - :class:`.Response` object returned directly from
              :class:`.BatchAppsApi`.
        """
        self._log.info(
            "About to check size of requested output file before downloading")

        output_props = self._api.props_output_file(url=output.get('link'))

        if output_props.success:
            self._log.debug("Successful retrieved output size data: "
                            "{0}".format(output_props.result))

            size = output_props.result

        else:
            self._log.error("Failed to retrieve output size: "
                            "{0}".format(output_props.result))

            return output_props

        return self._api.get_output_file(download_dir,
                                         size,
                                         overwrite,
                                         fname=output.get('name'),
                                         url=output.get('link'))

    def get_tasks(self):
        """
        Get a list of the jobs tasks.
        This will only return those tasks that have been started so far.

        :Returns:
            - A list of :class:`.Task` objects.

        :Raises:
            - :exc:`.RestCallException` if an error occurred during call
              to the service.
        """
        if self.tasks_url:
            resp = self._api.list_tasks(url=self.tasks_url)

        else:
            resp = self._api.list_tasks(job_id=self.id)

        if resp.success:
            self.tasks = [Task(self._api, self.id, **task_def)
                          for task_def in resp.result]

            return self.tasks

        else:
            raise resp.result

    def get_output(self, download_dir, output=None, overwrite=False):
        """
        Download a job output file.
        This could be the jobs final output, or if specified, any intermediate
        output file.

        :Args:
            - download_dir (str): Full path to the directory to download the
              output to.

        :Kwargs:
            - output: An output dictionary (as created by
              :meth:`.list_all_outputs()`). If specified, the specific output
              will be downloaded, otherwise the jobs final output will be
              downloaded.

        :Returns:
            - The full path to the downloaded file (str).

        :Raises:
            - :exc:`.FileDownloadException` if the SubmittedJob has no URL
              to a final output yet. This may be because the job has not yet
              finished, or has not been updated.
            - :exc:`.RestCallException` if an error occurred during the request.
        """
        if output:
            name = output.get('name', "")
            download = self._get_intermediate_output(output,
                                                     download_dir,
                                                     overwrite)

        elif self.output_url and self.output_filename:
            name = self.output_filename
            download = self._get_final_output(download_dir, overwrite)

        else:
            raise FileDownloadException(
                "Job has no reference to an output file, "
                "please update to check if the output is ready")

        if download.success:
            return os.path.join(download_dir, name)

        else:
            raise download.result

    def list_all_outputs(self):
        """
        List all outputs created by the job.
        This includes processed outputs, intermediary outputs and log files.

        :Returns:
            - List of outputs as dictionaries with keys
              ``['name', 'link', 'type']``.

        :Raises:
            - :exc:`.RestCallException` if error occurred during request.
        """
        all_outputs = self._api.list_output_files(self.id)

        if all_outputs.success:
            return all_outputs.result

        else:
            raise all_outputs.result

    def get_thumbnail(self, download_dir=None, filename=None, overwrite=True):
        """
        Download the preview thumbnail for job.
        This thumbnail will only be available if the job has completed.

        :Kwargs:
            - download_dir (str): The full path to the directory to download
              the thumbnail. If not specified, the OS temp directory will
              be used.
            - filename (str): A name to give the thumbnail file. If not
              specified a randomly generated filename will be used.
            - overwrite (bool): Whether an existing file will be overwritten.
              Default is ``True``.

        :Returns:
            - The full path to the downloaded file (str).

        :Raises:
            - :exc:`.FileDownloadException` if the SubmittedJob has no
              reference to a job thumbnail. This could mean that the job
              has not yet completed or the object has not been updated.
            - :exc:`.RestCallException` if an error occurred during the request.
        """
        if not download_dir:
            download_dir = tempfile.gettempdir()

        if not filename:
            rdm = [random.choice(string.hexdigits) for x in range(8)]
            filename = ''.join(rdm) + ".png"

        if self.thumb_url:
            download = self._get_final_preview(download_dir,
                                               filename,
                                               overwrite)

        else:
            raise FileDownloadException(
                "Job has no reference to a thumbnail, "
                "please update to check if the thumbnail is ready")

        if download.success:
            return os.path.join(download_dir, filename)

        else:
            raise download.result

    def get_logs(self, start=None, max_lines=100):
        """Get the system log messages for the job.

        :Kwargs:
            - start (str): The UTC time from which log messages will be
              retrieved. If not set, will retrieve messages from the start
              of the job. Default is ``None``.
            - max_lines (int): The max number of log messages to be retrieved.
              Default is 100.

        :Returns:
            - If successful, a dict in the format:
              ``{'upTo': '', 'messages': {'taskId', 'timestamp', 'text'}}``.
              Where ``'upTo'`` will contain the timestamp of the last log
              message retrieved, and ``'messages'`` will contain a list of
              dictionaries with the details of each log message.
            - If unsuccessful, returns ``None``.
        """

        logs = self._api.get_log(self.id, start, max_lines)

        if logs.success:
            return logs.result

        else:
            self._log.error("Failed to retrieve job logs. Error: "
                            "{0}".format(logs.result.msg))
            return None

    def update(self):
        """
        Update the job object.
        Used to keep the submission data up-to-date as the job progresses
        on the cloud.

        :Returns:
            - ``True`` if the job has been successfully updated.

        :Raises:
            - :exc:`.RestCallException` if an error occurred during the request.
        """
        self._log.debug("About to update job {0}".format(self.id))
        resp = self._api.get_job(self.id)

        if resp.success:
            self.submission = self._format_submission(resp.result)
            return True

        else:
            raise resp.result

    def cancel(self):
        """
        Cancel the job.
        This can only be called if the job is queued or running.

        :Returns:
            - ``True`` if the job is successfully cancelled.
            - ``False`` if the job is unable to be cancelled,
              e.g. it has completed.

        :Raises:
            - :exc:`.RestCallException` if the request failed.
        """
        self._log.debug("About to cancel job {0}".format(self.id))
        resp = self._api.cancel(self.id)

        if resp.success:
            self.update()
            return True

        if resp.result.type is None:
            # Call was successful but job was unable to be cancelled.
            return False

        else:
            raise resp.result

    def reprocess(self):
        """
        Reprocess any failed tasks in a job.

        :Returns:
            - ``True`` if the failed tasks have been successfully re-queued.
            - ``False`` if the job is unable to be re-queued,
              e.g. it has already completed.

        :Raises:
            - :exc:`.RestCallException` if the request failed.
        """
        self._log.debug("About to reprocess job {0}".format(self.id))
        resp = self._api.reprocess(self.id)

        if resp.success:
            return True

        if resp.result.type is None:
            # Call was successful but job was unable to be reprocessed.
            return False

        else:
            raise resp.result

class Task(object):
    """
    Definition for a single job task. Can only exist after a task has been
    launched in the cloud. The data associated with a task will vary depending
    on the status of that task.
    To update a task object, it must be done from the job parent,
    :meth:`.SubmittedJob.get_tasks()`.

    :Attributes:
        - status (str)
        - completion_time (str)
        - instance (str)
        - deployment (str)
        - cores (str)
        - charge_time (str)
        - non_charge_time (str)
        - outputs (list)
    """

    def __init__(self, client, job_id, **props):
        """
        :Args:
            - client (:class:`.BatchAppsApi`): A configured and authenticated
              Batch Apps Management API instance.
            - job_id (str): The ID of the parent job of the task.

        :Kwargs:
            - props (dict): All additional data related the to progress of the
              task. What data is available will depend on the status.
              Data that is not available will be set to ``None``.
        """
        if not hasattr(client, 'get_output_file'):
            raise TypeError(
                'client must be authenticated BatchAppsApi object.')

        self._api = client
        self._job = str(job_id)
        self._log = logging.getLogger('batch_apps')

        self.id = int(props.get('id', 0))
        self.status = props.get('status', None)
        self.completion_time = props.get('completionTime', None)
        self.instance = props.get('instanceId', None)
        self.deployment = props.get('deploymentId', None)
        self.cores = props.get('coreCount', None)
        self.charge_time = props.get('chargeTime', None)
        self.non_charge_time = props.get('nonChargeTime', None)

        self.outputs = []
        raw_outputs = props.get('outputs', [])

        for _output in raw_outputs:
            self.outputs.append({
                'name': _output.get('name'),
                'link': _output.get('link', {'href':None})['href'],
                'type': _output.get('kind')
                })

    def _get_file(self, output, download_dir, overwrite):
        """Internal method to download a task output.

        :Args:
            - output (dict): An output specification such as created
              by :meth:`.list_outputs()`.
            - download_dir (str): The directory the output file will be
              written to.
            - overwrite (bool): Whether to overwrite the file is it already
              exists.

        :Returns:
            - :class:`.Response` object returned directly from
              :class:`.BatchAppsApi`.
        """
        if output.get('type') == 'TaskPreview':
            size = None

        else:
            output_props = self._api.props_output_file(url=output.get('link'))

            if output_props.success:
                size = output_props.result

            else:
                raise output_props.result

        return self._api.get_output_file(download_dir,
                                         size,
                                         overwrite,
                                         fname=output.get('name'),
                                         url=output.get('link'))

    def get_thumbnail(self, download_dir=None, filename=None, overwrite=True):
        """
        Download the preview thumbnail for task.
        This thumbnail will only be available if the task has completed.

        :Kwargs:
            - download_dir (str): The full path to the directory to download
              the thumbnail. If not specified, the OS temp directory will
              be used.
            - filename (str): A name to give the thumbnail file. If not
              specified and one has not been specified by the server, a
              randomly generated filename will be used.
            - overwrite (bool): Whether an existing file will be overwritten.
              Default is ``True``.

        :Returns:
            - The full path to the downloaded file (str).

        :Raises:
            - :exc:`.FileDownloadException` if the Task has no reference to
              a thumbnail. This could mean that the task has not yet
              completed or the object has not been updated.
            - :exc:`.RestCallException` if an error occurred during the request.
        """
        if not download_dir:
            download_dir = tempfile.gettempdir()

        thumbs = [o for o in self.outputs if o['type'] == 'TaskPreview']

        if len(thumbs) < 1:
            raise FileDownloadException(
                "Task has no reference to a thumbnail, "
                "please update tasklist to check if the thumbnail is ready")

        thumb = thumbs.pop()

        if filename:
            thumb['name'] = str(filename)

        elif not 'name' in thumb:
            rdm = [random.choice(string.hexdigits) for x in range(8)]
            thumb['name'] = ''.join(rdm)+".png"


        self._log.info("Found thumbnails in task object: {0}, "
                       "downloading {1}".format(thumbs, thumb))

        download = self._get_file(thumb, download_dir, overwrite)

        if download.success:
            return os.path.join(download_dir, thumb['name'])

        else:
            raise download.result

    def list_outputs(self):
        """
        List all outputs created by the task.
        This includes processed outputs, intermediary outputs and log files.

        :Returns:
            - List of outputs as dictionaries with keys
              ``['name', 'link', 'type']``.

        :Raises:
            - :exc:`.RestCallException` if error occurred during request.
        """
        resp = self._api.list_task_outputs(self._job, self.id)

        if resp.success:
            self.outputs = resp.result
            return self.outputs

        else:
            raise resp.result

    def get_output(self, output, download_dir, overwrite=False):
        """Download a task output file.

        :Args:
            - output: An output dictionary (as created by
              :meth:`.Task.list_outputs()`).
            - download_dir (str): Full path to the directory to download
              the output to.

        :Kwargs:
            - overwrite (bool): Whether to overwrite an existing file.
              Default is ``False``.

        :Returns:
            - The full path to the downloaded file (str).

        :Raises:
            - :exc:`.RestCallException` if an error occurred during the request.
        """
        download = self._get_file(output, download_dir, overwrite)
        if download.success:
            return os.path.join(download_dir, output.get('name', ''))
        else:
            raise download.result

    def cancel(self):
        """
        Cancel the task.
        This can only be called if the task is running.

        :Returns:
            - ``True`` if the task is successfully cancelled.

        :Raises:
            - :exc:`.RestCallException` if the request failed or the task was
              not able to be cancelled.
        """
        resp = self._api.cancel_task(self._job, self.id)

        if resp.success:
            return True

        if resp.result.type is None:
            # Call was successful but task was unable to be cancelled.
            return False

        else:
            raise resp.result
