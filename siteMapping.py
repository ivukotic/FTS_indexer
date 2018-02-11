import sys
import socket
import time
import requests


try:
    import simplejson as json
except ImportError:
    import json

ot = 0


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

    timeout = 60
    socket.setdefaulttimeout(timeout)

    ot = time.time() - 86300  # in case it does not succeed in updating it will try again in 100 seconds.
    try:
        r = requests.get('http://atlas-agis-api.cern.ch/request/site/query/list/?json&vo_name=atlas&state=ACTIVE')
        res = r.json()
        sites = []
        for s in res:
            sites.append(s["rc_site"])
        # print(res)
        print('Sites reloaded.')
    except:
        print("Could not get sites from AGIS. Exiting...")
        print("Unexpected error: ", str(sys.exc_info()[0]))

    print('All done.')
    ot = time.time()  # all updated so the next one will be in one day.
