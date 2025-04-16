import requests
import subprocess
import socket
import pandas as pd
import re
from prettytable import PrettyTable
from urllib.parse import urlparse

def fetch_public_ip():
    """
    Fetch the public IP address of the host.

    Returns
    -------
    str
        The public IP address.
    """
    response = requests.get('https://api.ipify.org?format=json')
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
    cymru_request = f'whois -h whois.cymru.com " -v {ip_address}"'
    isp_info = subprocess.check_output(cymru_request, shell=True).decode("utf-8")

    lines = isp_info.strip().split('\n')
    columns = lines[0].split('|')
    data = [line.split('|') for line in lines[1:]]

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
    fast_js_url = 'https://fast.com/app-ed402d.js'
    response = requests.get(fast_js_url)
    if response.status_code == 200:
        content = response.text
        token_match = re.search(r'token:"([^"]+)"', content)
        if token_match:
            return token_match.group(1)
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
        A DataFrame containing the Domain and IP Address of Netflix's OCA candidates.
    """
    response = requests.get(f'https://api.fast.com/netflix/speedtest?https=true&token={token}')
    oca_list = response.json()
    df = pd.DataFrame(oca_list)

    # Extract domain from each URL
    df['Domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
    # Resolve the IP address from the domain
    df['IP Address'] = df['Domain'].apply(lambda domain: socket.gethostbyname(domain))

    # Return only the Domain and IP Address columns
    return df[['Domain', 'IP Address']]

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
    pt = PrettyTable()
    pt.field_names = df.columns.tolist()
    for _, row in df.iterrows():
        pt.add_row(row.values)
    return pt

def main():
    """
    Main function to execute the program logic.
    """
    print("=" * 60)
    print("Fetching public IP address...")
    ip_address = fetch_public_ip()
    print(f"Your public IP address is: {ip_address}")
    print("=" * 60)

    # Retrieve host ISP information
    isp_df = get_host_isp_info(ip_address)
    print("Host IP Information:")
    print(dataframe_to_prettytable(isp_df))
    print("=" * 60)

    # Fetch and display OCA candidates
    token = get_netflix_token()
    if token:
        oca_df = fetch_oca_candidates(token)
        print("Allocated OCAs for this user:")
        print(dataframe_to_prettytable(oca_df))
    else:
        print("Failed to fetch Netflix token.")
    print("=" * 60)

if __name__ == "__main__":
    main()