#!/usr/bin/env python

import queue
import socket
import time
import threading
from threading import Thread
import copy
from datetime import datetime

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
            "retry": m['retry'],
            "processing_start": m['timestamp_tr_st'],
            "processing_stop": m['timestamp_tr_comp'],
            "transfer_start": m['tr_timestamp_start'],
            "transfer_stop": m['tr_timestamp_complete'],
            "final_transfer_state": m['t_final_transfer_state']
        }
        if m['timestamp_chk_src_st'] > 0:
            data['timestamp_chk_src_st'] = m['timestamp_chk_src_st']
            data['timestamp_chk_src_ended'] = m['timestamp_chk_src_ended']

        if m['timestamp_checksum_dest_st'] > 0:
            data['timestamp_chk_dst_st'] = m['timestamp_checksum_dest_st']
            data['timestamp_chk_dst_ended'] = m['timestamp_checksum_dest_ended']

        if m['t_error_code']:
            data['error_code'] = m['t_error_code']

        if m['t_failure_phase'] and m['t_failure_phase']!='':
            data['failure_phase'] = m['t_failure_phase']
        
        if m['tr_error_category'] and m['tr_error_category']!='':
            data['error_category'] = m['tr_error_category']


        if m['t__error_message'] and m['t__error_message']!='':
            data['error_message'] = m['t__error_message']


        if 'file_metadata' in m and m['file_metadata']!=None:
            md = m['file_metadata']
            data['metadata']={}
            if 'src_type' in md and md['src_type']!=None:
                data['metadata']['src_type'] = md['src_type']
            if 'dst_type' in md and md['dst_type']!=None:
                data['metadata']['dst_type'] = md['dst_type']
            if 'src_rse' in md and md['src_rse']!=None:
                data['metadata']['src_rse'] = md['src_rse']
                so = siteMapping.get_site_from_ddm( md['src_rse'] )
                if so is not None:
                    data['metadata']['src_site'] = so[0]
            if 'dst_rse' in md and md['dst_rse']!=None:
                data['metadata']['dst_rse'] = md['dst_rse']
                de = siteMapping.get_site_from_ddm( md['dst_rse'] )
                if de is not None:
                    data['metadata']['dst_site'] = de[0]
            if 'request_id' in md:
                data['metadata']['request_id'] = md['request_id']
            if 'activity' in md:
                data['metadata']['activity'] = md['activity']
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
