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
"""Unit tests for Configuration"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    from builtins import open
    BUILTIN_OPEN = "builtins.open"
except ImportError:
    BUILTIN_OPEN = "__builtin__.open"

import os
import logging
import batchapps.config
from batchapps import Configuration
from batchapps.exceptions import InvalidConfigException


# pylint: disable=W0212
class TestConfiguration(unittest.TestCase):
    """Unit tests for Configuration"""

    def setUp(self):
        self.userdir = os.path.expanduser("~")
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.test_dir = os.path.join(self.cwd, "test_assets", "test_config")
        self.use_test_files = os.path.exists(self.test_dir)
        return super(TestConfiguration, self).setUp()

    @mock.patch.object(Configuration, '_check_directory')
    @mock.patch.object(Configuration, '_configure_logging')
    @mock.patch.object(Configuration, '_set_logging_level')
    @mock.patch.object(Configuration, 'save_config')
    @mock.patch.object(batchapps.config.os.path, 'isfile')
    @mock.patch.object(batchapps.config.configparser.RawConfigParser, 'read')
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
        self.assertEqual(cfg.jobtype, "Blender")
        self.assertEqual(cfg.job_type, "Blender")

        cfg = Configuration(data_path=self.test_dir, jobtype=None)
        self.assertEqual(cfg.jobtype, "Blender")
        self.assertEqual(cfg.job_type, "Blender")

        with self.assertRaises(InvalidConfigException):
            Configuration(application='TestApp', default=True)
        with self.assertRaises(InvalidConfigException):
            Configuration(jobtype=42, default=True)

    @mock.patch.object(Configuration, '_check_directory')
    @mock.patch.object(Configuration, '_configure_logging')
    @mock.patch.object(Configuration, '_set_logging_level')
    @mock.patch.object(Configuration, 'save_config')
    @mock.patch.object(batchapps.config.os.path, 'isfile')
    def test_config_read_defaults(self,
                                  mock_file,
                                  mock_save,
                                  mock_level,
                                  mock_logging,
                                  mock_dir):
        """Test read"""
        if not self.use_test_files:
            self.skipTest("No test files present")
        mock_dir.return_value = True
        mock_logging.return_value = logging.getLogger("read_defaults")
        mock_file.return_value = True

        cfg = Configuration(data_path=self.test_dir, datadir="")
        self.assertFalse(mock_save.called)
        mock_dir.assert_called_with(self.test_dir)
        mock_file.assert_called_with(
            os.path.join(self.test_dir, "batch_apps.ini"))

        self.assertEqual(cfg.jobtype, "Blender")

    @mock.patch.object(batchapps.config.os.path, 'isdir')
    @mock.patch.object(batchapps.config.os, 'mkdir')
    @mock.patch.object(batchapps.config.os, 'remove')
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
        mock_open.assert_called_with("c:\\my_dir\\BatchAppsData\\aba_test", 'w')
        mock_rem.assert_called_with("c:\\my_dir\\BatchAppsData\\aba_test")
        self.assertTrue(check)

    @mock.patch.object(batchapps.config.os.path, 'isdir')
    @mock.patch.object(batchapps.config.os, 'mkdir')
    @mock.patch.object(batchapps.config.os, 'remove')
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

    @mock.patch.object(batchapps.config.logging, 'Formatter')
    @mock.patch.object(batchapps.config.logging, 'StreamHandler')
    @mock.patch.object(batchapps.config.logging, 'FileHandler')
    @mock.patch.object(batchapps.config.logging, 'getLogger')
    @mock.patch.object(batchapps.config.os.path, 'isfile')
    @mock.patch.object(batchapps.config.os.path, 'getsize')
    @mock.patch.object(batchapps.config.shutil, 'move')
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

    @mock.patch.object(batchapps.config.logging, 'Formatter')
    @mock.patch.object(batchapps.config.logging, 'StreamHandler')
    @mock.patch.object(batchapps.config.logging, 'FileHandler')
    @mock.patch.object(batchapps.config.logging, 'getLogger')
    @mock.patch.object(batchapps.config.os.path, 'isfile')
    @mock.patch.object(batchapps.config.os.path, 'getsize')
    @mock.patch.object(batchapps.config.shutil, 'move')
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

    @mock.patch.object(batchapps.config.logging, 'Formatter')
    @mock.patch.object(batchapps.config.logging, 'StreamHandler')
    @mock.patch.object(batchapps.config.logging, 'FileHandler')
    @mock.patch.object(batchapps.config.logging, 'getLogger')
    @mock.patch.object(batchapps.config.os.path, 'isfile')
    @mock.patch.object(batchapps.config.os.path, 'getsize')
    @mock.patch.object(batchapps.config.shutil, 'move')
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
        """Test deprecated method set_default_application"""

        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("set_default_application")
        Configuration.set_default_application(cfg)
        self.assertTrue(cfg.set_default_jobtype.called)

    @mock.patch.object(Configuration, 'save_config')
    def test_config_set_default_jobtype(self, mock_save):
        """Test set_default_jobtype"""

        if not self.use_test_files:
            self.skipTest("No test files present")
      
        _cfg = configparser.RawConfigParser()
        _cfg.read(os.path.join(self.test_dir, "batch_apps.ini"))
        cfg = mock.create_autospec(Configuration)
        cfg._config = _cfg
        cfg.jobtype = "Test"
        cfg._write_file = True
        cfg._log = logging.getLogger("set_default_jobtype")

        Configuration.set_default_jobtype(cfg)
        self.assertFalse(cfg._config.has_option('Blender', 'default_jobtype'))
        self.assertTrue(cfg._config.has_option('Test', 'default_jobtype'))

        cfg.jobtype = "Test"
        Configuration.set_default_jobtype(cfg)
        self.assertFalse(cfg._config.has_option('Blender', 'default_jobtype'))
        self.assertTrue(cfg._config.has_option('Test', 'default_jobtype'))

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

    @mock.patch.object(batchapps.config.os, 'remove')
    @mock.patch.object(batchapps.config.Configuration, 'save_config')
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
        cfg.jobtype = "SomeApp"

        with self.assertRaises(InvalidConfigException):
            Configuration.endpoint(cfg)

        _cfg.add_section('Authentication')
        with self.assertRaises(InvalidConfigException):
            Configuration.endpoint(cfg)

        cfg.jobtype = "TestApp"
        ept = Configuration.endpoint(cfg)
        self.assertEqual(_cfg.get('TestApp', 'endpoint'), 'http://test')
        self.assertEqual(ept, 'test')

        ept = Configuration.endpoint(cfg, "https://new_test/")
        self.assertEqual(_cfg.get('TestApp', 'endpoint'), 'http://test')
        self.assertEqual(_cfg.get('Authentication', 'endpoint'), 'https://new_test/')
        self.assertEqual(ept, 'new_test/')

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
        """Test depcrecated method application"""
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("application")
        Configuration.application(cfg)
        self.assertTrue(cfg.current_jobtype.called)

        Configuration.application(cfg, "test")
        cfg.current_jobtype.assert_called_with("test")

    def test_config_current_jobtype(self):
        """Test current_jobtype"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("jobtype")
        cfg._config = _cfg
        cfg.jobtype = "TestApp"

        app = Configuration.current_jobtype(cfg)
        self.assertEqual(app, cfg.jobtype)

        _cfg.add_section('TestApp2')
        with self.assertRaises(InvalidConfigException):
            Configuration.current_jobtype(cfg, 'DifferentApp')

        app = Configuration.current_jobtype(cfg, "TestApp2")
        self.assertEqual(app, 'TestApp2')
        self.assertEqual(cfg.jobtype, 'TestApp2')
        self.assertEqual(cfg.job_type, 'TestApp2')

    def test_config_applications(self):
        """Test deprecated method applications"""
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("applications")
        Configuration.applications(cfg)
        self.assertTrue(cfg.list_jobtypes.called)

    def test_config_list_jobtypes(self):
        """Test list_jobtypes"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("Logging")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("list_jobtypes")
        cfg._config = _cfg

        with self.assertRaises(InvalidConfigException):
            apps = Configuration.list_jobtypes(cfg)

        _cfg.add_section("Authentication")
        apps = Configuration.list_jobtypes(cfg)
        self.assertEqual(apps, [])

        _cfg.add_section("Blender")
        _cfg.add_section("NewTestApp")
        apps = Configuration.list_jobtypes(cfg)
        self.assertEqual(sorted(apps), sorted(['Blender', 'NewTestApp']))

    def test_config_default_params(self):
        """Test default_params"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("default_params")
        cfg._config = _cfg
        cfg.jobtype = "TestApp"

        params = Configuration.default_params(cfg)
        self.assertEqual(params, {})

        cfg._config.set("TestApp", "1", "teST")
        cfg._config.set("TestApp", "2", None)
        cfg._config.set("TestApp", "3", [])

        params = Configuration.default_params(cfg)
        self.assertEqual(params, {'1':'teST', '2':None, '3':[]})

    def test_config_add_application(self):
        """Testing deprecated method add_application"""

        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("add_application")
        Configuration.add_application(cfg, "1", "2", three="3")
        cfg.add_jobtype.assert_called_with("1", three="3")

    def test_config_add_jobtype(self):
        """Test add_jobtype"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("add_jobtype")
        cfg._config = _cfg

        Configuration.add_jobtype(cfg,
                                  "TestApp",
                                  "http://endpoint",
                                  "test_id")
        self.assertEqual(cfg._config.sections(), ['TestApp'])
        self.assertEqual(dict(cfg._config.items('TestApp')), {})

        Configuration.add_jobtype(cfg,
                                  "TestApp2",
                                  "test_id",
                                  a="1",
                                  b=2,
                                  c=None)
        self.assertEqual(cfg._config.sections(), ['TestApp', 'TestApp2'])
        self.assertEqual(dict(cfg._config.items('TestApp2')),
                         {'a':'1',
                          'b':2,
                          'c':None})

    def test_config_set(self):
        """Test set"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("config_set")
        cfg._config = _cfg
        cfg.jobtype = "TestApp"

        Configuration.set(cfg, "key", "value")
        self.assertEqual(dict(cfg._config.items('TestApp')), {'key':'value'})

        cfg.jobtype = "TestApp2"
        with self.assertRaises(InvalidConfigException):
            Configuration.set(cfg, "key", "value")

    def test_config_get(self):
        """Test get"""

        _cfg = configparser.RawConfigParser()
        _cfg.add_section("TestApp")
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("config_get")
        cfg._config = _cfg
        cfg.jobtype = "TestApp2"

        param = Configuration.get(cfg, "endpoint")
        self.assertIsNone(param)

        cfg.jobtype = "TestApp"
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
        cfg.jobtype = "TestApp"

        rem = Configuration.remove(cfg, "TestApp")
        self.assertFalse(rem)

        rem = Configuration.remove(cfg, "TestApp2")
        self.assertFalse(rem)

        rem = Configuration.remove(cfg, 42)
        self.assertFalse(rem)

        rem = Configuration.remove(cfg, None)
        self.assertFalse(rem)

        cfg._config.set("TestApp", "1", 1)
        cfg._config.set("TestApp", "2", 2)

        rem = Configuration.remove(cfg, "1")
        self.assertTrue(rem)
        self.assertEqual(dict(cfg._config.items('TestApp')), {'2':2})

        _cfg.add_section("Logging")
        rem = Configuration.remove(cfg, "Logging")
        self.assertFalse(rem)

        cfg.jobtype = "TestApp2"
        rem = Configuration.remove(cfg, "TestApp")
        self.assertTrue(rem)
        self.assertEqual(cfg._config.sections(), ['Logging'])

    def test_config_aad_config(self):
        """Test aad_config"""

        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("aad")
        cfg._config = _cfg
        cfg._reformat_config.return_value = {"a":1, "b":2}
        cfg._validate_auth = lambda a: dict(_cfg.items("Authentication"))

        with self.assertRaises(InvalidConfigException):
            Configuration.aad_config(cfg)

        _cfg.add_section("Authentication")
        aad = Configuration.aad_config(cfg)
        self.assertEqual(aad, {"a":1, "b":2})

        aad = Configuration.aad_config(cfg, client_id="a", tenant="b",
                                       endpoint="c")
        self.assertEqual(aad, {"a":1, "b":2, "client_id":"a", "tenant":"b",
                               "endpoint":"c"})
        _cfg.remove_section("Authentication")
        _cfg.add_section("Authentication")

        _cfg.set("Authentication", "root", "test")
        aad = Configuration.aad_config(cfg, key=3, redirect=4)
        self.assertEqual(aad, {"root":"test", "unattended_key":"3",
                               "redirect_uri":"4"})

        _cfg.remove_section("Authentication")
        _cfg.add_section("Authentication")
        _cfg.set("Authentication", "root", "test")
        
        aad = Configuration.aad_config(cfg, account=3)
        aad = Configuration.aad_config(cfg, account="test;test")
        aad = Configuration.aad_config(cfg, account="ClientID=abc;TenantID=xyz")
        self.assertEqual(aad, {"root":"test", "unattended_account":"ClientID=abc;TenantID=xyz"})

        _cfg.remove_section("Authentication")
        _cfg.add_section("Authentication")
        _cfg.set("Authentication", "root", "test")

        aad = Configuration.aad_config(cfg, account="ClientID=abc;TenantID=xyz",
                                       client_id="foo", tenant="bar")
        self.assertEqual(aad, {"root":"test", "client_id":"foo", "tenant":"bar",
                               "unattended_account":"ClientID=abc;TenantID=xyz"})

    def test_config_validate_auth(self):
        """Test validate_auth"""
        _cfg = configparser.RawConfigParser()
        cfg = mock.create_autospec(Configuration)
        cfg._invalid_data = lambda s: Configuration._invalid_data(cfg, s)
        _cfg.add_section("Authentication")
        cfg._config = _cfg
        
        with self.assertRaises(InvalidConfigException):
            Configuration._validate_auth(cfg, False)

        _cfg.set("Authentication", "auth_uri", "a")
        _cfg.set("Authentication", "resource", "b")
        _cfg.set("Authentication", "token_uri", "c")
        _cfg.set("Authentication", "endpoint", "d")
        _cfg.set("Authentication", "client_id", "e")
        _cfg.set("Authentication", "tenant", "f")
        _cfg.set("Authentication", "root", "g")
        _cfg.set("Authentication", "redirect_uri", "{redirect}")

        with self.assertRaises(InvalidConfigException):
            Configuration._validate_auth(cfg, False)

        _cfg.set("Authentication", "redirect_uri", "h")
        auth = Configuration._validate_auth(cfg, False)

        with self.assertRaises(InvalidConfigException):
            Configuration._validate_auth(cfg, True)

        _cfg.set("Authentication", "unattended_account", None)
        _cfg.set("Authentication", "unattended_key", "i")

        with self.assertRaises(InvalidConfigException):
            Configuration._validate_auth(cfg, True)

        _cfg.set("Authentication", "unattended_account", "j")
        auth = Configuration._validate_auth(cfg, True)

        _cfg.remove_option("Authentication", "redirect_uri")
        auth = Configuration._validate_auth(cfg, True)

    def test_config_reformat_config(self):
        """Test reformat_config"""

        old_cfg = configparser.RawConfigParser()
        old_cfg.add_section("Authentication")
        old_cfg.set("Authentication", "auth_uri",
                    "login.windows.net/common/oauth2/authorize")
        old_cfg.set("Authentication", "resource", "https://batchapps.core.windows.net/")
        old_cfg.set("Authentication", "token_uri", "login.windows.net/common/oauth2/token")
        
        old_cfg.add_section("TestJob")
        old_cfg.set("TestJob", "endpoint", "test.com")
        old_cfg.set("TestJob", "client_id", "abc")
        old_cfg.set("TestJob", "redirect_uri", "redirect.com")

        cfg = mock.create_autospec(Configuration)
        cfg._log = logging.getLogger("aad")
        cfg._config = old_cfg
        cfg.jobtype = "TestJob"

        aad = Configuration._reformat_config(
            cfg, dict(cfg._config.items("Authentication")))

        self.assertEqual(aad, {"endpoint":"test.com", "client_id":"abc",
                               "auth_uri":"/oauth2/authorize",
                               "root":"login.windows.net/",
                               "token_uri":"/oauth2/token",
                               "redirect_uri":"redirect.com",
                               "unattended_account":None,
                               "unattended_key":None,
                               "tenant":"common",
                               "resource":"https://batchapps.core.windows.net/"})

        old_cfg.set("Authentication", "service_principal", "")
        old_cfg.set("Authentication", "service_principal_key", "")

        aad = Configuration._reformat_config(
            cfg, dict(cfg._config.items("Authentication")))

        self.assertEqual(aad, {"endpoint":"test.com", "client_id":"abc",
                               "auth_uri":"/oauth2/authorize",
                               "root":"login.windows.net/",
                               "token_uri":"/oauth2/token",
                               "redirect_uri":"redirect.com",
                               "unattended_account":"",
                               "unattended_key":"",
                               "tenant":"common",
                               "resource":"https://batchapps.core.windows.net/"})

        old_cfg.set("Authentication", "service_principal_key", "%&#5$#")
        old_cfg.set("Authentication", "service_principal",
                    "ClientId=xyz;TenantId=test_account.onmicrosoft.com")

        aad = Configuration._reformat_config(
            cfg, dict(cfg._config.items("Authentication")))

        self.assertEqual(aad, {"endpoint":"test.com", "client_id":"abc",
                               "auth_uri":"/oauth2/authorize",
                               "root":"login.windows.net/",
                               "token_uri":"/oauth2/token",
                               "redirect_uri":"redirect.com",
                               "unattended_account":"ClientId=xyz;TenantId=test_account.onmicrosoft.com",
                               "unattended_key":"%&#5$#",
                               "tenant":"common",
                               "resource":"https://batchapps.core.windows.net/"})

