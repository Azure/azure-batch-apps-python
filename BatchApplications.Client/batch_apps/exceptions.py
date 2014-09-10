#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------

from . import utils

import logging
LOG = logging.getLogger('batch_apps')

class AuthenticationException(Exception):
    """
    Error relating to missing or invalid credentials.
    """
    def __init__(self, *args):
        """
        Log the exception args as ERROR
        """
        LOG.error("AuthenticationException: {0}".format(*args))
        super(AuthenticationException, self).__init__(*args)

class InvalidConfigException(Exception):
    """
    Error thrown by an incorrect/incomplete config file.
    """
    def __init__(self, *args):
        """
        Log the exception args as ERROR
        """
        LOG.error("InvalidConfigException: {0}".format(*args))
        super(InvalidConfigException, self).__init__(*args)

class FileDownloadException(Exception):
    """
    Error thrown during downloading outputs or files.
    """
    def __init__(self, *args):
        """
        Log the exception args as ERROR
        """
        LOG.error("FileDownloadException: {0}".format(*args))
        super(FileDownloadException, self).__init__(*args)

class FileMissingException(Exception):
    """
    Error occured during userfile creation and gathering where file does not
    exist locally.
    """
    def __init__(self, *args):
        """
        Log the exception args as ERROR
        """
        LOG.error("FileMissingException: {0}".format(*args))
        super(FileMissingException, self).__init__(*args)

class FileInvalidException(Exception):
    """
    Error occurred during the manipulation of a userfile.
    """
    def __init__(self, *args):
        """
        Log the exception args as ERROR
        """
        LOG.error("FileInvalidException: {0}".format(*args))
        super(FileInvalidException, self).__init__(*args)

class RestCallException(Exception):
    """
    Gather all exceptions thrown by the rest_client and during REST
    call preparation and interpretation in :class:`.BatchAppsApi`.
    """

    def __init__(self, exp_type, message, excep, silent=False):
        """
        Will mostly be used to wrap an exception thrown during a REST call,
        then returned to the user as the ``result`` of a :class:`.Response`
        object.

        Log the exception args as CRITICAL

        :Args:
            - exp_type (type): The type of the root exception thrown.
            - message (str): The human readable text associated with the
                error to be reported to the user.
            - excep (Exception, etc): The root exception object, for further
                inspection if required by the user. This may not always be
                set, or may contain a REST response object if a call failed
                but no exception was thrown
                (See: :func:`.rest_client._call()`).

        :Kwargs:
            - silent (bool): If ``True``, the error will not be logged.
                Default is ``False``.
        """
        self.type = exp_type
        self.msg = message
        self.root_exception = excep

        if not silent:
            LOG.critical("Exception of type {type} occurred in the client. "
                         "Message: {msg}".format(type=self.type, msg=self.msg))

            if isinstance(excep, Exception):
                LOG.debug("Root exception details: {args}, {trace}".format(
                    args=excep.args,
                    trace=utils.get_trace(excep)))

            elif hasattr(excep, "content"):
                LOG.debug("Root exception details: {resp}".format(
                    resp=excep.content))

            else:
                LOG.debug("Root exception: {0}".format(excep))
        super(RestCallException, self).__init__(message)

    def __str__(self):
        """RestCallException as a string.

        Returns:
            The message string.
        """
        return self.msg
