# FTS_indexer
Collects data from FTS AMQ and sends to Elasticsearch

container requires environment variables:

Mandatory:
MQ_HOST = 'netmon-mb.cern.ch'
MQ_USER = 'psatlflume'
MQ_PASS ''


Optional:
ES_USER
ES_PASS
ES_HOST