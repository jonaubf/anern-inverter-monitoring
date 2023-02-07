FROM library/python:3.9-slim

WORKDIR /app
ADD . /app

RUN python setup.py install

EXPOSE 8081
