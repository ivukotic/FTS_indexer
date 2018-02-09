#!/usr/bin/env python

import queue
import socket
import time
import threading
from threading import Thread
import copy
import json
from datetime import datetime
import math

import tools
from AMQ_Listener import ActiveMqListener
import siteMapping

# topic = "/topic/transfer.fts_monitoring_state"
# topic = "/topic/transfer.fts_monitoring_start"
topic = "/topic/transfer.fts_monitoring_complete"

siteMapping.reload()
MQ_parameters = tools.get_MQ_connection_parameters()

q = queue.Queue()


def inserter(message):
    q.put(message)


print("starting ...")
PORT = 61113

ips = set()
for a in socket.getaddrinfo(MQ_parameters['MQ_HOST'], PORT):
    ips.add(a[4][0])

for ip in ips:
    if ip.count(':') > 0:
        continue
    ActiveMqListener(ip, PORT, topic, inserter, MQ_parameters['MQ_USER'], MQ_parameters['MQ_PASS'])


def eventCreator():
    aLotOfData = []
    es_conn = tools.get_es_connection()
    while True:
        m = q.get()
        # print(m)
        dati = datetime.utcfromtimestamp(float(m['tr_timestamp_start']) / 1000)
        data = {
            '_type': 'docs',
            '_id': m['tr_id'],
            '_index': 'tfts_' + str(dati.year) + "-" + str(dati.month).zfill(2) + "-" + str(dati.day).zfill(2),
            'endpnt': m['endpnt'],
            'vo': m['vo'],
            "src_hostname":  m['src_hostname'],
            "dst_hostname":  m['dst_hostname'],
            "f_size":  m['f_size'],
            "t_error_code":  m['t_error_code'],
            "retry": m['retry'],
            "timestamp_tr_st": m['timestamp_tr_st'],
            "timestamp_tr_comp": m['timestamp_tr_comp'],
            "timestamp_chk_src_st": m['timestamp_chk_src_st'],
            "timestamp_chk_src_ended": m['timestamp_chk_src_ended'],
            "timestamp_checksum_dest_st": m['timestamp_checksum_dest_st'],
            "timestamp_checksum_dest_ended": m['timestamp_checksum_dest_ended'],
            "tr_timestamp_start": m['tr_timestamp_start'],
            "tr_timestamp_complete": m['tr_timestamp_complete']
        }

        # so = siteMapping.getPS(source)
        # de = siteMapping.getPS(destination)
        # if so is not None:
        #     data['srcSite'] = so[0]
        # if de is not None:
        #     data['destSite'] = de[0]

        aLotOfData.append(copy.copy(data))

        q.task_done()

        if len(aLotOfData) > 500:
            succ = tools.bulk_index(aLotOfData, es_conn=es_conn, thread_name=threading.current_thread().name)
            if succ is True:
                aLotOfData = []



# start eventCreator threads
for i in range(1):
    t = Thread(target=eventCreator)
    t.daemon = True
    t.start()


while True:
    time.sleep(55)
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "qsize:", q.qsize())
