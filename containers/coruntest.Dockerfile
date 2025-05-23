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

# copy over corundum files, using same directory structure as in SimBricks
COPY ./nics/corundum /corundum
COPY ./nics/corundma_tb /corundum/fpga/app/dma_bench/tb/corundma_tb

# overwrite files with errors, with patches written by me
COPY ./containers/patches/mqnic_rx_queue_map.v /corundum/fpga/common/rtl/mqnic_rx_queue_map.v
COPY ./containers/patches/mqnic_core_pcie_us.Makefile /corundum/fpga/app/dma_bench/tb/mqnic_core_pcie_us/Makefile

# overwrite /lib/eth/lib/axis python files with SimBricks versions
# COPY ./containers/patches/eth_lib_axis-py/ /corundum/lib/eth/lib/axis/

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t coruntest -f containers/coruntest.Dockerfile .
# docker run -d --name coruntb coruntest

# docker exec -it coruntb bash
# Then remember to source the venv and set verilator as the SIM:
# source /corundum/venv/bin/activate
# export SIM=verilator
#
# before running make
