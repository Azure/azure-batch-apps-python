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
"""Create PyPI Package"""

import sys
import os
import subprocess
import shutil

def main():
    """Build Py Module documentation and Pip package"""

    python_exe = os.path.join(sys.prefix, "python.exe")
    if not os.path.exists(python_exe):
        print("Cannot find python.exe at path: {0}".format(python_exe))

    print("Building package...")

    package_dir = os.path.abspath("build")
    if not os.path.isdir(package_dir):
        os.mkdir(package_dir)

    if sys.version_info[:2] < (2, 7,):
        result = subprocess.call([python_exe,
                                  "setup.py",
                                  "sdist",
                                  "--formats=zip"])
        if result != 0:
            raise RuntimeError("Failed to build distribution package")

        build_dir = os.path.abspath("dist")
        build_file = os.listdir(build_dir)[0]

        shutil.move(os.path.join(build_dir, build_file),
                    os.path.join(package_dir, build_file))

        shutil.rmtree(build_dir)

    else:
        for frmt in ["gztar", "zip"]:
            result = subprocess.call([python_exe,
                                      "setup.py",
                                      "sdist",
                                      "--formats={0}".format(frmt)])

            if result != 0:
                raise RuntimeError("Failed to build distribution package")

            build_dir = os.path.abspath("dist")
            build_file = os.listdir(build_dir)[0]

            shutil.move(os.path.join(build_dir, build_file),
                        os.path.join(package_dir, build_file))

            shutil.rmtree(build_dir)

if __name__ == '__main__':
    main()
