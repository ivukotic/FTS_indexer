curl -XPOST 'http://atlas-kibana-dev.mwt2.org:9200/_template/tfts' -d '{
    "index_patterns" : "tfts*",
    "settings" : {
        "number_of_shards" : 5,
        "number_of_replicas" : 0
    },
    "aliases": {
      "fts": {}
    },
    "mappings" : {
        "docs" : {
            "_source" : { "enabled" : true },
            "properties" : {
                "endpnt" : { "type" : "keyword" },
                "vo" : { "type" : "keyword" },
                "src_hostname" : { "type" : "keyword" },
                "dst_hostname" : { "type" : "keyword" },
                "src_site" : { "type" : "keyword" },
                "dst_site" : { "type" : "keyword" },
                "f_size" : { "type" : "long" },
                "error_code" : { "type" : "integer" },
                "failure_phase" : { "type" : "keyword" },
                "error_category" : { "type" : "keyword" },
                "final_transfer_state" : { "type" : "keyword" },
                "retry" : { "type" : "integer" },
                "processing_start" :{ "type" : "date" },
                "processing_stop" :{ "type" : "date" },
                "timestamp_chk_src_st" :{ "type" : "date" },
                "timestamp_chk_src_ended" :{ "type" : "date" },
                "timestamp_chk_dst_st" :{ "type" : "date" },
                "timestamp_chk_dst_ended" :{ "type" : "date" },
                "transfer_start" :{ "type" : "date" },
                "transfer_stop" :{ "type" : "date" },
                "metadata":{
                    "properties":{
                        "activity" : { "type" : "keyword" },
                        "src_type" : { "type" : "keyword" },
                        "dst_type" : { "type" : "keyword" },
                        "src_rse" : { "type" : "keyword" },
                        "dst_rse" : { "type" : "keyword" },
                        "request_id" : { "type" : "keyword" }
                    }
                }
            }
        }
    }
}'