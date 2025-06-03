from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

from scapy.packet import ls

from pathlib import Path

from netlib.iproute import IPRoute
from netlib.tap import Tap

# instantiate ip helper
ipr = IPRoute()

# instantiate TAP device
faucet = Tap(no_su=True, config_script=Path("./tap-config.sh"))


print("listening...")
while True:
    # Send at Layer 2 (Ethernet layer)
    req = faucet.listen()

    ip_pkt = req.getlayer(IP)

    if ip_pkt is None:
        continue

    ip_src, ip_dst = ip_pkt.fields["src"], ip_pkt.fields["dst"]

    # if not from our little tap subnet, and not coming to us
    if not (
        ip_src.startswith("10.0.0.") and ip_dst.fields["dst"] == "10.0.0.1"
    ):
        continue

    print("here're the message deets:")

    print("ls:")
    ls(req)
    print("\n")

    print("short:")
    req.show()
    print("\n")

    print(f"IP: src = {ip_src}, dst = {ip_dst}\n")

    print("listening...")
