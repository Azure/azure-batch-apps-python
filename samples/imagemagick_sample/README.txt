#-------------------------------------------------------------------------
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
 

Batch Apps ImageMagick Sample
------------------------------
This sample should only be treated as a basic example of how to run and deploy an ImageMagick job 
using the Batch apps service and the python client.
 
The sample covers:
How to create and submit the Job to the Batch apps service using the BatchApps Client python package.
How to monitor a submitted job.
How to download any outputs created by the running Job.
How to download the final outputs of the Job.


What is ImageMagick?
--------------------
ImageMagick is an open-source command line tool used for manipulating images. See more at 
http://www.imagemagick.org/.
In this sample, ImageMagick is used simply as an example of a JobType that can be run on the Batch 
Apps platform.
Any type of application that can be made to run in parallel has the potential to use the Batch Apps 
service. 


Pre-sample Set Up
-----------------
Before you can run a job in the cloud it is necessary to build two application-specific components,
a cloud assembly and application image, that will work alongside the client application.
These then need to be uploaded to blob storage.

The cloud assembly is a set of dlls containing two parts: a job splitter and a task processor, describing 
how to parallelize a job into tasks and how to invoke the application program to run each task respectively.

The application image is a zip file containing the application to be run in the cloud (in this 
case ImageMagick) along with any dependencies.
For instructions on how to build a cloud assembly and application image for ImageMagick see ....


Set Up
------
	1. Open VisualStudio 2013
	2. Make sure you have installed your preferred version of Python (see the Python package project 
	   page for compatible versions).
	3. Install the PyTools (Python Tools for Visual Studio) plugin by going to 'Tools' > 'Extensions 
	   and Updates' and search for pytools.
	4. Open the sample solution

In order to run the sample, the BatchApps python package either needs to by installed into your python 
installation, or a virtual python development
environment needs to be set up. To create such an environment:

	1. Create a python environment by right-clicking 'Python Environments' in the Solution Explorer 
	   and 'Add Virtual Environment'.
	2. Install the BatchApps Client python package, which can be done in several different ways:
		a. Right-click on your newly created python environment in the solution explorer. Click 'Install 
		   from requirements.txt'.
		   Pip will use the requirements.txt provided with the project to install all necessary packages, 
		   including BatchApps Client. 
		b. Right-click on your newly created python environment in the solution explorer, click 'Install 
		   python package', type BatchAppsClient and click OK. 
		c. Open the cmd prompt and enter "C:\\Path\\To\\VS Python Environment\\Scripts\\activate.bat" to 
		   activate your environment.
 		   Then enter "C:\\Path\\To\\VS Python Environment\\Scripts\\pip.exe" install BatchAppsClient. 
		   After installation, deactivate the virtual environment using deactivate.bat


Running the Project
-------------------
	1. Set the appropriate global variables in the script:
		a. TIMEOUT: The length of time you would like the script to continue monitoring a job once it's 
		   submitted, until it completes. The default is set to an hour.
		b. DOWNLOAD_DIR: The path to the output location.
		c. ASSET_DIR: The path to the folder containing the images you want to upload.
		a. ENDPOINT: Login to MissionControl https://manage.batchapps.windows.net/ with your Microsoft
		   Account. Select your service under the Services page. Copy the service URL from the clipboard.
		b. CLIENT_ID & REDIRECT_URI: Navigate, and sign in to the Azure Management Portal. Click Active 
		   Directory, click the directory, click the application you have registered. The client_id and 
		   redirect_uri can be found under the 'Configure' tab.
	2. Optional: By default, this sample downloads tasks as they complete. If you would like to also 
	   download the final job output once the the job has completed, ensure the appropriate line of 
	   code has been uncommented in the _check_job_stopped() function.
	3. Run the sample by right-clicking on ImageProcessingSample.py and clicking on Start Without Debugging,
	   or alternatively, click the Start button in the tool shelf (make sure the ImageProcessingSample is
	   set as the startup file). Your job should be submitted to the Batch service, and you should be able
	   to watch progress via the pop-up console. Once the job finishes the output should be downloaded
	   into the output location.
