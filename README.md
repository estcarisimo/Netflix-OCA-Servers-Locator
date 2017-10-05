# Finding Netflix's OCA
## Description
Little piece of Python code to find out the currently candidate Netflix's OCA for the end-hosts that runs the script.
The script is based on fast.com, which is Netflix's speed test, which measures the the throughput between the users and the closest OCA.
The script is twofold: 
	1) It gets the token which is necessary to requests for the OCA list 
	2) It uses the token to download the list of OCA.

For more info: https://medium.com/netflix-techblog/building-fast-com-4857fe0f8adb

## Requierements:
To install the python libraries that are required to run the script:
'''
sudo pip install subprocess, json, requests, bs4
'''