FROM ubuntu:24.04

RUN apt-get update && apt-get upgrade -y

# install useful networking tools
RUN apt-get install -y iproute2 curl iputils-ping net-tools dnsutils

# install useful system tools
RUN apt-get install -y gtkwave python3-venv python3-pip verilator python3

# make the tunic directory and work there
RUN mkdir -p /tunic
WORKDIR /tunic

RUN python3 -m venv venv
RUN . venv/bin/activate && pip install --upgrade pip
RUN . venv/bin/activate && pip install pyyaml

# copy over previously cloned tunic repo
COPY ./nics/tunic /tunic

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t tunic_test -f containers/tunic.Dockerfile .
# docker run -d --name tunic_tb tunic_test
# docker exec -it tunic_tb bash

# source /tunic/venv/bin/activate
# ./tools/runtest --type sim --config tonic/tonic_reno.yaml
