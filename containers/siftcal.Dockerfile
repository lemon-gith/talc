FROM ubuntu:24.04 AS build-image

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y rsync

RUN mkdir -p /corundum
RUN mkdir -p /coruncopy

COPY ./nics/corundum /corundum

WORKDIR /coruncopy

# copy, resolving all symlinks, except the example ones, cos those are cyclic...
RUN rsync -r -L -K --exclude '*/example/**/lib' \
  /corundum/fpga/app/template/ /coruncopy/

# Grab a fresh copy of the image to build the final container with
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
RUN rm ./activenv.corundum && mv ./activenv.siftcal ./activenv

# to update/add scripts, you can use the following command:
# docker cp ./scripts/<filename> cortb:/usr/local/bin/

# make directory for TAP stuff
RUN mkdir -p /siftcal/pyutils/netlib
# add the pyutils directory to PYTHONPATH, so it can be easily imported
RUN echo -e "\nPYTHONPATH=\${PYTHONPATH:+\${PYTHONPATH}:}/siftcal/pyutils/" >> \
  ~/.bashrc

# make the corundum directory and work there
RUN mkdir -p /siftcal
WORKDIR /siftcal

# copy over corundum files
COPY --from=build-image /coruncopy/ /siftcal/

# make sure the requirements are ported over
COPY ./containers/configs/requirements.txt /siftcal/

# set up cocotb tools
RUN python3 -m venv venv
RUN . activenv && pip install --upgrade pip
RUN . activenv && pip install -r /siftcal/requirements.txt

# TODO: Since I'm maintaining the overall file structure,
# can just give short instruction on how to port to full repo
# in order to be able to put it onto one of the supported FPGA boards

# give python executable networking capabilities (using our global script)
RUN privesc set /usr/bin/python3.12

# So that it's always running, and we can just exec in
ENTRYPOINT [ "sleep", "infinity" ]

# to get our nice mounted directory, which should make working on this easier,
# make sure to run the `docker run` command below

# run from repo root:
# docker build -t siftcal -f containers/siftcal.Dockerfile .
# docker run -d --name itcal --gpus=all --cap-add=NET_RAW --cap-add=NET_ADMIN --device /dev/net/tun:/dev/net/tun --mount type=bind,src=./src/tb,dst=/siftcal/tb/testbed/ --mount type=bind,src=./src/tap/py/,dst=/siftcal/pyutils/tapaz/ siftcal
# docker exec -it itcal bash

# then you can run make to run the testbench with `make`
