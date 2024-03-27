FROM python:latest

LABEL maintainer="Ilija Vukotic <ivukotic@cern.ch>"

COPY *.py .
COPY requirements.txt .

RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt


