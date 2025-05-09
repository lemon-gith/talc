FROM ubuntu:24.04

RUN apt update && apt upgrade -y

# install useful networking tools
RUN apt install -y iproute2 curl iputils-ping net-tools dnsutils

# install corundum system tools
RUN apt install -y python3 gtkwave iverilog verilator python3-pip python3-virtualenv

# make the corundum directory and work there
RUN mkdir -p /corundum
WORKDIR /corundum

RUN python3 -m virtualenv venv
RUN . venv/bin/activate && pip install --upgrade pip

RUN . venv/bin/activate && pip install cocotb cocotb-bus cocotb-test cocotbext-axi cocotbext-eth cocotbext-pcie pytest scapy tox pytest-xdist pytest-sugar

# copy over corundum files, using same directory structure as in SimBricks
COPY ./nics/corundum/fpga/common/lib /corundum/lib
COPY ./nics/corundum/fpga/common/rtl /corundum/rtl
COPY ./nics/corundum_if/ /corundum/

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t corundum_test -f containers/corundum.Dockerfile .
# docker run -d --name corundum_tb corundum_test
# docker exec -it corundum_tb bash
