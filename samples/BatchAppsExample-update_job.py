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

"""
A sample script showing use of the batchapps module to retrieve updated
job progress.
"""

import getpass
import sys
import webbrowser

from batchapps import (
    FileManager,
    JobManager,
    Credentials,
    Configuration)

from batchapps.credentials import AzureOAuth

from batchapps.exceptions import (
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

def update_job(auth, config):
    """
    Updates the job and returns True or False depending on the success
    of the operation.
    
    :Args:
        - auth (:class:`.Credentials`): instance of the Credentials class as
          returned by authentication()
        - config (:class:`.Configuration`): instance of the Configuration
          class as returned by logging_mode()
    """
    
    job_mgr = JobManager(auth, cfg=config)
    jobid = input("Please enter the job ID: ")

    try:
        job = job_mgr.get_job(jobid=jobid)
        job.update()
        print("Latest updates on job {0} retrieved.\nStatus: {1}\n"
              "Progress: {2}%".format(job.name, job.status, job.percentage))

    except RestCallException as e:
        print("Update failed: {0}".format(e))

if __name__ == "__main__":
    mode = logging_mode()
    creds = authentication(mode)
    update_job(creds, mode)