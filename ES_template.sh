curl -XPOST 'http://atlas-kibana-dev.mwt2.org:9200/_template/tfts' -d '{
    "template" : "tfts*",
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

                "f_size" : { "type" : "long" },
                "t_error_code" : { "type" : "integer" },
                "retry" : { "type" : "integer" },

                "processing_start" :{ "type" : "date" },
                "processing_stop" :{ "type" : "date" },
                "timestamp_chk_src_st" :{ "type" : "date" },
                "timestamp_chk_src_ended" :{ "type" : "date" },
                "timestamp_chk_dest_st" :{ "type" : "date" },
                "timestamp_chk_dest_ended" :{ "type" : "date" },
                "transfer_start" :{ "type" : "date" },
                "transfer_stop" :{ "type" : "date" }
            }
        }
    }
}'