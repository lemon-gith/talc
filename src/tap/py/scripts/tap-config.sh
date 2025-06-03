#!/bin/bash

devname=${1:-tap0}

sudo ip link set $devname up
sudo ip addr add 10.0.0.1/24 dev $devname
