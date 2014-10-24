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

"""
A sample script showing use of the batch_apps module to cancel a running job.
"""

import getpass
import sys
import webbrowser

from batch_apps import (
    FileManager,
    JobManager,
    Credentials,
    Configuration)

from batch_apps.credentials import AzureOAuth

from batch_apps.exceptions import (
    AuthenticationException,
    RestCallException,
    InvalidConfigException)

LOG_LEVEL = "debug" 

def authentication(mode):
    """
    Authenticates a username against a stored password, if any, otherwise
    requires a password is to be entered.

    :Args:
        - cfg (:class:`.Configuration`): an instance of class Configuration as
          returned by create_config()

    :Returns:
        - a :class:`.Credentials` instance object
    """

    try:
        return AzureOAuth.get_session(config=mode)

    except (AuthenticationException, InvalidConfigException) as e:
        print("Could not get existing session: {0}".format(e))
        
    try:
        auth_url = AzureOAuth.get_authorization_url(config=mode)[0]
        webbrowser.open(auth_url)
        redirect_url = input("Please enter authentication url: ")
        return AzureOAuth.get_authorization_token(redirect_url,
                                                  config=mode,
                                                  state=None)

    except (AuthenticationException, InvalidConfigException) as e:
        print("Failed to get authorization: {0}".format(e))

def logging_mode():
    """
    Sets configuration to chosen log_level using existing
    congifuration setup.
    
    :Returns:
        - a :class:`.Configuration` instance object
    """

    global LOG_LEVEL

    if input("Run in debug mode? (yes/no)")[0].lower() == 'n':
        LOG_LEVEL = "info"

    try:
        return Configuration(log_level=LOG_LEVEL)

    except InvalidConfigException as e:
        print("Invalid Configuration: {0}".format(e))

def retrieve_job(auth, config):
    """
    Get the details of the most recently submitted job of a given name.
    
    :Args:
        - auth (:class:`.Credentials`): instance of the Credentials
          class as returned by authentication()

    :Returns:
        - The first from a list of :class:`.SubmittedJob` objects
        
    """

    job_mgr = JobManager(auth, cfg=config)
    job = input("Which job would you like to cancel? ")

    try:
        job_ref = job_mgr.get_jobs(per_call=1,
                                   name=job if job is not '' else None)

        if len(job_ref) < 1:
            raise ValueError("Found no jobs by that name.")

        return job_ref[0]

    except RestCallException:
        raise

def cancel_job(auth, config):
    """
    Attempts to cancel the selected job and returns True or False depending
    on the success of the operation.
    
    :Args:
        - auth (:class:`.Credentials`): instance of the Credentials class
          as returned by authentication()
        - config (:class:`.Configuration`): instance of the Configuration class
          as returned by logging_mode()
    """

    try:
        job = retrieve_job(auth, config)
        if job.cancel():
            print("Job successfully cancelled")
        else:
            print("Job cannot be cancelled either because the job has "
                  "completed or has been aborted.")

    except (RestCallException, ValueError) as e:
        print("Cancel attempt failed: {0}".format(e))


if __name__ == "__main__":
    mode = logging_mode()
    creds = authentication(mode)
    cancel_job(creds, mode)
