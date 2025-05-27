FROM ubuntu:24.04

RUN apt-get update && apt-get upgrade -y

# install useful networking tools
RUN apt-get install -y iproute2 curl iputils-ping net-tools dnsutils tcpdump

# install SimBricks corundum dependencies
RUN apt-get install -y python3-dev python-is-python3 python3-pip gtkwave \
 git autoconf apt-utils bc bison flex build-essential cmake doxygen g++

# install verilator separately, since it uses an older version
# and also needs a patch
COPY ./containers/patches/corunsim/verilator.patch /tmp/
WORKDIR /tmp
RUN git clone -b v4.010 https://github.com/verilator/verilator \
 && cd verilator \
 && patch -p1 < /tmp/verilator.patch \
 && autoupdate \
 && autoconf \
 && ./configure \
 && make -j`nproc` \
 && make install \
 && rm -rf /tmp/verilator

# make the corundum directory and work there
RUN mkdir -p /corundum
WORKDIR /corundum

# copy over corundum files, using same directory structure as in SimBricks
COPY ./nics/corunsim/corundum/fpga/common/lib /corundum/lib
COPY ./nics/corunsim/corundum/fpga/common/rtl /corundum/rtl
COPY ./nics/corunsim/interface/ /corundum/

# overwrite files with errors, with patches written by SimBricks devs
COPY ./containers/patches/corunsim/port.v /corundum/rtl/port.v
COPY ./containers/patches/corunsim/interface.v /corundum/rtl/interface.v
COPY ./containers/patches/corunsim/dma_client_axis_sink.v /corundum/lib/pcie/rtl/dma_client_axis_sink.v

# overwrite /lib/eth/lib/axis python files with SimBricks versions
COPY ./containers/patches/corunsim/eth_lib_axis-py/ /corundum/lib/eth/lib/axis/

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t corunsim_test -f containers/corunsim.Dockerfile .
# docker run -d --name corunsim_tb corunsim_test
# docker exec -it corunsim_tb bash
