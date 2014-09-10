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
"""Unit tests for Credentials and AzureOAuth"""

import sys

if sys.version_info[:2] <= (2, 7, ):
    import unittest2 as unittest
else:
    import unittest

if sys.version_info[:2] >= (3, 3, ):
    from unittest import mock
else:
    import mock

import requests_oauthlib
import logging

from batch_apps import (
    AzureOAuth,
    Credentials,
    Configuration)

from batch_apps.exceptions import (
    AuthenticationException,
    InvalidConfigException)


# pylint: disable=W0212
class TestAzureOAuth(unittest.TestCase):
    """Unit tests for AzureOAuth"""

    @mock.patch('batch_apps.credentials.requests_oauthlib')
    def test_azureoauth_setup_session(self, mock_requests):
        """Test _setup_session"""

        with self.assertRaises(InvalidConfigException):
            AzureOAuth._setup_session({}, None)

        AzureOAuth._setup_session({'token_uri':'4'},
                                  {'redirect_uri':'1', 'client_id':'3'},
                                  None)
        mock_requests.OAuth2Session.assert_called_with("3",
                                                       redirect_uri="http://1")

        AzureOAuth.session = None
        AzureOAuth._setup_session({'token_uri':'4'},
                                  {'redirect_uri':'1', 'client_id':'3'},
                                  state='4')
        mock_requests.OAuth2Session.assert_called_with("3",
                                                       redirect_uri="http://1",
                                                       state='4')
        mock_requests.reset_mock()
        AzureOAuth._setup_session({'token_uri':'4'},
                                  {'redirect_uri':'1', 'client_id':'3'},
                                  state='4')
        self.assertFalse(mock_requests.OAuth2Session.called)
        AzureOAuth.session = None

    @mock.patch('batch_apps.credentials.Credentials')
    @mock.patch('batch_apps.credentials.Configuration')
    def test_azureoauth_get_session(self, mock_config, mock_credentials):
        """Test get_session"""

        mock_config.return_value = mock.create_autospec(Configuration)
        mock_config.return_value.get.return_value = "test"
        AzureOAuth.get_session()
        self.assertTrue(mock_config.called)
        mock_credentials.assert_called_with(mock_config.return_value, "test")
        mock_config.reset_mock()

        mock_cfg = mock.create_autospec(Configuration)
        AzureOAuth.get_session(config=mock_cfg)
        self.assertFalse(mock_config.called)
        mock_credentials.assert_called_with(mock_cfg, mock.ANY)

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch.object(AzureOAuth, '_setup_session')
    def test_azureoauth_get_authorization_url(self, mock_setup, mock_config):
        """Test get_authorization_url"""

        AzureOAuth.session = mock.create_autospec(
            requests_oauthlib.OAuth2Session)

        mock_config.aad_config.return_value = {'auth_uri':'1', 'resource':'2'}
        with self.assertRaises(AuthenticationException):
            AzureOAuth.get_authorization_url()

        AzureOAuth.session.authorization_url.return_value = ("a", "b")
        url, state = AzureOAuth.get_authorization_url()
        self.assertTrue(mock_config.called)
        self.assertIsNotNone(url)
        self.assertIsNotNone(state)

        mock_config.reset_mock()
        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_authorization_url(1)

        self.assertFalse(mock_config.called)
        AzureOAuth.session = None

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch.object(AzureOAuth, '_setup_session')
    @mock.patch('batch_apps.credentials.Credentials')
    def test_get_authorization_token(self,
                                     mock_creds,
                                     mock_setup,
                                     mock_config):
        """Test get_authorization_token"""

        AzureOAuth.session = mock.create_autospec(
            requests_oauthlib.OAuth2Session)

        mock_config.aad_config.return_value = {'redirect_uri':'1',
                                               'redirect_port':'2',
                                               'token_uri':'3'}
        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_authorization_token("test", config="test")

        AzureOAuth.session.fetch_token.return_value = {}
        authed = AzureOAuth.get_authorization_token("test")
        mock_setup.assert_called_with(mock.ANY, mock.ANY, state=None)
        mock_creds.assert_called_with(mock.ANY, mock.ANY, token={})
        self.assertIsNotNone(authed)

        authed = AzureOAuth.get_authorization_token("test", state="test")
        mock_setup.assert_called_with(mock.ANY, mock.ANY, state="test")

    @mock.patch('batch_apps.credentials.requests_oauthlib')
    @mock.patch('batch_apps.credentials.BackendApplicationClient')
    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch('batch_apps.credentials.Credentials')
    def test_get_principal_token(self,
                                 mock_creds,
                                 mock_config,
                                 mock_client,
                                 mock_req):
        """Test get_principal_token"""

        mock_session = mock.create_autospec(
            requests_oauthlib.OAuth2Session)

        mock_req.OAuth2Session.return_value = mock_session
        mock_config.aad_config.return_value = {'token_uri':'http://common',
                                               'resource':'test'}

        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_principal_token(mock_config)
        mock_config.aad_config.return_value = {'service_principal':'1',
                                               'service_principal_key':'3',
                                               'token_uri':'http://common',
                                               'resource':'test'}

        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_principal_token(mock_config)
        mock_config.aad_config.return_value = {'service_principal':None,
                                               'service_principal_key':None,
                                               'token_uri':'http://common',
                                               'resource':'test'}

        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_principal_token(mock_config)
        mock_config.aad_config.return_value = {'service_principal':'1@2',
                                               'service_principal_key':'3',
                                               'token_uri':'common',
                                               'resource':'test'}

        AzureOAuth.get_principal_token(mock_config)
        mock_client.assert_called_with("1")
        mock_req.OAuth2Session.assert_called_with("1", client=mock.ANY)
        mock_session.fetch_token.assert_called_with(
            "https://2",
            client_id='1',
            resource='https://test',
            client_secret='3',
            response_type='client_credentials')


# pylint: disable=W0212
class TestCredentials(unittest.TestCase):
    """Unit tests for Credentials"""

    @mock.patch('batch_apps.credentials.Configuration')
    @mock.patch.object(Credentials, 'get_stored_auth')
    @mock.patch.object(Credentials, 'store_auth')
    @mock.patch.object(Credentials, 'get_session')
    def test_credentials_create(self,
                                mock_get_session,
                                mock_store_auth,
                                mock_get_stored_auth,
                                mock_config):
        """Test credentials object"""

        with self.assertRaises(InvalidConfigException):
            Credentials(None, None)

        Credentials(mock_config, "test", token={'token_type':'1',
                                                'access_token':'2'})
        mock_store_auth.assert_called_with({'token_type':'1',
                                            'access_token':'2'})
        self.assertTrue(mock_get_session.called)
        self.assertFalse(mock_get_stored_auth.called)

        mock_get_stored_auth.return_value = ({'token_type':'3',
                                              'access_token':'4'})
        Credentials(mock_config, "testId")
        mock_store_auth.assert_called_with({'token_type':'3',
                                            'access_token':'4'})
        self.assertTrue(mock_get_session.called)
        self.assertTrue(mock_get_stored_auth.called)

    @mock.patch('batch_apps.credentials.keyring')
    def test_credentials_store_auth(self, mock_keyring):
        """Test store_auth"""

        creds = mock.create_autospec(Credentials)
        creds._log = logging.getLogger()
        creds._id = 'test'
        Credentials.store_auth(creds, {'token_type':'1',
                                       'access_token':'2'})

        mock_keyring.set_password.assert_called_with("AzureBatchApps",
                                                     "test",
                                                     str({'token_type':'1',
                                                          'access_token':'2'}))

    @mock.patch('batch_apps.credentials.keyring')
    def test_credentials_clear_auth(self, mock_keyring):
        """Test clear_auth"""

        creds = mock.create_autospec(Credentials)
        creds._log = logging.getLogger()
        creds._id = 'test'
        Credentials.clear_auth(creds)

        mock_keyring.delete_password.assert_called_with("AzureBatchApps",
                                                        "test")

    @mock.patch('batch_apps.credentials.keyring')
    def test_credentials_get_stored_auth(self, mock_keyring):
        """Test get_stored_auth"""

        creds = mock.create_autospec(Credentials)
        creds._log = logging.getLogger()
        creds._id = 'test'
        mock_keyring.get_password.return_value = None

        with self.assertRaises(AuthenticationException):
            Credentials.get_stored_auth(creds)
        mock_keyring.get_password.assert_called_with("AzureBatchApps",
                                                     "test")

        mock_keyring.get_password.return_value = str({'token_type':'1',
                                                      'access_token':'2'})
        Credentials.get_stored_auth(creds)
        mock_keyring.get_password.assert_called_with("AzureBatchApps", "test")

    @mock.patch('batch_apps.credentials.requests_oauthlib')
    def test_credentials_get_session(self, mock_requests):
        """Test get_session"""

        creds = mock.create_autospec(Credentials)
        creds._id = '1'
        creds.cfg = {'resource':'2', 'token_uri':'3'}
        creds.token = {'expires_at':'1',
                       'expires_in':'2',
                       'refresh_token':"test"}
        creds._log = logging.getLogger()

        Credentials.get_session(creds)
        mock_requests.OAuth2Session.assert_called_with(
            '1',
            token=creds.token,
            auto_refresh_url='https://3',
            auto_refresh_kwargs={'client_id':'1', 'resource':'https://2'},
            token_updater=creds.store_auth)

        creds.token = {'expires_at':'1', 'expires_in':'2'}
        Credentials.get_session(creds)
        mock_requests.OAuth2Session.assert_called_with('1',
                                                       token=creds.token)

