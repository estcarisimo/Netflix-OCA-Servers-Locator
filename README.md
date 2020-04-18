# Finding Netflix's OCA
## Description
Little piece of Python code to find out candidate Netflix's Open Connect Appliances (OCA) for the end-host running this script.
We rely on Netflix's speed-test fast.com, which measures throughput between users and their allocated OCAs.
The script is two-fold: 
1. It gets the token necessary to request the list of OCAs.  
2. It requests the list of OCAs by inserting the token on the request.

For more info: https://medium.com/netflix-techblog/building-fast-com-4857fe0f8adb

## Requirements:
To install the python libraries that are required to run the script:
```
$ pip install -r requirements.txt
```

In addition, you may need to install ```whois``` and/or ```curl``` in case they ar not installed yet

```
$ sudo apt-get install whois
$ sudo apt-get install curl
```

## To run

Thanks to @seblaz, scripts now supports python3

```
python get_ocas.py
```

