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
        return

    print("Building package...")

    package_dir = os.path.abspath("build")
    if not os.path.isdir(package_dir):
        try:
            os.mkdir(package_dir)
        except:
            print("Cannot create build dir at path: {0}".format(package_dir))
            return

    if sys.version_info[:2] < (2, 7,):
        result = subprocess.call([python_exe,
                                  "setup.py",
                                  "sdist",
                                  "--formats=zip"])
        if result != 0:
            print("Failed to build distribution package: Non-zero exit code.")
            return

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
                print("Failed to build distribution package: Non-zero exit code.")
                return

            build_dir = os.path.abspath("dist")
            build_file = os.listdir(build_dir)[0]

            shutil.move(os.path.join(build_dir, build_file),
                        os.path.join(package_dir, build_file))

            shutil.rmtree(build_dir)

if __name__ == '__main__':
    main()
