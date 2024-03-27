#/bin/bash
python3 FTS_indexer.py

rc=$?; if [[ $rc != 0 ]]; then 
    echo "problem with the job. Exiting."
    exit $rc; 
fi