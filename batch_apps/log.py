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
