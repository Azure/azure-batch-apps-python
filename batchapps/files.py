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
import hashlib
import multiprocessing
import pickle

from os import path
from datetime import datetime

from . import utils
from .exceptions import (
    FileMissingException,
    FileInvalidException,
    RestCallException)

def upload_wrapper(arg, **kwargs):
    '''
    Wrapper to pull upload method from self to avoid multiprocessing
    errors in Python 2.6.
    '''
    return FileCollection._upload_forced(*arg, **kwargs)


class FileCollection(object):
    """
    A set of userfiles which can be applied to a job.
    Behaves like a ``list``.
    """

    def __init__(self, client, *files):
        """
        :Args:
            - client (:class:`.BatchAppsApi`): An authorized Batch Apps
              Management API REST client.
            - files (:class:`UserFile`, list): *Optional*. Any files to be
              included in the collection. Can be individual
              :class:`UserFile` objects or a list of them.
        """
        if not hasattr(client, 'query_files'):
            raise TypeError(
                "client must be an authenticated BatchAppsApi object.")

        self._api = client
        self._collection = []
        self._log = logging.getLogger('batch_apps')

        for _file in files:
            self.add(_file)

    def __str__(self):
        """String representation of FileCollection

        :Returns:
            - A string containing a list of filenames
        """
        return str([str(a) for a in self._collection])

    def __len__(self):
        """Length of FileCollection

        :Returns:
            - Number of files in the collection.
              I.e. Length of internal list _collection
              Example usage:
                  >> if len(my_asset_collection) == 0: print("Empty")
        """
        return len(self._collection)

    def __iter__(self):
        """Get FileCollection iterator

        :Returns:
            - Iterator for internal list _collection.
              Example usage:
                  >> for _file in FileCollection(my_list): print(_file.name)
        """
        return iter(self._collection)

    def __getitem__(self, filekey):
        """FileCollection subscript - get userfile from collection via index

        :Args:
            - filekey (int, str, slice): Index of a specific userfile in the
              collection. This can be an integer index, a slice index or the
              name of a particular file.

        :Returns:
            - If a string name is passed in, the output will be a list of
              :class:`.UserFile` objects, as multplie files may have the same
              name. Likewise, passing in a slice will produce a list of
              :class:`.UserFile`. Passing an int index will return a single
              :class:`.UserFile`
              Example usage:
                  >> print(my_collection[5])
                  "texture.tif"
                  >> print(my_collection["star.png"])
                  "['star.png']"
                  >> print(my_collection[5:-3])
                  "['texture.tif', 'star.png']"

        :Raises:
            - FileMissingException: UserFile is not found or index is out
              of range.
        """
        if isinstance(filekey, int) and filekey < len(self):
            return self._collection[filekey]

        elif isinstance(filekey, slice):
            return self._collection[filekey]

        elif filekey in [a.name for a in self._collection]:
            return [a for a in self._collection if a.name == filekey]

        else:
            raise FileMissingException(
                "Requested file is not in the collection")

    def __setitem__(self, filekey, fileval):
        """Restrict setting userfiles in collection via index/subscript

        :Args:
            - filekey: Ignored

        :Raises:
            - TypeError - an FileCollection subscript cannot be assigned to
        """
        raise TypeError("Collection subscript cannot be assigned to")

    def __delitem__(self, filekey):
        """
        Delete userfile from collection, by name or index.

        :Args:
            - filekey (int, str): It an integer, will delete the userfile in
              the collection at that index. Otherwise if it's a string, all
              files in the collection with that name will be deleted.

              If the name is not found, or the index out of range,
              nothing will happen.
        """
        if isinstance(filekey, int) and filekey < len(self):
            del self._collection[filekey]

        if isinstance(filekey, slice):
            del self._collection[filekey]

        elif isinstance(filekey, str):
            self._collection = [a for a in self._collection
                                if a.name != filekey]

    def _upload_forced(self, userfile):
        """Upload a single file in the collection, ignoring overwrite.
        Only used internally in :func:upload by the parallel subprocesses

        :Args:
            - userfile (:class:`.UserFile`): The file from the collection
              to be uploaded

        :Returns:
            - A tuple containing the result of the :func:`UserFile.upload` call,
              and the original userfile:
              ``(bool success, userfile, string result)``
        """
        self._log.debug("About to upload file: {0}".format(userfile))
        resp = userfile.upload(force=True)

        # TODO: Need to fix hanging when we try to return the result
        # object rather than just a string.
        # self._log.critical(str(resp.result))

        return (resp.success, userfile, str(resp.result))

    def _get_message(self, operation):
        """Generate file specifier list for REST API

        :Returns:
            - A list of the file specifier messages for each :class:`.UserFile`
              in the collection, formatted for use for the REST API client.
        """
        filespecs = []
        for _file in self._collection:

            if operation is "query":
                filespecs.append(_file.create_query_specifier())

            elif operation is "submit":
                filespecs.append(_file.create_submit_specifier())

        return filespecs

    def _remove_duplicates(self, rm_list):
        """Custom duplicate removal for UserFile objects, as
        using set() does not work correctly.

        :Args:
            -rm_list (list): The list that will have duplicates removed.

        :Returns:
            - The cleaned up list.
        """
        cleaned = []
        for i in rm_list:
            if i not in cleaned:
                cleaned.append(i)
        return cleaned

    def add(self, userfile):
        """Add a userfile to the collection.

        :Args:
            - userfile (:class:`.UserFile`, list): File to be added to the
              collection. Must be unique or FileInvalidException will be
              raised. ``userfile`` can also be a list, all non-unique and
              non-:class:`.UserFile` objects will be removed with a warning
              before the list is added to the collection.

        :Raises:
            - :class:`.FileInvalidException` if called with a non:class:`.UserFile` object
              or the file is already in the collection.
        """
        if isinstance(userfile, UserFile) and userfile not in self._collection:
            self._log.debug("Adding UserFile object to collection: "
                            "{0}".format(userfile))
            self._collection.append(userfile)

        elif isinstance(userfile, list):
            self._log.debug("Adding list object to collection")

            file_list = [a for a in self._remove_duplicates(userfile)
                         if isinstance(a, UserFile)
                         and a not in self._collection]

            if set(file_list) != set(userfile):
                self._log.warning(
                    "Some invalid or duplicated userfiles removed from list")

            self._collection.extend(file_list)

        else:
            raise FileInvalidException(
                "Only unique UserFile objects can be added to collection, "
                "not {type}".format(type=type(userfile)))

    def extend(self, file_collection):
        """Extend a file collection by merging two together

        :Args:
            - file_collection (:class:`.FileCollection`): A file collection to
              be merged into the current collection. Any duplicate userfiles
              will be removed.

        :Raises:
            - AttributeError if ``file_collection`` is not a
              :class:`.FileCollection`
        """
        if isinstance(file_collection, FileCollection):
            self._log.debug(
                "Extending file collection with: {0}".format(file_collection))

            self._collection.extend(file_collection._collection)
            self._collection = self._remove_duplicates(self._collection)

        else:
            msg = ("FileCollection can only be "
                   "extended by another FileCollection")
            self._log.error(msg)
            raise AttributeError(msg)

    def remove(self, userfile):
        """
        Remove a userfile from the collection, via index or name.

        :Args:
            - userfile (str, int, :class:`.UserFile`, list, slice): The name,
              object or index of the file to be removed. If a name is passed
              in, only the first occurance of that name will be removed. To
              remove all occurances, use :meth:`.__delitem__()`.
              A :class:`.UserFile` object can also be passed in or a list
              of any of the above.

        :Raises:
            - TypeError if ``userfile`` is not a :class:`.UserFile`, int, str,
              slice or list thereof.
        """
        if isinstance(userfile, int) and userfile < len(self):
            self._log.debug("Removing userfile {0} from index: "
                            "{1}".format(self._collection[userfile], userfile))

            del self._collection[userfile]

        elif isinstance(userfile, UserFile):
            self._log.debug("Removing userfile object {0}".format(userfile))
            self._collection.remove(userfile)

        elif isinstance(userfile, list):
            self._log.debug("Removing list of files: {0}".format(
                ', '.join([str(a) for a in userfile])))

            for rem in userfile:
                self.remove(rem)

        elif isinstance(userfile, slice):
            self._log.debug("Removing files from indices: "
                            "{0}".format(userfile))

            del self._collection[userfile]

        elif isinstance(userfile, str):
            self._log.debug("Removing first userfile with name: "
                            "{0}".format(userfile))

            if len(self[userfile]) > 0:
                self._collection.remove(self[userfile].pop())

        else:
            raise TypeError("File to remove must be userfile object, "
                            "filename string, userfile index int or slice")

    def upload(self, force=False, threads=None):
        """Upload all files in a set, optionally in parallel

        :Kwargs:
            - force (bool): Whether the client will only upload if the file
              has not be previously uploaded. Default is ``False``,
              i.e. always check and if file has been uploaded, don't
              re-uplod. Set to ``True`` to upload regardless.
            - threads (int): number of parallel uploads, default is 1
              (i.e. not parallel). Max threads is 10.

        :Returns:
            - A list of tuples containing any files that failed to upload and
              the exception information. In the format:
              ``[(UserFile(), ExceptionStr), (UserFile(), ExceptionStr)..]``
              If all files successfully uploaded this list will be empty.

        :: warning ::
            During parallel uploads, messages will only be logged to the
            console, not to file.
        """
        if not force:
            self._log.info(
                "Checking to see if files in collection exist in the cloud")

            file_set = self.is_uploaded()

        else:
            self._log.debug("Uploading files regardless of whether "
                            "they've been uploaded before")

            file_set = self

        if threads:
            threads = min(threads, 10)
        failed = []

        if not threads or threads < 1: # No subprocessed uploads
            for _file in file_set:
                result, userfile, error = self._upload_forced(_file)
                if not result:
                    failed.append((userfile, error))

        else:
            try:
                parallel_uploads = multiprocessing.Pool(threads)
                self._log.debug("Created a pool for {0} parallel file "
                                "uploads".format(threads))

                for subset in range(0, len(file_set), threads):

                    fstr = ', '.join([str(a)
                                      for a in file_set[subset:subset+threads]])
                    self._log.debug(
                        "Creating thread to upload: {0}".format(fstr))

                    selected_files = file_set[subset:subset+threads]
                    zipped = zip([self]*len(selected_files), selected_files)
                    pickle.dumps(zipped)

                    processes = parallel_uploads.map_async(upload_wrapper,
                                                           zipped)
                    results = processes.get()
                    for res in results:
                        if not res[0]:
                            failed.append((res[1], res[2]))

            except Exception as exp:
                self._log.exception(
                    "Exception in parallel uploads: {0}".format(exp))

                return [(f, str(exp)) for f in file_set._collection]

        return failed

    def is_uploaded(self, per_call=50):
        """Check if all files in set have already been uploaded

        :Kwargs:
            - per_call (int): Number of files to check against the server
              at a time. The more per call, the slower the call and the
              bigger the return object, but too few per call could mean a
              large number of calls for a big file collection. Default is 50.

        :Returns:
            - An :class:`FileCollection` containing the files that have yet
              to be uploaded.

        :Raises:
            - :class:`.RestCallException`. If an exception has been thrown be the REST
              client, it will be raised here.
        """
        file_set = FileCollection(self._api, *list(self._collection))
        collection_spec = self._get_message("query")

        self._log.debug(
            "File collection specification: {0}".format(collection_spec))

        for i in range(0, len(self), per_call):
            self._log.info("Checking {0} files for prior uploads".format(
                len(collection_spec[i:i+per_call])))

            resp = self._api.query_files(collection_spec[i:i+per_call])
            if not resp.success:
                raise resp.result

            resp_files = [UserFile(self._api, r_file)
                          for r_file in resp.result]
            self._log.info(
                "{0} of {1} files have already been "
                "uploaded".format(len(resp_files),
                                  len(collection_spec[i:i+per_call])))

            # Check for matching uploaded userfiles in server response.
            # TODO: Set up path or md5 comparison
            for r_file in resp_files:
                to_remove = [_file for _file in file_set
                             if (_file.name == r_file.name)
                             and (_file.compare_lastmodified(r_file))]

                # Remove any matches from the list of files to be uplaoded.
                file_set.remove(to_remove)

        self._log.debug(
            "Files that still need to be uploaded: {0}".format(file_set))

        return file_set


class UserFile(object):
    """
    Definition of a single file to be used during the running of a
    particular job.

    :Attributes:
        - name (str)
        - path (str)
        - url (str)
        - tag (str)
    """

    def __init__(self, client, file_def):
        """
        :Args:
            - client (:class:`BatchAppsApi`): Authenticated and configured
              REST API client.
            - file_def (str, dict): Defining information on the file. To create
              a userfile of a local file, this will be a string of the full
              path to the file. To represent a userfile that exists in the
              cloud, this will be a dictionary containing the path, name,
              last modified date, and URL to the file.
        """
        if not hasattr(client, 'send_file'):
            raise TypeError(
                "client must be an authenticated BatchAppsApi object.")

        self._api = client
        self._log = logging.getLogger('batch_apps')

        if isinstance(file_def, str):
            self.name = path.basename(file_def)
            self.path = path.normpath(file_def)
            self.url = ""
            self.tag = ""

            self._exists = self._verify_path()
            self._last_modified = self.get_last_modified()
            self._checksum = self.get_checksum()

        elif isinstance(file_def, dict):
            self.name = file_def.get('name', "Unknown")
            self.path = file_def.get('originalFilePath', "")
            self.url = file_def.get('link', {}).get('href', "")
            self.tag = ""

            self._exists = False
            self._last_modified = file_def.get('lastModifiedTime', "")
            self._checksum = ""
        else:
            raise TypeError("file_def must be str or dict.")

    def __bool__(self):
        """Bool representation of an :class:`.UserFile`

        Defined by whether the file exists at it's referenced path.
        Example usage::
            >> if not UserFile("texture.png"): print("Can't find texture file")
        """
        return self._exists

    def __len__(self):
        """Determine userfile length as the size of the file in bytes.

        :Returns:
            - Size of the file in bytes (int)
              If the file doesn't exist, return 0.
        """
        if self._exists:
            return path.getsize(self.path)
        else:
            return 0

    def __eq__(self, compare_to):
        """
        :class:`.UserFile` comparison.
        If both files exist locally, the comparison will be with names and
        md5 checksums. If one or both of the files only exist in the cloud,
        the comparison will be of full paths.

        :Args:
            - compare_to (:class:`.UserFile`): The userfile to compare the
              current userfile to.

        :Returns:
            - ``True`` if the two files are equal, else ``False``.

        Example usage:
            >> if assset_a == asset_b: print("Duplicate files!")
        """
        #TODO: When server supports md5, have all checking done based on this.
        if isinstance(compare_to, UserFile):

            if compare_to._exists and self._exists:
                return ((compare_to._checksum == self._checksum)
                        and (compare_to.name == self.name))

            return compare_to.path == self.path

        return False

    def __lt__(self, compare_to):
        """
        UserFile ordering (less-than).
        Order of a sorted file list is done alphabetically based on the
        filename.

        :Args:
            - compare_to (:class:`.UserFile`): The userfile to sort the current
              userfile against.

        :Returns:
            - ``True`` if current userfile is "less than" passed in userfile,
              else ``False``.

        Example usage:
            >> print(sorted(my_asset_collection))
            "['a.png', 'b.jpg', 'c.tif']"
        """
        return self.name < compare_to.name

    def __str__(self):
        """String representation of :class:`.UserFile`.

        :Returns:
            - The filename of the UserFile (string).
        """
        return self.name

    def __hash__(self):
        """:class:`.UserFile` hashing behaviour

        :Returns:
            - If file exists locally, hash of the file checksum.
            - If the file is in the cloud, hash of the full path.
        """
        #TODO: Once server supports md5, only hash this.
        if self._exists:
            return hash(self._checksum)

        else:
            return hash(self.path)

    def _verify_path(self):
        """Verify existance of new userfile reference.

        :Returns:
            - ``True`` if file exists at the given path, else ``False``.
        """
        if not path.isfile(self.path):
            self._log.warning(
                "Unable to verify existance of new file: %s", self.path)

            return False

        return True

    def _get_windows_path(self):
        """Format the file path for use on Windows OS (Azure).

        :Returns:
            - Modified path with forward slashes replaced. No changes are
              made to the root or structure of the path.
        """
        return self.path.replace('/', '\\')

    def get_last_modified(self):
        """Get the last modified datetime stamp formatted for the REST API.

        :Returns:
            - If the file exists locally, the last modified
              timestamp (string).
            - If the file doesn't exist locally, an empty string.
        """

        if not self._exists:
            self._log.debug("Can't get last modified time for unverified file")
            return ""

        mod_time = datetime.utcfromtimestamp(path.getmtime(self.path))
        return mod_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    def compare_lastmodified(self, compare_to):
        """Compare files based on their last modified date.

        :Args:
            - compare_to (:class:`.UserFile`): UserFile to compare to
              current userfile.

        :Returns:
            - ``True`` if the files were last modified at the same time,
              else ``False``.
            - Returns ``False`` if either of the UserFiles don't exist locally.
        """

        self._last_modified = self.get_last_modified()
        if not self._last_modified:
            return False
        # It looks like the way date time stamps are returned has changed...
        #file1 = utils.parse_date_string(self._last_modified)
        #file2 = utils.parse_date_string(compare_to._last_modified)
        #return file1 == file2

        return self._last_modified == compare_to._last_modified


    def get_checksum(self):
        """Generate md5 checksum for file.

        :Returns:
            - If the file exists locally, the md5 checksum of the file (bytes).
            - If the file doesn't exist locally, an empty string.
        """

        if not self._exists:
            self._log.debug("Can't get checksum for unverified file")
            return ''

        block_size = 128
        hasher = hashlib.md5()

        try:
            with open(self.path, 'rb') as user_file:
                while True:
                    file_block = user_file.read(block_size)
                    if not file_block:
                        break
                    hasher.update(file_block)
            return hasher.digest()

        except (TypeError, EnvironmentError) as exp:
            self._log.debug("Can't get checksum: {0}".format(exp))
            return ''

    def create_query_specifier(self):
        """Create the file specifier for REST API communications

        :Returns:
            - Dictionary of the file specification.
              Format: ``{'FileName':'', 'Timestamp':'', 'OriginalPath':''}``

        :Raises:
            - :class:`.FileMissingException` if the file of which the specifier
              is requested does not exist locally.
        """
        if not self._exists:
            raise FileMissingException("File is not found to exist at path: "
                                       "{p}".format(p=self.path))

        file_spec = {
            'FileName': self.name,
            'Timestamp': self._last_modified,
            'OriginalPath': self._get_windows_path()
        }

        self._log.debug("File specification: {0}".format(file_spec))
        return file_spec

    def create_submit_specifier(self):
        """Create the file specifier for REST API communications.

        :Returns:
            - Dictionary of the file specification.
              Format: ``{'Name':'', 'Timestamp':''}``

        :Raises:
            - :class:`.FileMissingException` if the file of which the specifier
              is requested does not exist locally.
        """
        if not self._exists:
            raise FileMissingException("File is not found to exist at path: "
                                       "{p}".format(p=self.path))

        file_spec = {
            'Name': self.name,
            'Timestamp': self._last_modified,
        }

        self._log.debug("File specification: {0}".format(file_spec))
        return file_spec

    def upload(self, force=False):
        """Upload file.

        :Kwargs:
            - force (bool): If ``True``, uploads regardless of whether the
              file has already been uploaded. Else, checks if file has been
              uploaded, and if so, skips.

        :Returns:
            - Client :class:`.Response` object if upload was attempted.
            - ``None`` if upload was skipped.
        """
        uploaded = False

        if not force:
            self._log.info("Checking if file {0} has been previously "
                           "uploaded".format(self.name))

            uploaded = self.is_uploaded()
            self._log.info("Uploaded: {0}".format(uploaded))

        if force or uploaded is None:
            self._log.info("Uploading file {0}".format(self.name))
            return self._api.send_file(self)

        return None

    def is_uploaded(self):
        """Check if a file has already been uploaded.

        :Returns:
            - :class:.`.UserFile` if file has already been uploaded, else ``None``.

        :Raises:
            - :class:`.RestCallException` if any errors occured in the API
              client.
        """
        resp = self._api.query_files(self.create_query_specifier())
        if resp.success:

            resp_files = [UserFile(self._api, r_file)
                          for r_file in resp.result]

            for r_file in resp_files: #TODO: Set up path or md5 comparison

                if (self.name == r_file.name
                    and self.compare_lastmodified(r_file)):
                    return r_file

            return None

        else:
            raise resp.result

    def download(self, download_dir):
        """Download file.
        
        :Args:
            - download_dir (str): Path to the directory that to which the file 
              will be downloaded.

        :Raises:
            - :class:`.RestCallException` if any errors occured in the API
              client.
        """
        
        try:
            uploaded = self.is_uploaded()

        except RestCallException:
            raise
        except FileMissingException:
            return #TODO: We should be able to download a file that doesn't
                   # exist locally.
        
        if uploaded is None:
            self._log.debug("File has not been previously uploaded. "
                            "Cannot download file.")
            return

        resp = self._api.props_file(uploaded)

        if not resp.success:
            self._log.debug("Unable to retrieve properties of uploaded "
                            "file: {0}".format(resp.result))
            raise resp.result

        else:
            size = resp.result
            dl_file = self._api.get_file(self, size, download_dir)

            if not dl_file.success:

                self._log.debug("Failed to download file: "
                                "{0}".format(dl_file.result))
                raise dl_file.result

            else:
                self._log.info("Successfully downloaded file to "
                               "{0}".format(download_dir))
