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

from __future__ import with_statement

import logging
import os
import shutil
import time

import sys
VERSION = sys.version_info

if VERSION[:1] == (2,):
    import ConfigParser as configparser
else:
    import configparser

from .exceptions import InvalidConfigException
from . import utils

LOGGERS = {}

class Configuration(object):
    """
    Manage the configuration of the Batch Apps module, logging and job service.
    A Configuration object, either default or custom, is used to create both
    Job and File managers.
    """

    def __init__(self,
                 data_path=None,
                 log_level=None,
                 application="Blender",
                 name="batch_apps.ini",
                 datadir="BatchAppsData",
                 default=False):
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
            - application (str): The application job type, used to determine
              how a job will be processed in the cloud. The list of available
              job types will depend on the configuration and can checked
              using the :meth:`.applications()` method.
              Default application is 'Blender'.
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
            - :exc:`.InvalidConfigException` if the specified application is
              not defined in the config.

        """
        self._config = configparser.RawConfigParser()
        self._config.optionxform = str
        self._dir = datadir
        self.job_type = application

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
                    if (self._config.has_option(sec, "default_app") and
                    self._config.get(sec, "default_app") == "True"):
                        self.job_type = sec

            except EnvironmentError as exp:
                print("Failed to load config {0} with error: {0}".format(exp))
                self._set_defaults()
        else:
            self._set_defaults()

        if LOGGERS.get('level'):
            current_level = LOGGERS.get('level')
        else:
            current_level = self._config.get("Logging", "level")

        self._set_logging_level(log_level if log_level else current_level)

        if not self._config.has_section(self.job_type):
            raise InvalidConfigException(
                "Config file has no parameters for application: {type}. "
                "Please specify alternative config or application.".format(
                    type=self.job_type))

    def _set_defaults(self):
        """Create all default config data.

        This will save the default configuration file.
        It will also set global logging variables to be used throughout the
        session unless overridden.
        """
        self._config.add_section("Blender") # Sample Application Config
        self._config.set("Blender", "client_id", "{client_id}")
        self._config.set("Blender", "endpoint", "{endpoint}")
        self._config.set("Blender", "redirect_uri", "{redirect}")
        self._config.set("Blender", "filename", "")
        self._config.set("Blender", "SubstLocalStoragePath", "True")
        self._config.set("Blender", "format", "")
        self._config.set("Blender", "useoriginalpaths", "True")
        self._config.set("Blender", "start", "")
        self._config.set("Blender", "end", "")
        self._config.set("Blender", "command", "")
        self._config.set("Blender", "VhdVersionOverride", "")
        self._config.set("Blender", "default_app", "True")

        self._config.add_section("Test")
        self._config.set("Test", "client_id", "{client_id}")
        self._config.set("Test", "endpoint", "{endpoint}")
        self._config.set("Blender", "redirect_uri", "{redirect}")

        if not self._config.has_section('Logging'):
            self._config.add_section("Logging")

        gb_log = os.path.join(os.path.dirname(self._cfg_file),
                              "batch_apps.log")

        self._config.set("Logging", "output", gb_log)
        self._config.set("Logging", "level", 30)
        LOGGERS.update({'level':30})

        self._config.add_section("Authentication")
        self._config.set("Authentication",
                         "auth_uri",
                         "login.windows.net/common/oauth2/authorize")
        self._config.set("Authentication",
                         "resource",
                         "batchapps.core.windows.net/")
        self._config.set("Authentication",
                         "token_uri",
                         "login.windows.net/common/oauth2/token")
        self._config.set("Authentication", "service_principal", "")
        self._config.set("Authentication", "service_principal_key", "")

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

            with open(os.path.join(test_dir, "gb_test"), 'w') as test_file:
                test_file.write("All good to go!")

            os.remove(os.path.join(test_dir, "gb_test"))
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

        All logging statements will be in the folowing format:
            ``"%(asctime)-15s [%(levelname)s] %(module)s: %(message)s"``

        :Args:
            - data_path (str): The path that the log file will be written to
              if file writting is enabled in the configuration
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
        console_logging = logging.StreamHandler()
        console_logging.setFormatter(log_format)
        logger.addHandler(console_logging)

        if self._write_file:
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

        if isinstance(level, str) and level.lower() in utils.get_keys(levels):
            level = levels[level.lower()]

        elif ((not isinstance(level, int)) or
              (level not in utils.get_values(levels))):

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

    def set_default_application(self):
        """
        Set the application to be used by default when createing a
        :class:`.Configuration` object. This method will set the current
        application to be the default, and will save the changes.
        """
        for sec in self._config.sections():

            if (self._config.has_option(sec, "default_app") and
            self._config.get(sec, "default_app") == "True"):

                self._config.remove_option(sec, "default_app")

        self._config.set(self.job_type, "default_app", "True")

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
        """Get and sets the endpoint associated with the current application.

        :Args:
            - endpoint (str): *optional* A new endpoint, if supplied, will
              redirect job submission for the current application. To persist
              changes :meth:`.save_config()` must be called.

        :Returns:
            - If ``endpoint`` is not supplied, the endpoint for the current
              application will be returned (str). Otherwise the new
              endpoint (str).

        :Raises:
            - :exc:`.InvalidConfigException` if current application does not
              have an endpoint configured.

        """
        if len(endpoint) > 0 and self._config.has_section(self.job_type):
            self._log.info("Redirecting endpoint for application {app} "
                           "from {old} to {new}".format(app=self.job_type,
                                                        old=self.endpoint(),
                                                        new=endpoint))

            self._config.set(self.job_type, 'endpoint', str(endpoint[0]))
            return str(endpoint[0])

        elif self._config.has_option(self.job_type, "endpoint"):
            return self._config.get(self.job_type, "endpoint")

        else:
            raise InvalidConfigException("No valid endpoint value for "
                                         "{type}".format(type=self.job_type))

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

    def application(self, *application):
        """
        Gets and sets the current job application.
        If setting a new application, this will also change all associated
        parameters and the endpoint to those configured to the new application.

        :Args:
            - application (str): *optional* A new application, if supplied,
              will update the current job type and job configuration for new
              job submissions.

        :Returns:
            - The current application (str)

        :Raises:
            - :exc:`.InvalidConfigException` if the supplied application has no
              associated configuration.

        """
        if application and self._config.has_section(str(application[0])):
            self._log.info("Setting application from {0} to {1}".format(
                self.job_type,
                str(application[0])))

            self.job_type = str(application[0])

        elif application and not self._config.has_section(str(application[0])):
            raise InvalidConfigException(
                "No configuration for '{type}' found."
                " Please add it.".format(type=application))

        return self.job_type

    def applications(self):
        """Gets a list of all the applications defined in the configuration.

        :Returns:
            - A list of strings of the application options configured.

        """
        apps = list(self._config.sections())
        apps.remove("Logging")
        return apps

    def default_params(self):
        """Gets the default parameters for the current application.

        :Returns:
            - A dictionary of all the string parameters tied to the application.
              This includes the application endpoint.

        """
        return dict(self._config.items(self.job_type))

    def add_application(self, application, endpoint, client_id, **params):
        """Add a new application section to the configuration.

        :Args:
            - application (str): The name of the application / job type to be
              added.
            - endpoint (str): The api endpoint for all server communication for
              this application.

        :Kwargs:
            - params: *optional* Any additional parameters to be associated
              with the application and to be submitted with a job of this
              type can be added as keyword arguments.

        """
        self._log.debug("Configuring new application: "
                        "{app} with endpoint {end}".format(app=application,
                                                           end=endpoint))

        if not self._config.has_section(application):
            self._config.add_section(application)

        self._config.set(application, "endpoint", endpoint)
        self._config.set(application, "client_id", client_id)

        for (option, value) in params.items():
            self._config.set(application, option, value)

    def set(self, param, value):
        """Set or add a parameter to the configuration of the current
        application.

        :Args:
            - param (str): The parameter to set, either new or already
              existing.
            - value (str): The value to assign to the given parameter.

        """
        self._log.debug("Setting {app} parameter {prm} to {val}".format(
            app=self.job_type,
            prm=param,
            val=value))

        try:
            self._config.set(self.job_type, str(param), str(value))

        except configparser.NoSectionError:
            raise InvalidConfigException(
                "Current application {0} has no valid"
                " configuration to set to.".format(self.job_type))

    def get(self, param):
        """Get a parameter from the current application configuration.

        :Args:
            - param (str): The parameter to retrieve.

        :Returns:
            - The value of the given parameter (str) if it exists.
            - ``None`` if the parameter doesn't exist and a warning will be logged.

        """
        try:
            return self._config.get(self.job_type, param)

        except (AttributeError, configparser.Error) as exp:
            self._log.warning(
                "Couldn't get {prm} parameter for {app}. Error: "
                "{err}".format(prm=param, app=self.job_type, err=exp))

            return None

    def remove(self, setting):
        """
        Remove a parameter or whole whole section from the config.
        For these changes to be persisted :meth:`.save_config()`
        must be called.

        :Args:
            - setting (str): Application or parameter to be removed from
              the config. If the supplied setting is not an application or
              current application parameter, nothing will happen. The
              'Logging' and 'Authentication' sections cannot be removed.
              Likewise, the 'endpoint' parameter for an application cannot
              be removed.

        :Raises:
            - :exc:`ValueError` if the section to be removed is the current
              application. The current application will need to be changed before
              the section can be removed.
        """
        setting = str(setting)
        if (self._config.has_section(str(setting)) and
            setting not in ['Logging', 'Authentication']):

            if setting == self.job_type:
                self._log.warning(
                    "The configuration for current application "
                    "{app} cannot be removed".format(app=self.job_type))

                raise ValueError(
                    "Cannot remove section for current application.")

            self._log.debug("Removing {app} from "
                            "configuration".format(app=self.job_type))

            self._config.remove_section(setting)
            return True

        elif (self._config.has_option(self.job_type, setting) and
              setting not in ['endpoint']):

            self._log.debug("Removing {app} parameter {prm}".format(
                app=self.job_type,
                prm=setting))

            self._config.remove_option(self.job_type, setting)
            return True

        else:
            self._log.info("Configuration has no application or "
                           "parameter {0}".format(setting))
            return False

    def aad_config(self):
        """Retrieve the authentication details from the configuration.
        Used by the :mod:`.credentials` module.

        :Returns:
            - dict containing the authentication parameters.

        :Raises:
            - :class:`.InvalidConfigException` is the authentication defaults
              are not found in the configuration.
        """
        try:
            return dict(self._config.items("Authentication"))

        except configparser.NoSectionError:
            raise InvalidConfigException(
                "No valid authentication configuration found.")

        