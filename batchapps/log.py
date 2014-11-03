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

import logging

class PickleLog(logging.getLoggerClass()):
    """PickleLog

    Logging extension to facilitate pickling of the logging streams during
    the launching of subprocesses in the multiprocessing module.
    """

    def __getstate__(self):
        """Serializing state of the logger.

        Removes the stream logging handlers when pickling

        :Returns:
            - The Logger dict with the 'handlers' key removed.
        """
        pick = dict(self.__dict__)
        pick.pop('handlers')
        return pick

    def __setstate__(self, state):
        """De-serialization state of the logger.

        Reinstates the console stream handler, but the not file handler as
        the could create confilcts between subprocesses writing to the same
        file.

        :Args:
            - state (dict): The logger state as resolved from deserilization
              from which the logger will be rebuilt. The 'handlers' key
              will be re-added before setting to the Logger.
        """
        #TODO: Would be nice to fix this.
        state['handlers'] = []

        log_format = logging.Formatter(
            "%(asctime)-15s [%(levelname)s] %(module)s: %(message)s")

        console_logging = logging.StreamHandler()
        console_logging.setFormatter(log_format)

        state['handlers'].append(console_logging)
        self.__dict__ = state
