FROM ubuntu:24.04

RUN apt update && apt upgrade -y

# install useful networking tools
RUN apt install -y iproute2 curl iputils-ping net-tools dnsutils

# TODO: will I still be using python? maybe a tad
# but probably don't need pyyaml?

# install useful system tools
RUN apt install -y gtkwave python3 verilator python3-pip python3-venv

RUN python3 -m venv venv
RUN . venv/bin/activate && pip install --upgrade pip
RUN . venv/bin/activate && pip install pyyaml

# make the tunic directory and work there
RUN mkdir -p /tunic
WORKDIR /tunic

# copy over previously cloned tunic repo
COPY ./nics/tunic /tunic

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t tunic_test -f containers/tunic.Dockerfile .
# docker run -d --name tunic_tb tunic_test
# docker exec -it tunic_tb bash
