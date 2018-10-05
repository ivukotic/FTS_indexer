# FTS_indexer
Collects data from FTS AMQ and sends to Elasticsearch

requires environment variables:

Mandatory:
* MQ_HOST = 'netmon-mb.cern.ch'
* MQ_USER = 'XXXXX'
* MQ_PASS = 'XXXXX'

Optional:
* ES_USER
* ES_PASS
* ES_HOST

NB: for ATLAS Analytics this collector runs at UofC k8s cluster. It is started by regular "containers" scripts.