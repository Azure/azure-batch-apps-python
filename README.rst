===============================
Azure Batch Apps Python Client
===============================

The package is to enable Azure Batch Apps customers to interact with the
Management API using Python.


Installation
============

This package has been tested with Python 2.6, 2.7, 3.2, 3.3 and 3.4

>> pip install batch_apps

Required packages:

* `Requests 2.3.0 <http://docs.python-requests.org/en/latest/>`_

* `Keyring 3.8 <https://bitbucket.org/kang/python-keyring-lib>`_

* `Requests-OAuthlib 0.4.1 <http://requests-oauthlib.readthedocs.org/en/latest/>`_


Usage
============

Authentication
---------------

The module authenticates with Azure Active Directory (an implementation of OAuth2).
The batch_apps module provides a helper class to assist in retrieving an AAD token 
using Requests-OAuthlib. However if you have a preferred OAuth implementation, you 
authenticate with this instead::

	from batch_apps import AzureOAuth
	import webbrowser

	webbrowser.open(AzureOAuth.get_authorization_url())
	redirect_url = input("Please paste the redirect url here: ")

	creds = AzureOAuth.get_authorization_token(redirect_url)

Or alternatively, if you use a different AAD implementation::

	from batch_apps import Credentials
	import my_oauth

	aad_token = my_oauth.get_token()
	creds = Credentials(aad_token)

If you have Service Principal access credentials, you can also authenticate 
with these. You will need to add the crdentials to the batch_apps.ini configuration 
file::

	service_principal = my_service_client_id@my_tenant
	service_principal_key = my_service_password

Then you can authenticate with these credentials::

	from batch_apps import AzureOAuth

	creds = AzureOAuth.get_principal_token()

Once you have logged in for the first time, your session will be auth-refreshed 
for a limited time, so you will not need to re-authenticate. If you have a 
stored session, you can authenticate with::

	from batch_apps import AzureOAuth

	creds = AzureOAuth.get_session()


Job Management
---------------

Job management, including submission, monitoring, and accessing outputs is done 
through the JobManager class::

    from batch_apps import AzureOAuth, JobManager

	creds = AzureOAuth.get_session()
	mgr = JobManager(creds)

	my_job = mgr.create_job("First Job")
	
	# Apply any custom parameters and source files here
	job_id = my_job.submit()['jobid']

	job_progress = mgr.get_job(jobid=job_id)
	s
	if job_progress.status == 'Complete':
		job_progress.get_output('c:\\my_download_dir')

	else:
		job_progress.cancel()


File Management
----------------

File management, including job source files and dependencies can by synced to 
the cloud using the FileManager class::

	from batch_apps import AzureOAuth, FileManager

	creds = AzureOAuth.get_session()
	mgr = FileManager(creds)

	job_source = mgr.create_file('C:\\start_job.bat')
	file_collection = mgr.files_from_dir('c:\\my_job_assets')
	file_collection.add(job_source)

	file_collection.upload()

	# Check files previously uploaded matching a certain name
	mgr.find_files('start_job.bat')

	# Retrieve a list of all uploaded files
	mgr.list_files()


Application Configuration
--------------------------

To set up a new application type, and any custom parameters you want associated 
with it, it can be added to the configuration file.
You can edit the file directly, or via the Configuration class.
By default the configuration file will be created in the user directory::

	from batch_apps import Configuration

	cfg = Configuration(log_level='debug', default=True)
	cfg.add_application('my_app', 'my.endpoint.com', 'client_id')

	# Set this application as the current job type
	cfg.application('my_app')

	# Set this as the default application for all future jobs
	cfg.set_default_application()

	# Add some custom parameters
	cfg.set('start_val') = 1
	cfg.set('end_val') = 100
	cfg.set('timeout') = 500

	# Save additional parameters to file
	cfg.save_config()