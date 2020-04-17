import osproc, json, httpclient, strutils, re, nativesockets

let requests = newHttpClient()

proc get_host_isp_information() =
  ## This function call Netflix's API to get the list of candidates OCAs for the user running the script.
  const url = "https://api.ipify.org"
  let
    ipaddr = requests.getContent(url).strip()  # Get IP address.
    host_isp_information = execProcess("whois -h whois.cymru.com ' -v " & ipaddr & "'") # whois.
  echo "#".repeat(99), "\n> Host IP information\n", host_isp_information

proc request_for_oca() =
  ## This function call Netflix's API to get the list of candidates OCAs for the user running the script.
  const
    url = "https://fast.com/app-ed402d.js"
    query = "https://api.fast.com/netflix/speedtest?https=true&token="
  let  # Run command to get TOKEN from FAST.com API
    token = findAll(requests.getContent(url), re"""token:"(.+)",urlCount""")[0][7..^11]
    oca_list = parseJson(requests.getContent(query & token)) # JSON with OCA.
  echo "#".repeat(99), "\n> Allocated OCAs for this user"
  for oca in oca_list: echo oca["url"].getStr  # Echo the URLs to stdout.
  echo "#".repeat(99), "\n> IP address of the allocated OCAs"
  for oca in oca_list: echo getHostByName(oca["url"].getStr.split('/')[2]).addrList[0] # Echo the IPs to stdout.


when isMainModule:
  get_host_isp_information()
  request_for_oca()
