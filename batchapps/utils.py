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
"""Batch Apps Client Utility Module"""

import re
import urllib
import sys
import traceback

try:
    from urllib.parse import quote as urlquote, unquote as urlunquote
    from urllib.parse import urlsplit

except ImportError:
    from urllib import quote as urlquote, unquote as urlunquote
    from urlparse import urlsplit


import logging
LOG = logging.getLogger('batch_apps')

def parse_date_string(time_string):
    """Format datetime string into an easily comparable and REST happy form.

    :Args:
        - time_string (str): The datetime string to be formatted.

    :Returns:
        The string formatted for use with the REST API (str).
    """
    formatted = ''.join(re.findall('\\d+', time_string)) + "000000"
    LOG.debug("Parsed date string {in_t} to "
              "{out_t}".format(in_t=time_string, out_t=formatted[0:17]))

    return formatted[0:17]

def url_from_filename(filename):
    """
    Format a given filename for use in a URL, version independant.

    :Args:
        - filename (str): The filename to be used in the URL.

    :Returns:
        - The correctly formatted filename (str).
    """
    return urlquote(filename)

def filename_from_url(url, ext):
    """Extract a valid filename from a URL

    :Args:
        - url (str): URL to extract the filename from.
        - ext (str): An additional file extension if necessary.
            May be ``None``.

    :Returns:
        - A valid filename.
    """
    alt = urlsplit(url)
    url_file = alt.path.rpartition('/')[2]
    filename = urlunquote(url_file)

    LOG.debug("Filename {fn} with extension {ex} from url "
              "{ur}".format(fn=filename, ex=ext, ur=url))

    return (filename + ext) if ext else filename

def format_dictionary(dictionary):
    """Format parameter dictionary into a list for REST consumption.

    :Args:
        - dictionary (dict): parameter dict in the format
            {'parameter': 'value}.

    :Returns:
        - REST list in the format
            [ {'Name':'parameter}, {'Value':'value'} ]
    """
    return ({"Name": str(k), "Value": str(v)} for k, v in dictionary.items())

def valid_keys(resp_dict, search_keys):
    '''
    Version independant checking if a list of keys are present in a
    given dictionary.

    :Args:
        - resp_dict (dict): I dictionary from a server response.
        - search_keys (list): A list of keys to verify they are
            present in ``resp_dict``.

    :Returns:
        - ``True`` if all keys present in ``resp_dict`` else ``False``.
    '''
    if not isinstance(resp_dict, dict):
        return False

    try:
        overlap = list(list(resp_dict) & set(search_keys))
        return len(overlap) == len(search_keys)

    except TypeError:
        matching_keys = set(search_keys).intersection(list(resp_dict))
        return len(list(matching_keys)) == len(search_keys)

def get_trace(excep):
    """Retrieve an exception traceback

    :Args:
        - excep (:class:`Exception`): The exception that was thrown.

    :Returns:
        The traceback information (str).
    """
    try:
        trace = traceback.format_exc()
        return trace
    except AttributeError:
        return None


class Listener(object):
    """
    Process wrapper object for starting, stopping and monitoring
    background subprocesses.

    :Attributes:
        - pid (int): The process pid.
        - name (str): The process name.
        - children (list): A list of dependent :class:`.Listener` objects.
    """

    def __init__(self, process, *child):
        """Create new listener.

        :Args:
            - process (:class:`multiprocessing.Process`): The process to be
                wrapped for monitoring
            - child (:class:`.Listener`): And child processes that should be
                stoped before the parent process is stopped.
        """
        self._proc = process
        self.pid = self._proc.pid
        self.name = self._proc.name
        self.children = list(child)

    def working(self):
        """Check if the background process is still running.

        :Returns:
            ``True`` if the process is still running, else ``False``.
        """
        self.pid = self._proc.pid
        return self._proc.is_alive()

    def stop(self):
        """Terminate the background process"""
        self.pid = self._proc.pid

        try:
            for child in self.children:
                child.stop()

            self._proc.terminate()
            self._proc.join()

        except OSError as exc:
            LOG.debug("Interrupted download process: {0}".format(exc))


    def listen(self, timeout=100):
        """Join the background process for a period of time.

        :Kwargs:
            - timeout (int): The number of seconds that the subprocess will
                be monitored. Default is 100 seconds. Is set to ``None``,
                the process will be listened to indefinitely.

        :Raises:
            :class:`ValueError` if an invalid timeout is passed in.
        """
        if not timeout or isinstance(timeout, int):
            self._proc.join(timeout)
        else:
            raise ValueError(
                "Invalid timeout, please set an number of seconds (int)")
