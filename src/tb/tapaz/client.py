"""A singleton module containing a TAP Client, mainly just for testing"""

from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.packet import Packet

from netlib.iproute import IPRoute
from netlib.tap import Tap


class TAPClient:
    """
    Currently just a simple class providing an easy send fn for a TAP iface
    """
    ipr = IPRoute()

    def __init__(self, devname: str = "tap0"):
        self.tap = Tap(devname, is_client=True)

    def send(self, packet: Packet):
        self.tap.send(packet)


if __name__ == "__main__":
    tom = TAPClient()
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

    # Send at Layer 2 (Ethernet layer)
    tom.send(packet)
