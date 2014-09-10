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
""" Batch Apps Python Client.
"""

import logging
from .log import PickleLog

logging.setLoggerClass(PickleLog)

from .job_manager import JobManager
from .file_manager import FileManager
from .credentials import Credentials, AzureOAuth
from .config import Configuration

__all__ = ["job_manager", "file_manager", "credentials", "config"]


__version__ = "0.1.0"
