import requests
import subprocess
import socket
import pandas as pd
import re
from prettytable import PrettyTable

def fetch_public_ip():
    """
    Fetch the public IP address of the host.

    Returns
    -------
    str
        The public IP address.
    """
    # Send a GET request to ipify API to retrieve the public IP address
    response = requests.get('https://api.ipify.org?format=json')
    # Extract and return the IP address from the response JSON
    return response.json()['ip']

def get_host_isp_info(ip_address):
    """
    Fetch ISP information for a given IP address using an external WHOIS service.

    Parameters
    ----------
    ip_address : str
        The IP address for which to fetch ISP information.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing ISP information for the IP address.
    """
    # Execute a WHOIS query using an external service to get ISP details
    cymru_request = f'whois -h whois.cymru.com " -v {ip_address}"'
    isp_info = subprocess.check_output(cymru_request, shell=True).decode("utf-8")
    # Split the response into lines and extract columns and data
    lines = isp_info.strip().split('\n')
    columns = lines[0].split('|')
    data = [line.split('|') for line in lines[1:]]
    # Create and return a DataFrame with the extracted data
    df = pd.DataFrame(data, columns=[col.strip() for col in columns])
    
    return df

def get_netflix_token():
    """
    Retrieve a Netflix token from Fast.com for accessing OCA (Open Connect Appliances) candidates.

    Returns
    -------
    str or None
        A token for accessing Netflix's OCA candidates, or None if retrieval fails.
    """
    # Request the JavaScript file from Fast.com that contains the token
    fast_js_url = 'https://fast.com/app-ed402d.js'
    response = requests.get(fast_js_url)
    # If the request is successful, search for the token pattern in the response text
    if response.status_code == 200:
        content = response.text
        token_match = re.search(r'token:"([^"]+)"', content)
        if token_match:
            # Return the token if found
            return token_match.group(1)
    # Return None if no token is found
    return None

def fetch_oca_candidates(token):
    """
    Fetch Netflix's OCA candidates using the provided token.

    Parameters
    ----------
    token : str
        The token for accessing Netflix's OCA candidates.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing URLs and IP addresses of Netflix's OCA candidates.
    """
    # Use the token to request the list of OCA candidates from Fast.com
    response = requests.get(f'https://api.fast.com/netflix/speedtest?https=true&token={token}')
    oca_list = response.json()
    # Convert the JSON response to a DataFrame
    df = pd.DataFrame(oca_list)
    # Resolve and add the IP addresses of each OCA to the DataFrame
    df['IP Address'] = df['url'].apply(lambda x: socket.gethostbyname(x.split('/')[2]))
    return df[['url', 'IP Address']]

def dataframe_to_prettytable(df):
    """
    Convert a pandas DataFrame to a PrettyTable for pretty printing.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to convert.

    Returns
    -------
    prettytable.PrettyTable
        A PrettyTable object representing the DataFrame.
    """
    # Initialize a PrettyTable object and set its column names
    pt = PrettyTable()
    pt.field_names = df.columns.tolist()
    # Add each row of the DataFrame to the PrettyTable
    for index, row in df.iterrows():
        pt.add_row(row.values)
    # Return the PrettyTable object
    return pt

def main():
    """
    Main function to execute the program logic.
    """
    ip_address = fetch_public_ip()
    print(f"Fetching public IP address...\nYour public IP address is: {ip_address}\n")

    # Host ISP Information
    isp_df = get_host_isp_info(ip_address)
    print("Host IP Information:\n" + str(dataframe_to_prettytable(isp_df)) + "\n")

    # Fetch token for OCA candidates
    token = get_netflix_token()
    
    if token:
        # Allocated OCAs for the user
        oca_df = fetch_oca_candidates(token)
        print("Allocated OCAs for this user:\n" + str(dataframe_to_prettytable(oca_df)) + "\n")
    else:
        print("Failed to fetch Netflix token.")

if __name__ == "__main__":
    main()
