FROM python:latest

LABEL maintainer="Ilija Vukotic <ivukotic@cern.ch>"

RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY run.sh .
COPY FTS_indexer.py .
COPY AMQ_Listener.py .
