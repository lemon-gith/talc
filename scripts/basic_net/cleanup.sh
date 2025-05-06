#!/bin/bash

# provide some help, if needed
case $1 in
  -h | --help | h | help)
    if [ "$EUID" -ne 0 ]; then
      echo -n "Run as root: "
    else
      echo -n "Usage: "
    fi
    echo "$0"
    echo "This script cleans up the network namespaces and bridge created by setup.sh"
    exit 0
    ;;
esac

# must be run as root, since root privileges are required for most ip commands
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 2
fi

# delete namespaces
ip netns del nsc
ip netns del nss

# delete bridge
ip link del br0

echo "Squeaky clean :)"
