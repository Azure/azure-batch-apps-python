#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------

"""
A sample script showing use of the batch_apps module to upload files
for use in the cloud.
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
ASSET = "C:\\Path\\To\\My\\Asset.png"
ASSET_DIR = "C:\\Path\\To\\Assets\\Directory"

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

def upload_asset(auth, config):
    """
    Checks if a local asset has been uploaded before and if not,
    performs an upload operation on the single asset.
    
    :Args:
        - auth (:class:`.Credentials`): instance of the Credentials class
          as returned by authentication()
        - config (:class:`.Configuration`): instance of the Configuration
          class as returned by logging_mode()
    """
    
    asset_mgr = FileManager(auth, cfg=config)
    asset_to_upload = asset_mgr.create_file(ASSET)

    if asset_to_upload.is_uploaded():
        print("{0} already uploaded.".format(asset_to_upload))
        return

    else:
        conf = "{0} MBs to be uploaded. Continue? (yes/no) ".format(
            len(asset_to_upload)/1024/1024)

        if input(conf)[0].lower() == 'y':
            try:
                asset_to_upload.upload()
                print("{0} uploaded successfully.".format(asset_to_upload))

            except Exception as e:
                print("Upload failed: {0}".format(e))

        else:
            print("Upload aborted.")
            return

def upload_assets(auth, config):
    """
    Uploads a specified collection of assets either from a set created
    from scratch, or from the contents of existing directory.
    
    :Args:
        - auth (:class:`.Credentials`): instance of the Credentials class
          as returned by authentication()
        - config (:class:`.Configuration`): instance of the Configuration
          class as returned by logging_mode()
    """
    asset_mgr = FileManager(auth, cfg=config)
    asset_to_add = asset_mgr.create_file(ASSET)

    # Creates FileCollection object
    asset_set = asset_mgr.create_file_set(asset_to_add)

    # Extends a FileCollection object with another FileCollection
    asset_set.extend(asset_mgr.files_from_dir(ASSET_DIR))

    try:
        # force=true uploads the assets in the asset collection regardless of
        # whether they have been uploaded before.
        asset_set.upload(force=True)
        print("Assets uploaded successfully.")

    except RestCallException as e:
        print("failed: {0}".format(e))

if __name__ == "__main__":
    mode = logging_mode()
    creds = authentication(mode)

    # Upload a single file
    upload_asset(creds, mode)

    # Upload a collection of files
    upload_assets(creds, mode)
