FROM python:3.9-slim

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /src
RUN mkdir -p /tests
COPY src/ /src/
RUN pip install -e /src
COPY tests/ /tests/

WORKDIR /src