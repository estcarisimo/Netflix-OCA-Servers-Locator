# -*- coding: utf-8 -*-
#!/usr/local/bin/python

##################################################################
'''
Author: Esteban Carisimo
Affiliaton: Universidad de Buenos Aires & CONICET
Year: 2016
Description:
    Small piece of code to find out which Netflix's OCAs are candadites for the
    the end-host that is running the code.
    The search of the OCAs is based on the information provided by fast.com
'''
##################################################################

import subprocess
import json
import requests

cmd1 = 'curl -s https://fast.com/app-ed402d.js'
cmd2 = 'egrep -om1 \'token:"[^"]+\''
cmd3 = 'cut -f2 -d\'"\''
query = 'https://api.fast.com/netflix/speedtest?https=true&token=%s'

# Run command to get TOKEN from FAST.com API
ps1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE)
# Run command to extract TOKEN from FAST response
token = subprocess.check_output(
    cmd2,
    shell=True,
    stdin=ps1.stdout
).strip()[7:]
# Use TOKEN to request OCAs and URL to video chunk
response = requests.get(query % token)
# Turns `response` into dict
OCAs = json.loads(response.text)
for OCA in OCAs:
    print OCA['url']
