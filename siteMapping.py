import sys
import socket
import time
import requests


try:
    import simplejson as json
except ImportError:
    import json

ot = 0
ddm_site = {}

def getIP(host):
    ip = 'unknown'
    try:
        ip = socket.gethostbyname(host)
    except:
        print("Could not get ip for", host)
    return ip


def reload():
    print('starting mapping reload')
    global ot
    global ddm_site
    timeout = 60
    socket.setdefaulttimeout(timeout)

    ot = time.time() - 86300  # in case it does not succeed in updating it will try again in 100 seconds.
    try:
        r = requests.get('http://atlas-agis-api.cern.ch/request/site/query/list/?json&vo_name=atlas&state=ACTIVE')
        res = r.json()
        sites = []
        for s in res:
            sites.append(s["rc_site"])
            for ddm in s["ddmendpoints"]:
                ddm_site[ddm] = s["rc_site"]
        # print(res)
        print('Sites reloaded.')
    except:
        print("Could not get sites from AGIS. Exiting...")
        print("Unexpected error: ", str(sys.exc_info()[0]))

    print('All done.')
    ot = time.time()  # all updated so the next one will be in one day.

def get_site_from_ddm(ddm):
    if ddm in ddm_site:
        return ddm_site[ddm]
    return None