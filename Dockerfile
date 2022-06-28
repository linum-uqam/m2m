FROM python:3.6.13

RUN apt-get update
RUN apt-get -y upgrade

RUN apt -y install libblas-dev
RUN apt -y install liblapack-dev
RUN apt -y install libgl1-mesa-glx
RUN apt -y install jq
RUN apt -y install rename

WORKDIR /
COPY . .

WORKDIR /stage-2022-mahdi
RUN pip install -e .