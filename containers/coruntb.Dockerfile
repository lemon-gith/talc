FROM ubuntu:24.04

RUN apt-get update && apt-get upgrade -y

# install useful networking tools
RUN apt-get install -y iproute2 curl iputils-ping net-tools dnsutils tcpdump

# install SimBricks corundum dependencies
RUN apt-get install -y python3-dev python-is-python3 python3-pip gtkwave \
  git autoconf apt-utils bc bison flex build-essential cmake doxygen g++

RUN apt-get install -y verilator python3-venv iverilog

# make the corundum directory and work there
RUN mkdir -p /corundum
WORKDIR /corundum

# set up cocotb tools
RUN python3 -m venv venv
RUN . venv/bin/activate && pip install --upgrade pip
RUN . venv/bin/activate && pip install cocotb cocotbext-axi cocotbext-eth cocotbext-pcie scapy cocotb_test pytest

# copy over corundum files
COPY ./nics/corundum /corundum
# TODO: possibly do similar extractions as in corunsim to reduce complexity?
# As in, strip the system down to just what we need?
# Since I'm maintaining the overall file structure,
# can just give short instruction on how to port to full repo
# in order to be able to put it onto one of the supported FPGA boards

# add custom scripts to directory in PATH
COPY ./scripts/global /usr/local/bin
RUN chmod +x /usr/local/bin/*

# to update/add scripts, you can use the following command:
# docker cp ./scripts/<filename> cortb:/usr/local/bin/

ENTRYPOINT [ "sleep", "infinity" ]

# to get our nice mounted directory, which should make working on this easier,
# make sure to run the `docker run` command below

# run from repo root:
# docker build -t coruntb -f containers/coruntb.Dockerfile .
# docker run -d --name cortb --gpus=all --mount type=bind,src=./src/coruntb/tb,dst=/corundum/fpga/app/template/tb/coruntb coruntb
# docker exec -it cortb bash

# source /corundum/venv/bin/activate
# cd fpga/app/dma_bench/tb/coruntb
#
# then you can run make to run the testbench with `make`
