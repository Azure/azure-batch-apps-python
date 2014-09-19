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
"""Unit tests for Configuration"""

import sys

if sys.version_info[:2] <= (2, 7, ):
    import unittest2 as unittest
else:
    import unittest

if sys.version_info[:2] >= (3, 3, ):
    from unittest import mock
else:
    import mock

import os
import logging
import batch_apps.config
from batch_apps import Configuration
from batch_apps.exceptions import InvalidConfigException

if sys.version_info[:1] == (2,):
    import ConfigParser as configparser
    BUILTIN_OPEN = "__builtin__.open"
else:
    import configparser
    BUILTIN_OPEN = "builtins.open"

# pylint: disable=W0212
class TestConfiguration(unittest.TestCase):
    """Unit tests for Configuration"""

    def setUp(self):
        self.userdir = os.path.expanduser("~")
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.test_dir = os.path.join(self.cwd, "test_assets", "test_config")
        return super(TestConfiguration, self).setUp()

    @mock.patch.object(Configuration, '_check_directory')
    @mock.patch.object(Configuration, '_configure_logging')
    @mock.patch.object(Configuration, '_set_logging_level')
    @mock.patch.object(Configuration, 'save_config')
    @mock.patch.object(batch_apps.config.os.path, 'isfile')
    @mock.patch.object(batch_apps.config.configparser.RawConfigParser, 'read')
    def test_config_set_defaults(self,
                                 mock_read,
                                 mock_file,
                                 mock_save,
                                 mock_level,
                                 mock_logging,
                                 mock_dir):
        """Test _set_defaults"""

        mock_dir.return_value = False
        mock_logging.return_value = logging.getLogger("defaults")
        mock_file.return_value = False

        cfg = Configuration(default=True)
        self.assertTrue(mock_save.called)
        self.assertFalse(mock_read.called)
        self.assertFalse(mock_file.called)
        mock_logging.assert_called_with(
            os.path.join(self.userdir, "BatchAppsData"))

        mock_level.assert_called_with(30)
        self.assertEqual(sorted(cfg._config.sections()),
                         sorted(["Authentication",
                                 "Blender",
                                 "Logging",
                                 "Test"]))

        cfg = Configuration()
        self.assertTrue(mock_save.called)
        self.assertFalse(mock_read.called)
        self.assertTrue(mock_file.called)
        mock_logging.assert_called_with(
            os.path.join(self.userdir, "BatchAppsData"))

        self.assertEqual(sorted(cfg._config.sections()),
                         sorted(["Authentication",
                                 "Blender",
                                 "Logging",
                                 "Test"]))

        cfg = Configuration(data_path="c:\\mypath",
                            log_level=10,
                            datadir="data")

        self.assertFalse(mock_read.called)
        mock_dir.assert_any_call("c:\\mypath")
        mock_dir.assert_any_call(self.userdir)
        mock_logging.assert_called_with(os.path.join(self.userdir, "data"))
        mock_level.assert_called_with(10)

        mock_file.return_value = True
        cfg = Configuration(default=True)
        self.assertTrue(mock_save.called)
        self.assertFalse(mock_read.called)

        mock_save.reset()
        mock_read.side_effect = OSError("test")
        cfg = Configuration(data_path=self.test_dir, application='Blender')
        self.assertTrue(mock_save.called)
        self.assertTrue(mock_read.called)
        self.assertEqual(cfg.job_type, "Blender")

        cfg = Configuration(data_path=self.test_dir, application=None)
        self.assertEqual(cfg.job_type, "Blender")

        with self.assertRaises(InvalidConfigException):
            Configuration(application='TestApp', default=True)
        with self.assertRaises(InvalidConfigException):
            Configuration(application=42, default=True)

    @mock.patch.object(Configuration, '_check_directory')
    @mock.patch.object(Configuration, '_configure_logging')
    @mock.patch.object(Configuration, '_set_logging_level')
    @mock.patch.object(Configuration, 'save_config')
    @mock.patch.object(batch_apps.config.os.path, 'isfile')
    def test_config_read_defaults(self,
                                  mock_file,
                                  mock_save,
                                  mock_level,
                                  mock_logging,
                                  mock_dir):
        """Test read"""

        mock_dir.return_value = True
        mock_logging.return_value = logging.getLogger("read_defaults")
        mock_file.return_value = True

        cfg = Configuration(data_path=self.test_dir, datadir="")
        self.assertFalse(mock_save.called)
        mock_dir.assert_called_with(self.test_dir)
        mock_file.assert_called_with(
            os.path.join(self.test_dir, "batch_apps.ini"))

        self.assertEqual(cfg.job_type, "Blender")

    @mock.patch.object(batch_apps.config.os.path, 'isdir')
    @mock.patch.object(batch_apps.config.os, 'mkdir')
    @mock.patch.object(batch_apps.config.os, 'remove')
    @mock.patch(BUILTIN_OPEN)
    def test_config_check_directory_a(self,
                                      mock_open,
                                      mock_rem,
                                      mock_mkdir,
                                      mock_isdir):
        """Test _check_directory"""

        cfg = mock.create_autospec(Configuration)
        cfg._dir = "BatchAppsData"

        mock_isdir.return_value = True
        check = Configuration._check_directory(cfg, "c:\\my_dir")
        self.assertFalse(mock_mkdir.called)

        mock_isdir.return_value = False
        check = Configuration._check_directory(cfg, "c:\\my_dir")
        mock_isdir.assert_called_with("c:\\my_dir\\BatchAppsData")
        mock_mkdir.assert_called_with("c:\\my_dir\\BatchAppsData")
        mock_open.assert_called_with("c:\\my_dir\\BatchAppsData\\gb_test", 'w')
        mock_rem.assert_called_with("c:\\my_dir\\BatchAppsData\\gb_test")
        self.assertTrue(check)

    @mock.patch.object(batch_apps.config.os.path, 'isdir')
    @mock.patch.object(batch_apps.config.os, 'mkdir')
    @mock.patch.object(batch_apps.config.os, 'remove')
    @mock.patch(BUILTIN_OPEN)
    def test_config_check_directory_b(self,
                                      mock_open,
                                      mock_rem,
                                      mock_mkdir,
                                      mock_isdir):
        """Test _check_directory"""

        cfg = mock.create_autospec(Configuration)
        cfg._dir = "BatchAppsData"
        mock_isdir.return_value = False

        mock_mkdir.side_effect = OSError("boom!")
        check = Configuration._check_directory(cfg, "c:\\my_dir")
        self.assertFalse(mock_open.called)
        self.assertFalse(mock_rem.called)
        self.assertFalse(check)

        mock_isdir.return_value = True
        mock_open.side_effect = OSError("oops!")
        check = Configuration._check_directory(cfg, "c:\\my_dir")
        self.assertTrue(mock_open.called)
        self.assertFalse(mock_rem.called)
        self.assertFalse(check)

    @mock.patch.object(batch_apps.config.logging, 'Formatter')
    @mock.patch.object(batch_apps.config.logging, 'StreamHandler')
    @mock.patch.object(batch_apps.config.logging, 'FileHandler')
    @mock.patch.object(batch_apps.config.logging, 'getLogger')
    @mock.patch.object(batch_apps.config.os.path, 'isfile')
    @mock.patch.object(batch_apps.config.os.path, 'getsize')
    @mock.patch.object(batch_apps.config.shutil, 'move')
    def test_config_configure_logging_a(self,
                                        mock_move,
                                        mock_size,
                                        mock_isfile,
                                        mock_logger,
                                        mock_file,
                                        mock_stream,
                                        mock_format):
        """Test _configure_logging"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._config = _cfg
        mock_logger.return_value = logging.getLogger("configure_logging_a")
        cfg._write_file = True
        mock_isfile.return_value = True
        mock_size.return_value = 20485760
        Configuration._configure_logging(cfg, self.test_dir)
        self.assertTrue(mock_format.called)
        self.assertTrue(mock_move.called)
        self.assertTrue(mock_size.called)
        mock_file.assert_called_with(
            os.path.join(self.test_dir, "batch_apps.log"))

    @mock.patch.object(batch_apps.config.logging, 'Formatter')
    @mock.patch.object(batch_apps.config.logging, 'StreamHandler')
    @mock.patch.object(batch_apps.config.logging, 'FileHandler')
    @mock.patch.object(batch_apps.config.logging, 'getLogger')
    @mock.patch.object(batch_apps.config.os.path, 'isfile')
    @mock.patch.object(batch_apps.config.os.path, 'getsize')
    @mock.patch.object(batch_apps.config.shutil, 'move')
    def test_config_configure_logging_b(self,
                                        mock_move,
                                        mock_size,
                                        mock_isfile,
                                        mock_logger,
                                        mock_file,
                                        mock_stream,
                                        mock_format):
        """Test _configure_logging"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._config = _cfg
        cfg._write_file = True
        mock_logger.return_value = logging.getLogger("configure_logging_b")
        mock_isfile.return_value = False

        Configuration._configure_logging(cfg, self.test_dir)
        self.assertFalse(mock_size.called)
        self.assertFalse(mock_move.called)
        self.assertFalse(mock_file.called)

    @mock.patch.object(batch_apps.config.logging, 'Formatter')
    @mock.patch.object(batch_apps.config.logging, 'StreamHandler')
    @mock.patch.object(batch_apps.config.logging, 'FileHandler')
    @mock.patch.object(batch_apps.config.logging, 'getLogger')
    @mock.patch.object(batch_apps.config.os.path, 'isfile')
    @mock.patch.object(batch_apps.config.os.path, 'getsize')
    @mock.patch.object(batch_apps.config.shutil, 'move')
    def test_config_configure_logging_c(self,
                                        mock_move,
                                        mock_size,
                                        mock_isfile,
                                        mock_logger,
                                        mock_file,
                                        mock_stream,
                                        mock_format):
        """Test _configure_logging"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._config = _cfg
        mock_logger.return_value = logging.getLogger("configure_logging_c")
        cfg._write_file = False

        Configuration._configure_logging(cfg, self.test_dir)
        self.assertFalse(mock_file.called)
        self.assertFalse(mock_size.called)

    def test_config_set_logging_level(self):
        """Test _set_logging_level"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        _cfg.add_section("Logging")
        cfg._config = _cfg
        cfg._log = logging.getLogger("set_logging_level")

        lev = Configuration._set_logging_level(cfg, 10)
        self.assertEqual(lev, 'DEBUG')
        self.assertEqual(_cfg.get("Logging", "level"), 10)
        self.assertEqual(cfg._log.level, 10)

        lev = Configuration._set_logging_level(cfg, "deBug")
        self.assertEqual(lev, 'DEBUG')
        self.assertEqual(_cfg.get("Logging", "level"), 10)
        self.assertEqual(cfg._log.level, 10)

        for i in [23, "test", None, 0, "20"]:
            lev = Configuration._set_logging_level(cfg, i)
            self.assertEqual(lev, 'WARNING')
            self.assertEqual(_cfg.get("Logging", "level"), 30)
            self.assertEqual(cfg._log.level, 30)

    @mock.patch.object(Configuration, 'save_config')
    def test_config_set_default_application(self, mock_save):
        """Test set_default_application"""

        _cfg = configparser.RawConfigParser()
        _cfg.read(os.path.join(self.test_dir, "batch_apps.ini"))
        cfg = mock.create_autospec(Configuration)
        cfg._config = _cfg
        cfg.job_type = "Test"
        cfg._write_file = True

        Configuration.set_default_application(cfg)
        self.assertFalse(cfg._config.has_option('Blender', 'default_app'))
        self.assertTrue(cfg._config.has_option('Test', 'default_app'))

        cfg.job_type = "Test"
        Configuration.set_default_application(cfg)
        self.assertFalse(cfg._config.has_option('Blender', 'default_app'))
        self.assertTrue(cfg._config.has_option('Test', 'default_app'))

    @mock.patch(BUILTIN_OPEN)
    def test_config_save_config(self, mock_open):
        """Test save_config"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._config = _cfg
        cfg._write_file = False
        cfg._cfg_file = "my_file.ini"
        cfg._log = logging.getLogger("save_config")
        save = Configuration.save_config(cfg)
        self.assertFalse(save)

        cfg._write_file = True
        save = Configuration.save_config(cfg)
        mock_open.assert_called_with("my_file.ini", 'w')
        self.assertTrue(save)

        mock_open.side_effect = OSError("test")
        save = Configuration.save_config(cfg)
        self.assertFalse(save)

    @mock.patch.object(batch_apps.config.os, 'remove')
    @mock.patch.object(batch_apps.config.Configuration, 'save_config')
    def test_config_clear_config(self, mock_save, mock_rem):
        """Test clear_config"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("clear_config")
        cfg._config = _cfg
        cfg._write_file = False
        cfg._cfg_file = "my_file.ini"

        clr = Configuration.clear_config(cfg)
        self.assertTrue(clr)

        mock_rem.side_effect = OSError("Boom!")
        clr = Configuration.clear_config(cfg)
        self.assertFalse(clr)

    def test_config_endpoint(self):
        """Test endpoint"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section('TestApp')
        _cfg.set('TestApp', 'endpoint', 'http://test')
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("endpoint")
        cfg._config = _cfg
        cfg.job_type = "SomeApp"

        with self.assertRaises(InvalidConfigException):
            Configuration.endpoint(cfg)
        with self.assertRaises(InvalidConfigException):
            Configuration.endpoint(cfg, "test")

        cfg.job_type = "TestApp"
        ept = Configuration.endpoint(cfg)
        self.assertEqual(_cfg.get('TestApp', 'endpoint'), 'http://test')
        self.assertEqual(ept, 'http://test')

        ept = Configuration.endpoint(cfg, "http://new_test")
        self.assertEqual(_cfg.get('TestApp', 'endpoint'), 'http://new_test')
        self.assertEqual(ept, 'http://new_test')

    def test_config_logging_level(self):
        """Test logging_level"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("logging_level")
        cfg._config = _cfg

        with self.assertRaises(InvalidConfigException):
            Configuration.logging_level(cfg)

        _cfg.add_section('Logging')
        _cfg.set('Logging', 'level', '30')
        ept = Configuration.logging_level(cfg)
        self.assertEqual(ept, 'WARNING')

        ept = Configuration.logging_level(cfg, None)
        cfg._set_logging_level.assert_called_with("None")

        ept = Configuration.logging_level(cfg, "warning")
        cfg._set_logging_level.assert_called_with("warning")

    def test_config_application(self):
        """Test application"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("application")
        cfg._config = _cfg
        cfg.job_type = "TestApp"

        app = Configuration.application(cfg)
        self.assertEqual(app, cfg.job_type)

        _cfg.add_section('TestApp2')
        with self.assertRaises(InvalidConfigException):
            Configuration.application(cfg, 'DifferentApp')

        app = Configuration.application(cfg, "TestApp2")
        self.assertEqual(app, 'TestApp2')
        self.assertEqual(cfg.job_type, 'TestApp2')

    def test_config_applications(self):
        """Test applications"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("Logging")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("applications")
        cfg._config = _cfg

        apps = Configuration.applications(cfg)
        self.assertEqual(apps, [])

        _cfg.add_section("Blender")
        _cfg.add_section("NewTestApp")
        apps = Configuration.applications(cfg)
        self.assertEqual(sorted(apps), sorted(['Blender', 'NewTestApp']))

    def test_config_default_params(self):
        """Test default_params"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("default_params")
        cfg._config = _cfg
        cfg.job_type = "TestApp"

        params = Configuration.default_params(cfg)
        self.assertEqual(params, {})

        cfg._config.set("TestApp", "1", "teST")
        cfg._config.set("TestApp", "2", None)
        cfg._config.set("TestApp", "3", [])

        params = Configuration.default_params(cfg)
        self.assertEqual(params, {'1':'teST', '2':None, '3':[]})

    def test_config_add_application(self):
        """Test add_application"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("add_application")
        cfg._config = _cfg

        Configuration.add_application(cfg,
                                      "TestApp",
                                      "http://endpoint",
                                      "test_id")
        self.assertEqual(cfg._config.sections(), ['TestApp'])
        self.assertEqual(dict(cfg._config.items('TestApp')),
                         {'endpoint':"http://endpoint", 'client_id':'test_id'})

        Configuration.add_application(cfg,
                                      "TestApp2",
                                      "http://endpoint",
                                      "test_id",
                                      a="1",
                                      b=2,
                                      c=None)
        self.assertEqual(cfg._config.sections(), ['TestApp', 'TestApp2'])
        self.assertEqual(dict(cfg._config.items('TestApp2')),
                         {'endpoint':"http://endpoint",
                          'client_id':'test_id',
                          'a':'1',
                          'b':2,
                          'c':None})

    def test_config_set(self):
        """Test set"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("config_set")
        cfg._config = _cfg
        cfg.job_type = "TestApp"

        Configuration.set(cfg, "key", "value")
        self.assertEqual(dict(cfg._config.items('TestApp')), {'key':'value'})

        cfg.job_type = "TestApp2"
        with self.assertRaises(InvalidConfigException):
            Configuration.set(cfg, "key", "value")

    def test_config_get(self):
        """Test get"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("config_get")
        cfg._config = _cfg
        cfg.job_type = "TestApp2"

        param = Configuration.get(cfg, "endpoint")
        self.assertIsNone(param)

        cfg.job_type = "TestApp"
        param = Configuration.get(cfg, "endpoint")
        self.assertIsNone(param)

        cfg._config.set("TestApp", "endpoint", "http://test")
        param = Configuration.get(cfg, "endpoint")
        self.assertEqual(param, "http://test")

        param = Configuration.get(cfg, 42)
        self.assertIsNone(param)

    def test_config_remove(self):
        """Test remove"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("config_remove")
        cfg._config = _cfg
        cfg.job_type = "TestApp"

        with self.assertRaises(ValueError):
            Configuration.remove(cfg, "TestApp")

        rem = Configuration.remove(cfg, "TestApp2")
        self.assertFalse(rem)

        rem = Configuration.remove(cfg, 42)
        self.assertFalse(rem)

        rem = Configuration.remove(cfg, None)
        self.assertFalse(rem)

        cfg._config.set("TestApp", "1", 1)
        cfg._config.set("TestApp", "2", 2)
        cfg._config.set("TestApp", "endpoint", 3)

        rem = Configuration.remove(cfg, "1")
        self.assertTrue(rem)
        self.assertEqual(dict(cfg._config.items('TestApp')),
                         {'2':2, 'endpoint':3})

        rem = Configuration.remove(cfg, "endpoint")
        self.assertFalse(rem)
        self.assertEqual(dict(cfg._config.items('TestApp')),
                         {'2':2, 'endpoint':3})

        _cfg.add_section("Logging")
        rem = Configuration.remove(cfg, "Logging")
        self.assertFalse(rem)

        cfg.job_type = "TestApp2"
        rem = Configuration.remove(cfg, "TestApp")
        self.assertTrue(rem)
        self.assertEqual(cfg._config.sections(), ['Logging'])

    def test_config_aad_config(self):
        """Test aad_config"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("aad")
        cfg._config = _cfg

        with self.assertRaises(InvalidConfigException):
            Configuration.aad_config(cfg)

        _cfg.add_section("Authentication")
        aad = Configuration.aad_config(cfg)
        self.assertEqual(aad, {})
