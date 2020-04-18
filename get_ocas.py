
#  -*- coding: utf-8 -*-
# !/usr/local/bin/python

"""
'''
Author: Esteban Carisimo
Affiliaton: Universidad de Buenos Aires & CONICET
Year: 2016
Description:
    Small piece of code to find out which Netflix's OCAs are candadites for the
    the end-host that is running the code.
    The search of the OCAs is based on the information provided by fast.com
'''
"""

import subprocess
import json
import requests
import socket


def get_host_isp_information():
    """
    Thi function call Netflix's API to get the list of candidates OCAs for the user running the script.

    inputs
    -----------
    None

    returns
    -----------
    None (stdout)
    """
    public_ip_request = 'https://api.ipify.org?format=json'
    response = requests.get(public_ip_request)
    ip_addr = json.loads(response.text)
    cymru_request = 'whois -h whois.cymru.com " -v {}"'.format(ip_addr['ip'])
    # Run command to extract TOKEN from FAST response
    host_isp_information = subprocess.check_output(
        cymru_request,
        shell=True
    )
    print("############################################################################################################")
    print('> Host IP information')
    print(host_isp_information.decode("utf-8"))


def request_for_oca():
    """
    Thi function call Netflix's API to get the list of candidates OCAs for the user running the script.

    inputs
    -----------
    None

    returns
    -----------
    None (stdout)
    """
    cmd1 = 'curl -s https://fast.com/app-ed402d.js'
    cmd2 = 'egrep -om1 \'token:"[^"]+\''
    # cmd3 = 'cut -f2 -d\'"\''
    query = 'https://api.fast.com/netflix/speedtest?https=true&token={}'

    # Run command to get TOKEN from FAST.com API
    ps1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE)
    # Run command to extract TOKEN from FAST response
    token = subprocess.check_output(
        cmd2,
        shell=True,
        stdin=ps1.stdout
    ).strip()[7:].decode("utf-8")
    # Use TOKEN to request OCAs and URL to video chunk
    response = requests.get(query.format(token))
    # Turns `response` into dict
    oca_list = json.loads(response.text)
    print("############################################################################################################")
    print('> Allocated OCAs for this user')
    for oca in oca_list:
            print(oca['url'])
    print("############################################################################################################")
    print('> IP address of the allocated OCAs')
    for oca in oca_list:
            fqdn = oca['url'].split('/')[2]
            print(socket.gethostbyname(fqdn))


def main():
    """
    asd.

    asd.
    """
    get_host_isp_information()
    request_for_oca()


if __name__ == "__main__":
    # execute only if run as a script
    main()
