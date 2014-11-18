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
"""Unit tests for Credentials and AzureOAuth"""

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import requests_oauthlib
import logging

from batchapps import (
    AzureOAuth,
    Credentials,
    Configuration)

from batchapps.exceptions import (
    AuthenticationException,
    InvalidConfigException)


# pylint: disable=W0212
class TestAzureOAuth(unittest.TestCase):
    """Unit tests for AzureOAuth"""

    @mock.patch('batchapps.credentials.requests_oauthlib')
    def test_azureoauth_setup_session(self, mock_requests):
        """Test _setup_session"""

        AzureOAuth._setup_session({}, None)
        mock_requests.OAuth2Session.assert_called_with(
            None, redirect_uri="http://None")

        AzureOAuth.session = None
        AzureOAuth._setup_session({'redirect_uri':'1', 'client_id':'3'})
        mock_requests.OAuth2Session.assert_called_with("3",
                                                       redirect_uri="http://1")
        AzureOAuth.session = None
        AzureOAuth._setup_session({'redirect_uri':'1', 'client_id':'3'},
                                  state='2')
        mock_requests.OAuth2Session.assert_called_with("3",
                                                       redirect_uri="http://1",
                                                       state='2')
        mock_requests.reset_mock()
        AzureOAuth._setup_session({'redirect_uri':'1', 'client_id':'3'},
                                  state='4')
        self.assertFalse(mock_requests.OAuth2Session.called)
        AzureOAuth.session = None

    @mock.patch('batchapps.credentials.Credentials')
    @mock.patch('batchapps.credentials.Configuration')
    def test_azureoauth_get_session(self, mock_config, mock_credentials):
        """Test get_session"""

        mock_config.return_value = mock.create_autospec(Configuration)
        mock_config.return_value.aad_config.return_value = {'client_id':'abc'}
        AzureOAuth.get_session()
        self.assertTrue(mock_config.called)
        mock_credentials.assert_called_with(mock_config.return_value, 'abc')
        mock_config.reset_mock()

        mock_cfg = mock.create_autospec(Configuration)
        mock_cfg.aad_config.return_value = {'client_id':'abc'}
        AzureOAuth.get_session(config=mock_cfg)
        self.assertFalse(mock_config.called)
        mock_credentials.assert_called_with(mock_cfg, 'abc')

    @mock.patch('batchapps.credentials.Configuration')
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

    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch.object(AzureOAuth, '_setup_session')
    @mock.patch('batchapps.credentials.Credentials')
    def test_azureoauth_get_authorization_token(self,
                                     mock_creds,
                                     mock_setup,
                                     mock_config):
        """Test get_authorization_token"""

        AzureOAuth.session = mock.create_autospec(
            requests_oauthlib.OAuth2Session)

        mock_config.aad_config.return_value = {'root':'1/',
                                               'unattended_key':'3',
                                               'token_uri':'/auth',
                                               'resource':'test',
                                               'tenant':'common',
                                               'client_id':'abc'}

        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_authorization_token("test", config="test")

        AzureOAuth.session.fetch_token.return_value = {}
        authed = AzureOAuth.get_authorization_token("test")
        mock_setup.assert_called_with(mock.ANY, state=None)
        mock_creds.assert_called_with(mock.ANY, mock.ANY, token={})
        self.assertIsNotNone(authed)

        authed = AzureOAuth.get_authorization_token("test", state="test")
        mock_setup.assert_called_with(mock.ANY, state="test")

    @mock.patch.object(AzureOAuth, 'get_unattended_session')
    def test_azureoauth_get_principal_token(self, mock_token):
        """Test deprecated method get_principal_token"""

        AzureOAuth.get_principal_token()
        mock_token.assert_called_with(config=None)

        AzureOAuth.get_principal_token("hello")
        mock_token.assert_called_with(config="hello")

        AzureOAuth.get_principal_token(config="world")
        mock_token.assert_called_with(config="world")

    @mock.patch('batchapps.credentials.requests_oauthlib')
    @mock.patch('batchapps.credentials.BackendApplicationClient')
    @mock.patch('batchapps.credentials.Configuration')
    @mock.patch('batchapps.credentials.Credentials')
    def test_azureoauth_get_unattended_session(self,
                                 mock_creds,
                                 mock_config,
                                 mock_client,
                                 mock_req):
        """Test get_unattended_session"""

        mock_session = mock.create_autospec(
            requests_oauthlib.OAuth2Session)

        mock_req.OAuth2Session.return_value = mock_session
        mock_config.aad_config.return_value = {'root':'1/',
                                               'unattended_key':'3',
                                               'token_uri':'/auth',
                                               'resource':'test',
                                               'unattended_account':'abc'}

        with self.assertRaises(InvalidConfigException):
            AzureOAuth.get_unattended_session(mock_config)

        mock_config.aad_config.return_value['unattended_account'] = 'ClientID=abc;TenantID=common'
        AzureOAuth.get_unattended_session(mock_config)
        mock_client.assert_called_with("abc")
        mock_req.OAuth2Session.assert_called_with("abc", client=mock.ANY)
        mock_session.fetch_token.assert_called_with(
            "https://1/common/auth",
            client_id='abc',
            resource='https://test',
            client_secret='3',
            response_type='client_credentials')

        mock_config.aad_config.return_value = {'root':'http://1/',
                                               'unattended_key':'3',
                                               'token_uri':'/auth',
                                               'resource':'https://test',
                                               'unattended_account':'ClientID=abc;TenantID=common'}

        AzureOAuth.get_unattended_session(mock_config)
        mock_client.assert_called_with("abc")
        mock_req.OAuth2Session.assert_called_with("abc", client=mock.ANY)
        mock_session.fetch_token.assert_called_with(
            "https://1/common/auth",
            client_id='abc',
            resource='https://test',
            client_secret='3',
            response_type='client_credentials')


# pylint: disable=W0212
class TestCredentials(unittest.TestCase):
    """Unit tests for Credentials"""

    @mock.patch('batchapps.credentials.Configuration')
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

        with self.assertRaises(AuthenticationException):
            regression_test = Credentials(mock_config, "client_id")
        self.assertTrue(mock_get_stored_auth.called)
        mock_get_stored_auth.called = False

        Credentials(mock_config, "testID", token={'token_type':'1',
                                                  'access_token':'2'})
        mock_store_auth.assert_called_with({'token_type':'1',
                                            'access_token':'2'})
        self.assertTrue(mock_get_session.called)
        self.assertFalse(mock_get_stored_auth.called)

        mock_get_stored_auth.return_value = ({'token_type':'3',
                                              'access_token':'4'})
        Credentials(mock_config, "testID")
        mock_store_auth.assert_called_with({'token_type':'3',
                                            'access_token':'4'})
        self.assertTrue(mock_get_session.called)
        self.assertTrue(mock_get_stored_auth.called)

    @mock.patch('batchapps.credentials.keyring')
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

    @mock.patch('batchapps.credentials.keyring')
    def test_credentials_clear_auth(self, mock_keyring):
        """Test clear_auth"""

        creds = mock.create_autospec(Credentials)
        creds._log = logging.getLogger()
        creds._id = 'test'
        Credentials.clear_auth(creds)

        mock_keyring.delete_password.assert_called_with("AzureBatchApps",
                                                        "test")

    @mock.patch('batchapps.credentials.keyring')
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

    @mock.patch('batchapps.credentials.requests_oauthlib')
    def test_credentials_get_session(self, mock_requests):
        """Test get_session"""

        creds = mock.create_autospec(Credentials)
        creds._id = 'abc'
        creds.cfg = {'root':'1/',
                     'unattended_key':'3',
                     'token_uri':'/auth',
                     'resource':'https://test',
                     'tenant':'common',
                     'client_id':'abc'}
        creds.token = {'expires_at':'1',
                       'expires_in':'2',
                       'refresh_token':"test"}
        creds._log = logging.getLogger()

        Credentials.get_session(creds)
        mock_requests.OAuth2Session.assert_called_with(
            'abc',
            token=creds.token,
            auto_refresh_url='https://1/common/auth',
            auto_refresh_kwargs={'client_id':'abc', 'resource':'https://test'},
            token_updater=creds.store_auth)

        creds.token = {'expires_at':'1', 'expires_in':'2'}
        Credentials.get_session(creds)
        mock_requests.OAuth2Session.assert_called_with('abc',
                                                       token=creds.token)

