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
A sample script showing use of the batchapps module to construct and submit
an arbitrary job.
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
ASSET_DIR = "C:\\Path\\To\\Assets\\Directory"

# These settings will be specific to a users Batch Apps service.
ENDPOINT = "myservice.batchapps.core.windows.net"
CLIENT_ID = "abcd-1234-efgh-5678"
TENANT = "wxzy-8765-tuv-4321"
ACCOUNT_KEY = "********"

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
        return AzureOAuth.get_unattended_session(config=mode)

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
        raise RuntimeError("Failed to authenticate: {0}".format(e))

def create_config():
    """
    Looks for configuration settings for specified application, otherwise
    creates new configuration, sets chosen log_level.
    
    :Returns:
        - a :class:`.Configuration` instance object
    """

    global LOG_LEVEL

    if input("Run in debug mode? (yes/no)")[0].lower() == 'n':
        LOG_LEVEL = "info"

    try:
        # Look for application in existing config file
        config = Configuration(log_level=LOG_LEVEL, job_type="MyApp")
        print("Config Accepted")
        return config

    except InvalidConfigException:
        print("Valid config not found. Attempting to create new config.")

    try:  
        config = Configuration(log_level=LOG_LEVEL)
        config.aad_config(client_id=CLIENT_ID,
                          endpoint=ENDPOINT,
                          key=ACCOUNT_KEY,
                          tenant=TENANT,
                          unattended=True)

        config.add_jobtype("MyApp")
        config.current_jobtype("MyApp")
        
        # Examples of additional config settings for your job
        config.set("width", "500")
        config.set("height", "500")

        # Set MyApp to be the default job type
        config.set_default_jobtype()

    except InvalidConfigException as e:
         raise RuntimeError("Invalid Configuration: {0}".format(e))

    finally:
        config.save_config()
        return config

def submit_job(auth, config):
    """
    Create a new job submission and send it to the cloud.
    
    :Args:
        - auth :class:`.Credentials`: instance of the Credentials
          class as returned by authentication()
        - config :class:`.Configuration`: instance of the Configuration
          class as returned by create_config()
    """

    asset_mgr = FileManager(auth, cfg=config)
    job_mgr = JobManager(auth, cfg=config)

    # Converts directory contents to a FileCollection
    file_collection = asset_mgr.files_from_dir(ASSET_DIR)

    new_job = job_mgr.create_job("Test Job", files=file_collection)

    # Set various job parameters. The pre-configured parameters for the
    # job type can be found using new_job.get_default_params().

    new_job.instances = 5 # Number of machines to work on the job.
    new_job.start = 1
    new_job.end = 10
    new_job.numFrames = 10
    
    # This sets the file that will be run to start the job.
    # In this case the first file in the FileCollection.
    new_job.set_job_file(file_collection[0])

    # Upload all files needed for the job.
    new_job.required_files.upload(threads=4)

    try:
        submission = new_job.submit()
        print("New job submitted with ID: {0}".format(submission['jobId']))

    except RestCallException as e:
        print("Job failed: {0}".format(e))


if __name__ == "__main__":
    try:
        cfg = create_config()
        creds = authentication(cfg)
        submit_job(creds, cfg)

    except RuntimeError as exp:
        print("Job failed: {0}".format(exp))
