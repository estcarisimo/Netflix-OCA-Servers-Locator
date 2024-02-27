# Fetching Netflix OCA Information

## Description
This Python program is designed to help users find candidate Netflix's Open Connect Appliances (OCA) that are allocated to their network. It leverages Netflix's fast.com to measure the network throughput between the user and the OCAs. The program performs several steps to gather necessary information and present it to the user:

1. Fetches the public IP address of the user.
2. Retrieves ISP information for the user's IP address.
3. Obtains a token from fast.com necessary for requesting OCA candidates.
4. Requests a list of OCA candidates using the obtained token and displays them along with their IP addresses.

This utility provides insights into how Netflix delivers content with optimal performance by connecting users to the nearest or most suitable OCA.

For more information on how fast.com works and its significance, visit [Netflix TechBlog](https://medium.com/netflix-techblog/building-fast-com-4857fe0f8adb).

## Requirements

### Python Libraries
To install the required Python libraries, use the following command:

```sh
pip install -r requirements.txt
```

### External Tools
This script utilizes external commands like `whois` for fetching ISP information. Ensure that `whois` is installed on your system. Most environments come with `whois` pre-installed, but if it's missing, you can install it using:

```sh
sudo apt-get install whois
```

### Additional Setup
Ensure that Python and `pip` are correctly installed on your system. This script is compatible with Python 3.

## How to Run

To execute the script and find out the allocated Netflix OCA for your host, simply run:

```sh
python find_netflix_ocas.py
```

Ensure that you're in the directory containing the `get_ocas.py` script when you run this command.

## Contributions

This project welcomes contributions and suggestions. Feel free to fork the repository, make improvements, and submit pull requests. This initiative aims to improve understanding and performance insights related to Netflix's content delivery network and how it impacts user experience.

### Acknowledgements

This script has been updated to support Python 3 and to include enhancements in fetching and displaying OCA information. We appreciate all contributions that help in evolving and maintaining this utility.