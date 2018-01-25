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

topic = "/topic/transfer.fts_monitoring_state"
# topic = "/topic/transfer.fts_monitoring_start"
# topic = "/topic/transfer.fts_monitoring_complete"

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
    ActiveMqListener(ip, PORT, topic, inserter, MQ_parameters['MQ_USER'], MQ_parameters['MQ_PASS'])


def eventCreator():
    aLotOfData = []
    es_conn = tools.get_es_connection()
    while True:
        m = q.get()
        print(m)
        continue
        data = {
            '_type': 'latency'
        }

        source = m['meta']['source']
        destination = m['meta']['destination']
        data['MA'] = m['meta']['measurement_agent']
        data['src'] = source
        data['dest'] = destination
        data['src_host'] = m['meta']['input_source']
        data['dest_host'] = m['meta']['input_destination']
        data['ipv6'] = False
        if ':' in source or ':' in destination:
            data['ipv6'] = True
        so = siteMapping.getPS(source)
        de = siteMapping.getPS(destination)
        if so is not None:
            data['srcSite'] = so[0]
            data['srcVO'] = so[1]
        if de is not None:
            data['destSite'] = de[0]
            data['destVO'] = de[1]
        data['srcProduction'] = siteMapping.isProductionLatency(source)
        data['destProduction'] = siteMapping.isProductionLatency(destination)
        su = m['datapoints']
        for ts, th in su.items():
            dati = datetime.utcfromtimestamp(float(ts))
            data['_index'] = tools.index_prefix + str(dati.year) + "." + str(dati.month) + "." + str(dati.day)
            data['timestamp'] = int(float(ts) * 1000)
            th_fl = dict((float(k), v) for (k, v) in th.items())

            # mean
            samples = sum([v for k, v in th_fl.items()])
            th_mean = sum(k * v for k, v in th_fl.items()) / samples
            data['delay_mean'] = th_mean
            # std dev
            data['delay_sd'] = math.sqrt(sum((k - th_mean) ** 2 * v for k, v in th_fl.items()) / samples)
            # median
            csum = 0
            ordered_th = [(k, v) for k, v in sorted(th_fl.items())]
            midpoint = samples // 2
            if samples % 2 == 0:  # even number of samples
                for index, entry in enumerate(ordered_th):
                    csum += entry[1]
                    if csum > midpoint + 1:
                        data['delay_median'] = entry[0]
                        break
                    elif csum == midpoint:
                        data['delay_median'] = entry[0] + ordered_th[index + 1][0] / 2
                        break
                    elif csum == midpoint + 1 and index == 0:
                        data['delay_median'] = entry[0]
                        break
                    elif csum == midpoint + 1 and index > 0:
                        data['delay_median'] = entry[0] + ordered_th[index - 1][0] / 2
                        break
            else:  # odd number of samples
                for index, entry in enumerate(ordered_th):
                    csum += entry[1]
                    if csum >= midpoint + 1:
                        data['delay_median'] = entry[0]
                        break
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
