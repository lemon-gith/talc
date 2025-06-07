FROM ubuntu:24.04

# ensure that all following commands are run with bash, not bourne shell
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get upgrade -y

# install useful networking tools
RUN apt-get install -y iproute2 curl iputils-ping net-tools dnsutils tcpdump

# install Corundum dependencies
RUN apt-get install -y python3-dev python-is-python3 python3-pip gtkwave \
  git autoconf apt-utils bc bison flex build-essential cmake doxygen g++

RUN apt-get install -y verilator python3-venv iverilog

# add custom scripts to directory in PATH
WORKDIR /usr/local/bin
COPY ./scripts/global .
RUN chmod +x ./*
RUN rm ./activenv.talc && mv ./activenv.corundum ./activenv

# to update/add scripts, you can use the following command:
# docker cp ./scripts/<filename> cortb:/usr/local/bin/

# make directory for TAP stuff
RUN mkdir -p /tapaz

# make the corundum directory and work there
RUN mkdir -p /corundum
WORKDIR /corundum

# make sure the requirements are ported over
COPY ./containers/configs/requirements.txt /corundum/

# set up cocotb tools
RUN python3 -m venv venv
RUN . activenv && pip install --upgrade pip
RUN . activenv && pip install -r /corundum/requirements.txt

# copy over corundum files
COPY ./nics/corundum /corundum
# TODO: possibly do similar extractions as in corunsim to reduce complexity?
# As in, strip the system down to just what we need?
# Since I'm maintaining the overall file structure,
# can just give short instruction on how to port to full repo
# in order to be able to put it onto one of the supported FPGA boards

# give python executable networking capabilities (using our global script)
RUN privesc set /usr/bin/python3.12

# So that it's always running, and we can just exec in
ENTRYPOINT [ "sleep", "infinity" ]

# to get our nice mounted directory, which should make working on this easier,
# make sure to run the `docker run` command below

# run from repo root:
# docker build -t coruntb -f containers/coruntb.Dockerfile .
# docker run -d --name cortb --gpus=all --cap-add=NET_RAW --cap-add=NET_ADMIN --device /dev/net/tun:/dev/net/tun --mount type=bind,src=./src/coruntb/tb,dst=/corundum/fpga/app/template/tb/coruntb coruntb
# docker exec -it cortb bash

# source /corundum/venv/bin/activate
# cd fpga/app/dma_bench/tb/coruntb
#
# then you can run make to run the testbench with `make`
