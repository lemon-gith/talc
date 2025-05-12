FROM ubuntu:24.04

RUN apt update && apt upgrade -y

# install useful networking tools
RUN apt install -y iproute2 curl iputils-ping net-tools dnsutils

# install SimBricks corundum dependencies
RUN apt install -y python3 python3-pip gtkwave git autoconf apt-utils \
  bc bison flex build-essential cmake doxygen g++

# install verilator separately, since it uses an older version
# and also needs a patch
COPY ./containers/corundum_patches/verilator.patch /tmp/
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
COPY ./nics/corundum/fpga/common/lib /corundum/lib
COPY ./nics/corundum/fpga/common/rtl /corundum/rtl
COPY ./nics/corundum_if/ /corundum/

# overwrite files with errors, with patches written by SimBricks devs
COPY ./containers/corundum_patches/port.v /corundum/rtl/port.v
COPY ./containers/corundum_patches/dma_client_axis_sink.v /corundum/lib/pcie/rtl/dma_client_axis_sink.v

ENTRYPOINT [ "sleep", "infinity" ]

# run from repo root:
# docker build -t corundum_test -f containers/corundum.Dockerfile .
# docker run -d --name corundum_tb corundum_test
# docker exec -it corundum_tb bash
