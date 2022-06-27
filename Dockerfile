FROM python:3.8 as builder

WORKDIR /stage-2022-mahdi
RUN pip install -e .