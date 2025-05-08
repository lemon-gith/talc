FROM ubuntu:24.04

RUN apt update && apt upgrade -y

# install useful networking tools
RUN apt install -y iproute2 curl iputils-ping net-tools dnsutils

# install useful system tools
RUN apt install -y gtkwave python3 verilator python3-pip python3-venv

RUN python3 -m venv venv
RUN . venv/bin/activate && pip install --upgrade pip
RUN . venv/bin/activate && pip install pyyaml

# make the tonic directory and work there
RUN mkdir -p /tonic
WORKDIR /tonic

# copy over previously cloned tonic repo
COPY ./nics/tonic /tonic

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t tonic_test -f containers/tonic.Dockerfile .
# docker run -d --name tonic_tb tonic_test
# docker exec -it tonic_tb bash
