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
"""Batch Apps Python Client Unit Test Suite
"""

import sys
import os

if sys.version_info[:2] < (2, 7, ):
    try:
        import unittest2
        from unittest2 import TestLoader
        from test.test_support import run_unittest

    except ImportError:
        raise ImportError("The BatchApps Python Client test suite requires "
                          "the unittest2 package to run on Python 2.6 and "
                          "below.\nPlease install this package to continue.")
else:
    if sys.version_info[:1] == (2,):
        from test.test_support import run_unittest

    else:
        from test.support import run_unittest

    import unittest
    from unittest import TestLoader

if sys.version_info[:2] >= (3, 3, ):
    from unittest import mock
else:
    try:
        import mock

    except ImportError:
        raise ImportError("The BatchApps Python Client test suite requires "
                          "the mock package to run on Python 3.2 and below.\n"
                          "Please install this package to continue.")

def run_unit_tests():
    """
    Discover all unit test cases located in the test directory and run
    """
    test_dir = os.path.dirname(__file__)
    top_dir = os.path.dirname(os.path.dirname(test_dir))

    test_loader = TestLoader()
    run_unittest(test_loader.discover(test_dir,
                                      pattern="unittest_*.py",
                                      top_level_dir=top_dir))

def run_integration_tests():
    """
    Discover all unit test cases located in the test directory and run
    """
    test_dir = os.path.dirname(__file__)
    top_dir = os.path.dirname(os.path.dirname(test_dir))

    test_loader = TestLoader()
    run_unittest(test_loader.discover(test_dir,
                                      pattern="integrationtest_*.py",
                                      top_level_dir=top_dir))

if __name__ == '__main__':
    run_unit_tests()
