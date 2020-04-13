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

## To run

**The current version of the script only supports python 2**

```
python get_ocas.py
```

