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

from __future__ import with_statement

import logging
import os
import shutil
import time
import sys
    
try:
    import configparser

except ImportError:
    import ConfigParser as configparser

from .exceptions import InvalidConfigException
from . import utils

LOGGERS = {}
API_RESOURCE = "https://batchapps.core.windows.net/"
FILE_LOG = True
STREAM_LOG = True

class Configuration(object):
    """
    Manage the configuration of the Batch Apps module, logging and job service.
    A Configuration object, either default or custom, is used to create both
    Job and File managers.
    """

    def __init__(self,
                 data_path=None,
                 log_level=None,
                 jobtype=None,
                 name="batch_apps.ini",
                 datadir="BatchAppsData",
                 default=False,
                 **kwargs):
        """
        A new :class:`.Configuration` will attempt to use an existing saved
        config, and if one is not found default configuration will be used.
        Default configuration can also be forced, though this will overwrite
        an existing config if one exists.

        :Kwargs:
            - data_path (str): The path where Batch Apps client data
              (logs, configs) will be saved. If not set, will default to User
              directory, i.e. ``os.path.expanduser("~")``
            - log_level (str): The level of logging during Batch Apps session.
              Must be a string in ``['debug', 'info', 'warning', 'error',
              'critical']``. If not set default is 'warning'.
            - jobtype (str): The application job type, used to determine
              how a job will be processed in the cloud. The list of available
              job types will depend on the configuration and can checked
              using the :meth:`.list_jobtypes()` method.
              Default job type is 'Blender', unless overridden in config.
            - name (str): The name of the configuration file to read from and
              save to. Unless set, the default 'batch_apps.ini' will be used.
            - datadir (str): The name of the directory that will be created to
              hold the date (logs etc). Unless set the default
              'BatchAppsData' will be used.
            - default (bool): If ``True``, the default configuration will be
              used regardless of whether an existing configuration file is
              found. Any existing config will be overwritten by defaults
              (unless an alternative config ``name`` is set).

        :Raises:
            - :exc:`.InvalidConfigException` if the specified job type is
              not defined in the config.

        """
        self._config = configparser.RawConfigParser()
        self._config.optionxform = str
        self._dir = datadir
        self.jobtype = 'Blender'

        if data_path and self._check_directory(data_path):
            self._write_file = True
            cfg_path = os.path.join(data_path, self._dir)
        else:
            self._write_file = self._check_directory(os.path.expanduser("~"))
            cfg_path = os.path.join(os.path.expanduser("~"), self._dir)

        self._cfg_file = os.path.join(cfg_path, name)
        self._log = self._configure_logging(cfg_path)

        if not default and os.path.isfile(self._cfg_file):
            try:
                self._config.read(self._cfg_file)
                for sec in self._config.sections():

                    if (self._config.has_option(sec, "default_jobtype") and
                    self._config.get(sec, "default_jobtype") == "True"):
                        self.jobtype = sec
                        break

                    if (self._config.has_option(sec, "default_app") and #DEP
                    self._config.get(sec, "default_app") == "True"):
                        self._log.warning(
                            "Use of setting 'default_app' is "
                            "deprecated. Please use 'default_jobtype.'")

                        self.jobtype = sec
                        break

            except EnvironmentError as exp:
                print("Failed to load config {0} with error: {0}".format(exp))
                self._set_defaults()
        else:
            self._set_defaults()

        if LOGGERS.get('level'):
            current_level = LOGGERS.get('level')
        else:
            current_level = int(self._config.get("Logging", "level"))

        self._set_logging_level(log_level if log_level else current_level)

        if jobtype:
            self.jobtype = jobtype

        elif kwargs.get('application'): #DEP
            self._log.warning("Use of kwarg 'application' is deprecated. "
                              "Please replace with 'jobtype'.")
            self.jobtype = kwargs.get('application')

        if not self._config.has_section(self.jobtype):
            raise InvalidConfigException(
                "Config file has no setting for job type: {type}. "
                "Please specify alternative config or job type.".format(
                    type=self.jobtype))
        self.job_type = self.jobtype #DEP

    def _set_defaults(self):
        """Create all default config data.

        This will save the default configuration file.
        It will also set global logging variables to be used throughout the
        session unless overridden.
        """
        self._config.add_section("Blender") # Sample Job Type Config
        self._config.set("Blender", "filename", "output")
        self._config.set("Blender", "format", "png")
        self._config.set("Blender", "start", "1")
        self._config.set("Blender", "end", "10")
        self._config.set("Blender", "command", "PNG")
        self._config.set("Blender", "default_jobtype", "True")

        self._config.add_section("Test")
        self._config.set("Test", "param1", "abc")
        self._config.set("Test", "param2", "xyz")

        if not self._config.has_section('Logging'):
            self._config.add_section("Logging")

        log_dir = os.path.dirname(self._cfg_file)
        gb_log = os.path.join(log_dir, "batch_apps.log")

        self._config.set("Logging", "output", gb_log)
        self._config.set("Logging", "level", 30)
        LOGGERS.update({'level':30})

        self._config.add_section("Authentication")

        self._config.set("Authentication", "endpoint", "")
        self._config.set("Authentication", "unattended_account", "")
        self._config.set("Authentication", "unattended_key", "")
        self._config.set("Authentication", "client_id", "")
        self._config.set("Authentication", "redirect_uri", "")
        self._config.set("Authentication", "tenant", "common")

        self._config.set("Authentication", "auth_uri", "/oauth2/authorize")
        self._config.set("Authentication", "token_uri", "/oauth2/token")
        self._config.set("Authentication", "root", "login.windows.net/")
        self._config.set("Authentication", "resource", API_RESOURCE)
        

        self.save_config()

    def _check_directory(self, test_dir):
        """
        Check that the assigned directory exists and is able to be
        written to. Because logging has not yet been configured at this
        point, any errors will only be printed to stdout.
        If the directory check fails, the configuration object can still
        be used however no data (including logging) will be written to disk.

        :Args:
            - test_dir (str): Full path to the directory to be tested. If this
              directory does not yet exist it will attempt to create it.
              It will also attempt to write and then remove a temp file to
              this directory to ensure the correct permissions are available.

        :Returns:
            - ``True`` if the directory exists and can be written to,
              else ``False``.
        """
        test_dir = os.path.join(test_dir, self._dir)
        try:
            if not os.path.isdir(test_dir):
                os.mkdir(test_dir)

            with open(os.path.join(test_dir, "aba_test"), 'w') as test_file:
                test_file.write("All good to go!")

            os.remove(os.path.join(test_dir, "aba_test"))
            return True

        except (IOError, OSError, EnvironmentError) as exp:
            message = (
                "\nBatch Apps client is unable to write to directory: {path}\n"
                "Error: {error}\n"
                "Batch Apps session will continue without writing any "
                "data to disk.\nWarning: This includes logging.\n"
                "Please reconfigure output directory to enable file "
                "logging.\n".format(path=test_dir, error=exp))
            print(message)
            return False

    def _configure_logging(self, data_path):
        """
        Create logger and configure message format and output.
        A new session will append to an existing log file if one exists.
        If an existing log file has exceeded 10mb, it will be 'archived',
        and a new log file created.

        All logging statements will be in the following format:
            ``"%(asctime)-15s [%(levelname)s] %(module)s: %(message)s"``

        :Args:
            - data_path (str): The path that the log file will be written to
              if file writing is enabled in the configuration
              (see :meth:._check_directory())

        :Returns:
            - :class:`.PickleLogger`: Configured logging singleton, using
              custom serializable Logger extension class.
        """

        if not self._config.has_section('Logging'):
            self._config.add_section('Logging')

        if LOGGERS.get('batch_apps'):
            return LOGGERS.get('batch_apps')

        log_format = logging.Formatter(
            "%(asctime)-15s [%(levelname)s] %(module)s: %(message)s")

        logger = logging.getLogger('batch_apps')

        if STREAM_LOG:
            console_logging = logging.StreamHandler()
            console_logging.setFormatter(log_format)
            logger.addHandler(console_logging)

        if self._write_file and FILE_LOG:
            logfile = os.path.join(data_path, "batch_apps.log")

            if os.path.isfile(logfile) and os.path.getsize(logfile) > 10485760:
                split_log = os.path.splitext(logfile)
                timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
                shutil.move(logfile, "{root}-{date}{ext}".format(
                    root=split_log[0],
                    date=timestamp,
                    ext=split_log[1]))

            file_logging = logging.FileHandler(logfile)
            file_logging.setFormatter(log_format)
            logger.addHandler(file_logging)

        LOGGERS.update({'batch_apps':logger})
        logger.debug("Logger created with file={0}".format(self._write_file))
        return logger

    def _set_logging_level(self, level):
        """Set logging level.

        :Args:
            - level (str): The logging level required for the session.
              Must be one of the following:
              ``['debug', 'info', 'warning', 'error', 'critical']``.
              The input is not case sensitive. If an invalid input is
              supplied, the default level - 'warning' - will be set.

        :Returns:
            - The level applied (int).
        """
        levels = {'debug': 10,
                  'info': 20,
                  'warning': 30,
                  'error': 40,
                  'critical': 50}

        if isinstance(level, str) and level.lower() in levels:
            level = levels[level.lower()]

        elif ((not isinstance(level, int)) or
              (level not in levels.values())):

            print("Logging level '{level}' not recognized. Must be a string "
                  "name such as 'debug' or the associated integer. Defaulting"
                  " to level WARNING.".format(level=level))
            level = 30

        self._config.set("Logging", "level", level)
        self._log.setLevel(level)
        for handle in self._log.handlers:
            handle.setLevel(level)

        LOGGERS.update({'level':level})
        self._log.debug("Logging level set to {0}".format(level))
        return logging.getLevelName(level)

    def _reformat_config(self, old_auth):
        """
        Reformat a deprecated config to allow for backwards
        compatibility with v0.1.1.

        :Args:
            - old_auth (dict): Authentication config setting.

        :Returns:
            - A dictionary containing compatible auth config.

        :Raises:
            - :class:`.InvalidConfigException` if unable to reformat
              auth into correct format.
        """
        self._log.warning("Configuration file format is deprecated. "
                          "Please regenerate.")

        new_auth = {}
        new_auth["resource"] = old_auth.get("resource")
        new_auth["root"] = "login.windows.net/"
        new_auth["auth_uri"] = "/oauth2/authorize"
        new_auth["token_uri"] = "/oauth2/token"

        try:
            old_job =  dict(self._config.items(self.jobtype))
            new_auth["endpoint"] = old_job.get("endpoint")
            new_auth["client_id"] = old_job.get("client_id")
            new_auth["redirect_uri"] = old_job.get("redirect_uri")

            auth_uri = old_auth.get("auth_uri").split("/")
            tenant_index = auth_uri.index("login.windows.net") + 1
            new_auth["tenant"] = auth_uri[tenant_index]

            new_auth["unattended_account"] = old_auth.get("service_principal")
            new_auth["unattended_key"] = old_auth.get("service_principal_key")

        except(ValueError, KeyError, IndexError):
            raise InvalidConfigException(
                "Configuration file is out-of-date and "
                "unable to be reconciled. Please regenerate")

        return new_auth

    def set_default_application(self):
        """
        .. warning:: Deprecated. Use :meth:`.set_default_jobtype()`.

        Set the job type to be used by default when creating a
        :class:`.Configuration` object. This method will set the current
        job type to be the default, and will save the changes.
        """
        self._log.warning("set_default_application() has been deprecated. "
                          "Please use set_default_jobtype()")
        return self.set_default_jobtype()

    def set_default_jobtype(self):
        """
        Set the job type to be used by default when creating a
        :class:`.Configuration` object. This method will set the current
        job type to be the default, and will save the changes.
        """
        for sec in self._config.sections():

            if (self._config.has_option(sec, "default_app") and #DEP
            self._config.get(sec, "default_app") == "True"):

                self._config.remove_option(sec, "default_app")

            if (self._config.has_option(sec, "default_jobtype") and
            self._config.get(sec, "default_jobtype") == "True"):

                self._config.remove_option(sec, "default_jobtype")

        self._config.set(self.jobtype, "default_jobtype", "True")

        if self._write_file:
            self.save_config()


    def save_config(self):
        """
        Save configuration settings to file.
        Any changes made to the configuration will not be saved by default.
        So this method must be called to persist any changes to future
        sessions. Any saved changes will be lost if a new default
        :class:`.Configuration` object is created with the same path, or if
        :meth:`.clear_config()` is called. If an error occurs during file
        writing, this will be logged but not raised.

        :Returns:
            - ``True`` if save was successful, else ``False``.
        """
        if not self._write_file:
            self._log.warning("Config file writing disabled - "
                              "cannot save config changes")
            return False

        try:
            with open(self._cfg_file, 'w') as configfile:
                self._config.write(configfile)
            return True

        except (IOError, OSError) as exp:
            self._log.error("Failed to create configuration file: {file}. "
                            "Error: {error}".format(file=self._cfg_file,
                                                    error=exp))
            return False

    def clear_config(self):
        """
        Delete any existing config file and reset defaults.
        This will save a new default config file to the allocated path.
        If an error occurs during removing of the old config, this will be
        logged but not raised.

        :Returns:
            - ``True`` is the config was successfully cleared, else ``False``.
        """
        try:
            self._log.debug("Attempting to clear config "
                            "file {0}".format(self._cfg_file))

            os.remove(self._cfg_file)
            self._config = configparser.RawConfigParser()
            self._config.optionxform = str
            self._set_defaults()
            self._log.info("Deleted config file and reset config to defaults")
            return True

        except (IOError, OSError) as exp:
            self._log.error("Failed to remove configuration file: {file}. "
                            "Error: {error}".format(file=self._cfg_file,
                                                    error=exp))
            return False

    def endpoint(self, *endpoint):
        """
        Get and set the endpoint for the Batch Apps service.

        :Args:
            - endpoint (str): *optional* A new endpoint, if supplied, will
              change the configured endpoint. To persist changes
              :meth:`.save_config()` must be called.

        :Returns:
            - If ``endpoint`` is not supplied, the current endpoint will
              be returned (str). Otherwise the new endpoint (str).

        :Raises:
            - :exc:`.InvalidConfigException` if no endpoint found in the
              configuration.

        """
        end_p = ""
        if not self._config.has_section("Authentication"):
            raise InvalidConfigException("Config has no Authentication")

        elif len(endpoint) > 0:
            self._log.info("Changing endpoint from {old} to {new}".format(
                old=self.endpoint(), new=endpoint))

            self._config.set("Authentication", 'endpoint', str(endpoint[0]))
            end_p = str(endpoint[0])

        elif self._config.has_option("Authentication", "endpoint"):
            end_p = self._config.get("Authentication", "endpoint")

        elif self._config.has_option(self.jobtype, "endpoint"): #DEP
            self._log.warning("Job type config in deprecated format. "
                              "Please regenerate.")
            end_p = self._config.get(self.jobtype, "endpoint")

        else:
            raise InvalidConfigException("No valid endpoint value for "
                                         "{type}".format(type=self.jobtype))
        if end_p.startswith("http://"):
            end_p = end_p[7:]

        elif end_p.startswith("https://"):
            end_p = end_p[8:]

        return end_p

    def logging_level(self, *level):
        """Gets and sets the current logging level.

        :Args:
            - level (str): *optional* A new level, if supplied, all further
              logging in the current session will be at the new level. To
              persist changes :meth:`.save_config()` must be called.

        :Returns:
            - If ``level`` is not supplied, the current level used will be
              returned (str). Otherwise the new level (str).

        :Raises:
            - :exc:`.InvalidConfigException` if current configuration does not
              have a logging level configured.

        """
        if len(level) > 0 and self._config.has_option('Logging', 'level'):
            self._log.info("Setting logging level from {0}"
                           " to {1}".format(self.logging_level(), level))

            return self._set_logging_level(str(level[0]))

        elif self._config.has_option('Logging', 'level'):
            return logging.getLevelName(
                int(self._config.get('Logging', 'level')))

        else:
            raise InvalidConfigException(
                "No valid logging level found. Please set.")

    def application(self, *jobtype):
        """
        .. warning:: Deprecated. Please use :meth:`.current_jobtype()`.

        Gets and sets the current job type.

        :Args:
            - jobtype (str): *optional* A job type, if supplied,
              will update the current job type and job configuration for new
              job submissions.

        :Returns:
            - The current job type (str)

        :Raises:
            - :exc:`.InvalidConfigException` if the supplied job type has no
              associated configuration.

        """
        self._log.warning("application() has been deprecated. "
                          "Please use current_jobtype()")
        return self.current_jobtype(*jobtype)

    def current_jobtype(self, *jobtype):
        """
        Gets and sets the current job type.

        :Args:
            - jobtype (str): *optional* A job type, if supplied,
              will update the current job type and job configuration for new
              job submissions.

        :Returns:
            - The current job type (str)

        :Raises:
            - :exc:`.InvalidConfigException` if the supplied job type has no
              associated configuration.

        """
        if jobtype and self._config.has_section(str(jobtype[0])):
            self._log.info("Setting job type from {0} to {1}".format(
                self.jobtype,
                str(jobtype[0])))

            self.jobtype = str(jobtype[0])

        elif jobtype and not self._config.has_section(str(jobtype[0])):
            raise InvalidConfigException(
                "No configuration for '{type}' found."
                " Please add it.".format(type=jobtype))

        self.job_type = self.jobtype #DEP
        return self.jobtype

    def applications(self):
        """
        .. warning:: Deprecated. Please use :meth:`.list_jobtypes()`.

        Gets a list of all the job types defined in the configuration.

        :Returns:
            - A list of strings of the job types options configured.

        """
        self._log.warning("applications() is deprecated. "
                          "Please use list_jobtypes().")
        return self.list_jobtypes()

    def list_jobtypes(self):
        """Gets a list of all the job types defined in the configuration.

        :Returns:
            - A list of strings of the job types options configured.

        :Raises:
            - :class:`.InvalidConfigException` if either Logging or
              Authentication sections are missing from the config.
        """
        types = list(self._config.sections())
        try:
            types.remove("Logging")
            types.remove("Authentication")
        except ValueError:
            raise InvalidConfigException("Config missing key element")
        return types

    def default_params(self):
        """Gets the default parameters for the current job type.

        :Returns:
            - A dictionary of all the string parameters tied to the job type.

        """
        return dict(self._config.items(self.jobtype))

    def add_application(self, jobtype, *args, **params):
        """
        .. warning:: Deprecated. Please use :meth:`.add_jobtype()`.

        Add a new job type section to the configuration.

        :Args:
            - jobtype (str): The name of the job type to be added.

        :Kwargs:
            - params: *optional* Any additional parameters to be submitted
              with a job of this type can be added as keyword arguments.

        """
        self._log.warning("add_application() is deprecated. "
                          "Please use add_jobtype().")
        return self.add_jobtype(jobtype, **params)

    def add_jobtype(self, jobtype, **params):
        """Add a new job type section to the configuration.

        :Args:
            - jobtype (str): The name of the job type to be added.

        :Kwargs:
            - params: *optional* Any additional parameters to be submitted
              with a job of this type can be added as keyword arguments.

        """
        self._log.debug("Configuring new job type: {type}".format(
            type=jobtype))

        if not self._config.has_section(jobtype):
            self._config.add_section(jobtype)

        for (option, value) in params.items():
            self._config.set(jobtype, option, value)

    def set(self, param, value):
        """Set or add a parameter to the configuration of the current
        job type.

        :Args:
            - param (str): The parameter to set, either new or already
              existing.
            - value (str): The value to assign to the given parameter.

        """
        self._log.debug("Setting {jt} parameter {prm} to {val}".format(
            jt=self.jobtype,
            prm=param,
            val=value))

        try:
            self._config.set(self.jobtype, str(param), str(value))

        except configparser.NoSectionError:
            raise InvalidConfigException(
                "Current job type {0} has no valid"
                " configuration to set to.".format(self.jobtype))

    def get(self, param):
        """Get a parameter from the current job type configuration.

        :Args:
            - param (str): The parameter to retrieve.

        :Returns:
            - The value of the given parameter (str) if it exists.
            - ``None`` if the parameter doesn't exist and a warning will be logged.

        """
        try:
            return self._config.get(self.jobtype, param)

        except (AttributeError, configparser.Error) as exp:
            self._log.warning(
                "Couldn't get {prm} parameter for {jt}. Error: "
                "{err}".format(prm=param, jt=self.jobtype, err=exp))

            return None

    def remove(self, setting):
        """
        Remove a parameter or job type from the config.
        For these changes to be persisted :meth:`.save_config()`
        must be called.

        :Args:
            - setting (str): Job type or parameter to be removed from
              the config. If the supplied setting is not a job type or
              current job type parameter, nothing will happen. The
              current job type, or 'Logging' and 'Authentication' sections
              cannot be removed.
        
        :Returns:
            - ``True`` if the parameter of section was found as removed.
            - ``False`` if the selected section was the current job type
              or "Authentication" or "Logging". Will also be ``False`` if
              the job type or parameter were not found.

        """
        setting = str(setting)

        if setting in ['Logging', 'Authentication', self.jobtype]:
            self._log.warning("Cannot remove config for {0}".format(setting))
            return False

        elif self._config.has_section(setting):

            self._log.debug("Removing {jt} from "
                            "configuration".format(jt=self.jobtype))

            self._config.remove_section(setting)
            return True

        elif self._config.has_option(self.jobtype, setting):

            self._log.debug("Removing {jt} parameter {prm}".format(
                jt=self.jobtype,
                prm=setting))

            self._config.remove_option(self.jobtype, setting)
            return True

        else:
            self._log.info("Configuration has no job type or "
                           "parameter {0}".format(setting))
            return False

    def aad_config(self, account=None, key=None, client_id=None, tenant=None,
                  redirect=None, endpoint=None, unattended=False, validate=True, **kwargs):
        """Configure AAD authentication parameters to accompany an existing
        Batch Apps Service.
        If new values are set, :meth:`.save_config()` must be called for
        changes to be persisted.
        Backwards compatible with v0.1.1.

        :Kwargs:
            - account (str): The account string in the format as retrieved
              from the Batch Apps portal: ``ClientID=abc;TenantID=xyz``.
            - key (str): An Unattended Account key. This can be created in
              the Batch Apps portal.
            - client_id (str): The client ID, this can be retrieved from
              the AAD portal (not required if using an Unattended Account).
            - tenant (str): The auth tenant, this can be retrieved from
              the AAD portal (not required if using an Unattended Account).
            - redirect (str): The redirect url used for web UI login. This
              can be configured in the AAD portal (not required if using an
              Unattended Account).
            - endpoint (str): The Batch Apps service endpoint. This can be
              found in the service details in the Batch Apps Portal.
            - unattended (bool): Whether the intended authentication method
              will be unattended. The default is ``False``.

        :Returns:
            - dict containing the authentication parameters.

        :Raises:
            - :class:`.InvalidConfigException` if the authentication defaults
              are not found in the configuration or if any required information
              is missing. This will be raised after any new values passed in
              have been set.
        """

        if not self._config.has_section("Authentication"):
            raise InvalidConfigException("Config file has no Auth details.")

        if not self._config.has_option("Authentication", "root"): # old config

            auth_cfg = dict(self._config.items("Authentication"))
            auth_cfg = self._reformat_config(auth_cfg)

            self._config.remove_section("Authentication")
            self._config.add_section("Authentication")

            for setting in auth_cfg:
                self._config.set("Authentication", setting, auth_cfg[setting])

        if account is not None:
            self._config.set("Authentication", "unattended_account", str(account))

        if key is not None:
            self._config.set("Authentication", "unattended_key", str(key))

        if client_id is not None:
            self._config.set("Authentication", "client_id", str(client_id))

        if tenant is not None:
            self._config.set("Authentication", "tenant", str(tenant))

        if redirect is not None:
            self._config.set("Authentication", "redirect_uri", str(redirect))

        if endpoint is not None:
            self._config.set("Authentication", "endpoint", str(endpoint))

        if validate:
            auth_dict = self._validate_auth(unattended)
        else:
            auth_dict = dict(self._config.items("Authentication"))

        return auth_dict

    def _invalid_data(self, value):
        """
        Check that config value is neither ``None`` or empty.

        :Args:
            - value (str): The config value to check.

        :Returns:
            - ``True`` if value is invalid, else ``False``.
        """
        if not value or value == "":
            return True

        if '{' in value:
            return True

        return False

    def _validate_auth(self, unattended):
        """
        Check all the authentication settings in the config for
        valid entries based on auth type.

        :Args:
            - unattended (bool): ``True`` if authenticating via unattended
              account, else ``False``.

        :Returns:
            - Dictionary of all values in the Authentication config.

        :Raises:
            - :class:`.InvalidConfigException` if any required values are
              ``None`` or empty.
        """

        auth = dict(self._config.items("Authentication"))
        required = ['endpoint',
                    'resource',
                    'root',
                    'auth_uri',
                    'token_uri']

        if unattended:
            required.append("unattended_account")
            required.append("unattended_key")
        else:
            required.append("client_id")
            required.append("tenant")
            required.append("redirect_uri")

        valid_data = []
        for req_key in required:
            valid_data.append(auth.get(req_key))

        validated = [self._invalid_data(d) for d in valid_data]
        if any(validated):
            missing_val = required[validated.index(True)]
            raise InvalidConfigException(
                "Authentication configuration incomplete. "
                "Missing data for: {0}".format(missing_val))

        return auth

        