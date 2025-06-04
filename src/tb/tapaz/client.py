from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

import time

from netlib.iproute import IPRoute
from netlib.tap import Tap

ipr = IPRoute()

tom = Tap(is_client=True)

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

# while True:
if __name__ == "__main__":
    # Send at Layer 2 (Ethernet layer)
    tom.send(packet)

    time.sleep(2)
