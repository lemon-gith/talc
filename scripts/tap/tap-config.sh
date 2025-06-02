#!/bin/bash

set -xe

sudo ip link set tap0 up
sudo ip addr add 10.0.0.1/24 dev tap0
