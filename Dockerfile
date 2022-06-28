FROM python:3.6.13

RUN apt-get update
RUN apt-get -y upgrade

RUN apt -y install libblas-dev
RUN apt -y install liblapack-dev
RUN apt -y install libgl1-mesa-glx
RUN apt -y install jq
RUN apt -y install rename

WORKDIR /
ENV A2T_VERSION="main"
RUN wget https://github.com/linum-uqam/stage-2022-mahdi/archive/${A2T_VERSION}.zip
RUN unzip ${A2T_VERSION}.zip
RUN mv stage-2022-mahdi-${A2T_VERSION} allen2tract

WORKDIR /stage-2022-mahdi
RUN pip install -e .