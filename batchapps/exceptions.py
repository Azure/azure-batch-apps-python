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

from . import utils

import traceback
import logging
LOG = logging.getLogger('batch_apps')

class SessionExpiredException(Exception):
    """
    InvalidGrantError thrown during server call. This is generally interpreted
    to mean the current token has expired and cannot be refreshed. The client
    will need to be re-authenticated. This can be raised during any server call
    and would need to be handled by prompting the user to log in again.

    """
    def __init__(self, *args):
        """
        Log the exception args as ERROR
        """
        LOG.error("SessionExpiredException: {0}".format(*args))
        super(SessionExpiredException, self).__init__(*args)

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

    def __init__(self, exp_type, message, excep, *args, **kwargs):
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
        #TODO: Restructure the way we log these exception, as these can
        #be missed.
        self.type = exp_type
        self.msg = message
        self.root_exception = excep

        if not kwargs.get("silent", False):
            LOG.critical("Exception of type {type} occurred in the client. "
                         "Message: {msg}".format(type=self.type, msg=self.msg))

            if isinstance(excep, Exception):
                LOG.debug("Details: {args}, {trace}".format(
                    args=excep.args,
                    trace=utils.get_trace(excep)))

            elif hasattr(excep, "content"):
                LOG.debug("Details: {resp}".format(
                    resp=excep.content))

            else:
                LOG.debug("Root exception: {0}".format(excep))

        super(RestCallException, self).__init__(message, *args)

    def __str__(self):
        """RestCallException as a string.

        :Returns:
            - The message string.
        """
        return self.msg
