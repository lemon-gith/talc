from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether


fake_packet = Ether(
    src="00:00:00:00:00:00", dst="ff:ff:ff:ff:ff:ff"
) / IP(
    src="172.17.0.71", dst="172.17.255.255"
) / UDP(
    sport=6006, dport=1234
) / b"fake payload"

class FakeTB:
    """Emulates attrs, nothing more

    If you need more, pls do add more :)"""
    class FakeDriver:
        class FakeIface:
            index = 0
            port_count = 0
            async def recv(self):
                return fake_packet
            async def start_xmit(
                self, packet, tx_ring: int = 0,
                csum_start: int = 0, csum_offset: int = 0
            ):
                return


        interfaces = [FakeIface()]

    class FakePort:
        class FakeRx:
            async def send(self, _):
                return
        class FakeTx:
            async def recv(self):
                return fake_packet

        rx = FakeRx()
        tx = FakeTx()

    class FakeLogger:
        def info(self, msg: str):
            print(f"info: {msg}")
        def warning(self, msg: str):
            print(f"warning: {msg}")
        def warn(self, msg: str):
            """this method is deprecated, using `warning` instead"""
            self.warning(msg)

    driver = FakeDriver()
    port_mac = [FakePort()]
    log = FakeLogger()
