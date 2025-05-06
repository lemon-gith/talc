#!/bin/bash


DEFAULT_CLIENT_IP="10.0.0.2/24"
DEFAULT_SERVER_IP="10.0.0.3/24"

# provide some help, if needed
case $1 in
  -h | --help | h | help)
    if [ "$EUID" -ne 0 ]; then
      echo -n "Run as root: "
    else
      echo -n "Usage: "
    fi
    echo -e "$0 [CLIENT_IP] [SERVER_IP]\n"
    echo "This script creates a || nsc - br0 - nss || topology, for now"
    echo -e "So, two namespaces, connected via a bridge using veth pairs.\n"
    echo "Watch out for possible name conflicts, check your existing devices:"
    echo "- namespaces: nsc, nss"
    echo "- net bridge: br0"
    echo "- veth pairs: veth-c, veth-brc, veth-s, veth-brs"
    echo "- 2 ip addrs: \$1 or $DEFAULT_CLIENT_IP, \$2 or $DEFAULT_SERVER_IP"
    exit 0
    ;;
esac

# must be run as root, since root privileges are required for most ip commands
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 2
fi

client_ip=${1:-$DEFAULT_CLIENT_IP}
server_ip=${2:-$DEFAULT_SERVER_IP}


## SETUP ##
# create bridge
ip link add br0 type bridge
ip link set br0 up

# create namespaces
ip netns add nsc
ip netns add nss

# create veth pairs
ip link add veth-c type veth peer name veth-brc
ip link add veth-s type veth peer name veth-brs

## CONFIGURE ##
# connect client veth pair
ip link set veth-c netns nsc
ip link set veth-brc master br0

# set up client the veth pair
ip netns exec nsc ip address add $client_ip dev veth-c
ip netns exec nsc ip link set veth-c up
ip link set veth-brc up

# connect server veth pair
ip link set veth-s netns nss
ip link set veth-brs master br0

# set up server the veth pair
ip netns exec nss ip address add $server_ip dev veth-s
ip netns exec nss ip link set veth-s up
ip link set veth-brs up

## TAP ##

# ??????


