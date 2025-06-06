from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

from tapaz.client import TAPClient


# these are just some useful lines to preload into the scapy terminal, in one go

tac = TAPClient()

payload = bytes(b"Greetings, weary traveller. Wait no, it is I who has travelled...")

eth = Ether(src="5A:51:52:53:54:55", dst="ff:ff:ff:ff:ff:ff")

ip = IP(src="10.0.0.2", dst="10.0.0.1")

udp = UDP(sport=12345, dport=8200)

pkt = eth / ip / udp / payload

# Send at Layer 2 (Ethernet layer)
# tac.send(pkt)  # uncomment if you want to auto-send packet on load

# to read this into interpreter env :)
# exec(open("tapaz/preloader.py").read())
