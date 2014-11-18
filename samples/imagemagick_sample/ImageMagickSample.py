#-------------------------------------------------------------------------
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

"""
A sample script showing use of the python batchapps module to construct and
submit a simple ImageMagick job.
"""

import webbrowser
import time
import sys
import os

from batchapps.credentials import AzureOAuth
from batchapps import (
    FileManager,
    JobManager,
    Configuration)

from batchapps.exceptions import (
    AuthenticationException,
    RestCallException,
    InvalidConfigException)

# The length of time to monitor the job. Defualt: 1 hour
TIMEOUT = 3600

# Set to True to download final job output as well as task outputs.
DOWNLOAD_OUTPUT = False

# Specify your data directories here
DOWNLOAD_DIR = "C:\\Path\\To\\Download\\Directory"
ASSET_DIR = "C:\\Path\\To\\Files\\Directory"

# Specify your account info here
# - Copy BatchAppsServiceUrl value from the Batch Apps portal
# - The account ID is specific to your BatchApps account, where you 
#   can also create a new unattended account key.
ENDPOINT = "example.batchapps.core.windows.net"  
ACCOUNT_ID = "ClientID=1234-abcd;TenantID=5678-wxyz"
ACCOUNT_KEY = "********"

def _check_valid_dir(directory):
    """
    Checks directory path is valid and throws a RuntimeError if not.

    :Args:
        - directory (string): path to download or asset directory
    """

    try:

        if os.path.isdir(directory):
            return directory

        else:
            raise RuntimeError("Directory {0} does not "
                               "exist.".format(directory))

    except TypeError as exp:
        raise RuntimeError(exp)

def _download_job_output(job):
    """
    Downloads final job output when job has successfully completed and exits
    program.

    :Args:
        - job (:class:`batchapps.SubmittedJob`): an instance of the current
        SubmittedJob object
    """

    try:
        output = job.get_output(_check_valid_dir(DOWNLOAD_DIR))

        if os.path.isfile(output):
            print("Successfully downloaded job output.")
            return
        else:
            raise RuntimeError("Failed to download job output: "
                               "output returned unexpected value.")

    except RestCallException as exp:
        raise RuntimeError("Failed to download job output: {0}".format(exp))

    except AttributeError as exp:
        raise RuntimeError("Unexpected value passed: {0}".format(exp))

def _download_task_outputs(task, output_list):
    """
    Loops through tasks and downloads outputs that have not already been
    downloaded.

    :Args:
        - task (:class:`batchapps.Task`): the current task object.
        - output_list (list): a list of task outputs as dictionaries.
    """

    for output in output_list:

        try:
            _check_valid_dir(DOWNLOAD_DIR)
            output_name = os.path.join(DOWNLOAD_DIR, output["name"])

            if not os.path.isfile(output_name):
                print("Task {0} has completed. "
                      "Downloading now...".format(output["name"]))

                task.get_output(output, DOWNLOAD_DIR)
                print("Task download successful.")

        except KeyError as exp:
            raise RuntimeError("Failed {0}".format(exp))

def _track_completed_tasks(job):
    """
    Gather and download outputs for tasks that have completed.

    :Args:
        - job (:class:`batchapps.SubmittedJob`): the current submittedJob
          object.

    """

    try:
        tasks_completed = [t for t in job.get_tasks() if t.status == 'Complete']
        print("-------Checking for new tasks to download--------")

        for task in tasks_completed:

            # Check for merge task which has no outputs to download
            if task.id < job.number_tasks:
                
                # Check output type
                outputs = [o for o in task.outputs if o["type"] == "TaskOutput"]
                _download_task_outputs(task, outputs)

    except RestCallException as exp:
        raise RuntimeError("{0}\nRest call failed.".format(exp))

    except (TypeError, AttributeError, KeyError) as exp:
        raise RuntimeError("Failed {0}".format(exp))

def _retrieve_logs(job):
    """
    Retrieves system logs.

    :Args:
        - job (:class:`batchapps.SubmittedJob`): an instance of the current
          SubmittedJob object.
    """

    try:
        logs = job.get_logs()

        if logs and logs["messages"]:
            for statement in logs["messages"]:
                print(statement['text'])

        else:
            raise RuntimeError("No job logs.")

    except RestCallException as exp:
        raise RuntimeError("Failed to retrieve job logs: {0}".format(exp))

    except (TypeError, AttributeError, KeyError) as exp:
        raise RuntimeError("Received unexpected value for logs: {0}".format(exp))

def _check_job_stopped(job):
    """
    Checks job for failure or completion.

    :Args:
        - job (:class:`batchapps.SubmittedJob`): an instance of the current
          SubmittedJob object.

    :Returns:
        - A boolean indicating True if the job completed, or False if still in
          progress.
    :Raises:
        - RuntimeError if the job has failed, or been cancelled.
    """

    failure_list = ['Error',
                    'Cancelled',
                    'OnHold',
                    'Cancelling']

    try:

        if job.status in failure_list:
            print("\n\n-----------Job has stopped.-------------\nJob status: "
                  "{0}\nPrinting sytem logs to console".format(job.status))

            _retrieve_logs(job)
            raise RuntimeError("Job is no longer running.")

        elif job.status == "Complete":
            print("\n\n-------Job successfully completed--------")

            if DOWNLOAD_OUTPUT:
                _download_job_output(job)

            return True

        elif job.status in ['NotStarted', 'InProgress']:
            return False

        else:
            raise RuntimeError("Unexpected status.")

    except AttributeError as exp:
        raise RuntimeError(exp)

def authentication(cfg):
    """
    Attempts to retrieve an existing session otherwise creates a new session.

    :Returns:
        - An instance of the :class:`batchapps.Credentials`.
    """

    try:
        return AzureOAuth.get_unattended_session(config=cfg)

    except (AuthenticationException, InvalidConfigException) as exp:
        print("Unable to authenticate via Unattended Acocunt: {0}".format(exp))

    try:
        return AzureOAuth.get_session(config=cfg)

    except AuthenticationException as exp:
        print("Could not get existing session: {0}".format(exp))

    except InvalidConfigException as exp:
        raise RuntimeError("Failed to authenticate. {0}".format(exp))

    try:
        webbrowser.open(AzureOAuth.get_authorization_url(config=cfg)[0])
        auth_url = input("Please enter authentication url: ")

        return AzureOAuth.get_authorization_token(auth_url,
                                                  config=AzureOAuth.config)

    except (AuthenticationException, InvalidConfigException) as exp:
        raise RuntimeError("Failed to get authorization: {0}".format(exp))

def generate_config():
    """
    Uses a current configuration if possible otherwise creates a new
    configuration for the specified job type.

    :Returns:
        - An instance of the :class:`batchapps.Configuration`.
    """

    try:
        cfg = Configuration(log_level="info", job_type="ImageMagick")
        print("Existing config found.")
        return cfg

    except InvalidConfigException as exp:
        print("Invalid Configuration: {0}\n"
              "Attempting to create new config.".format(exp))

    try:
        cfg = Configuration(log_level="info")

        cfg.aad_config(account=ACCOUNT_ID, key=ACCOUNT_KEY,
		    ENDPOINT=endpoint, unattended=True)

        cfg.add_jobtype("ImageMagick")
        cfg.current_jobtype("ImageMagick")
        cfg.set("width", "500")
        cfg.set("height", "500")
        cfg.set_default_jobtype()

    except InvalidConfigException as exp:
        raise RuntimeError("Invalid Configuration: {0}".format(exp))

    finally:
        cfg.save_config()
        return cfg

def submit_job(configuration, creds, job_manager):
    """
    Create a new job submission and submit it to the cloud.

    :Args:
        - configuration (:class:`batchapps.Configuration`): The generated
          ImageMagick config to apply to the session.
        - creds (:class:`batchapps.Credentials`): The appropriate credentials
          to access the session.

    :Returns:
        - A submission response.
    """

    try:
        asset_mgr = FileManager(creds, cfg=configuration)

        files = asset_mgr.files_from_dir(_check_valid_dir(ASSET_DIR))

        new_job = job_manager.create_job("Image Magic Test", files=files)

        # Setting various job parameters.
        new_job.instances = len(files)           # 1 vm per file for optimal performance
        new_job.set_job_file(files[0])           # This sets the file that will be run to start the job.
        new_job.required_files.upload(threads=4) # Upload all files needed for the job.


        job_submission = new_job.submit()
        print("New job submitted with ID: {0}".format(job_submission['jobId']))
        return job_submission

    except RestCallException as exp:
        raise RuntimeError("Submission failed: {0}".format(exp))

def track_job_progress(job_manager, job_submission):
    """
    Monitors the status of the job.

    :Args:
        - job_manager (:class:`batchapps.JobManager`): a JobManager instance to provide
          access to job manipulation.
        - job_submission (dict): the submission response after
          submit_job() is called holding the new job's ID and a url to get the
          job details.
    """

    try:
        job = job_manager.get_job(jobid=job_submission['jobId'])
        timeout = time.time() + TIMEOUT

        while time.time() < timeout:

            print("Latest updates on job {0} retrieved.".format(job.name))
            print("Status: {0}".format(job.status))
            print("Progress: {0}".format(
                ('0' if not job.percentage else job.percentage)))

            _track_completed_tasks(job)

            if _check_job_stopped(job):
                return # Job complete

            time.sleep(10)
            job.update()

        else:
            raise RuntimeError("Timeout occured.")

    except RestCallException as exp:
        raise RuntimeError("Rest call failed: {0}".format(exp))

    except (TypeError, AttributeError) as exp:
        raise RuntimeError("Error occured: {0}".format(exp))

    except KeyboardInterrupt:
        raise RuntimeError("Monitoring aborted.")

if __name__ == "__main__":

    EXIT_STRING = "Successfully completed"

    try:
        im_config = generate_config()
        im_auth = authentication(im_config)
        im_jobmgr = JobManager(im_auth, cfg=im_config)

        im_submission = submit_job(im_config, im_auth, im_jobmgr)
        track_job_progress(im_jobmgr, im_submission)

    except RuntimeError as exp:
        EXIT_STRING = "{0}\nExiting program...".format(exp)

    except Exception as exp:
        EXIT_STRING = "An unexpected exception occured: {0}".format(exp)

    finally:
        sys.exit(EXIT_STRING)
