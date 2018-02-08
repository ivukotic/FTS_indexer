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

                "timestamp_tr_st" :{ "type" : "date" },
                "timestamp_tr_comp" :{ "type" : "date" },
                "timestamp_chk_src_st" :{ "type" : "date" },
                "timestamp_chk_src_ended" :{ "type" : "date" },
                "timestamp_checksum_dest_st" :{ "type" : "date" },
                "timestamp_checksum_dest_ended" :{ "type" : "date" },
                "tr_timestamp_start" :{ "type" : "date" },
                "tr_timestamp_complete" :{ "type" : "date" }
            }
        }
    }
}'