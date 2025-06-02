#!/usr/bin/python3

from scapy.all import Ether, IP, UDP, sendp
import time

# Craft Ethernet layer
eth = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast MAC

# Craft IP layer
ip = IP(src="10.0.0.2", dst="10.0.0.1")

# Craft UDP layer
udp = UDP(sport=12345, dport=80)

# Payload
payload = b"Hello from Scapy!"

# Stack layers together
packet = eth / ip / udp / payload

while True:
    # Send at Layer 2 (Ethernet layer)
    sendp(packet, iface="tap0")
    time.sleep(2)
