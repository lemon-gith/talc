# from scapy.layers.l2 import Ether
# from scapy.layers.inet import UDP
from scapy.layers.inet import IP

from scapy.packet import Packet
from scapy.packet import ls

from cocotbext.eth.eth_mac import EthMacFrame
from threading import Thread, current_thread

from netlib.iproute import IPRoute
from netlib.tap import Tap


class TAPServer:
    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self, tb):
        # instantiate TAP device
        self.faucet = Tap()

        # attach to the tesbench (for access to DUT)
        self.tb = tb

    def listen_tap(self):
        while True:
            # Send at Layer 2 (Ethernet layer)
            packet = self.faucet.listen()

            print("Got a packet!")

            # TODO: send to nic

            print("listening for next packet...")
            # TODO: thread this function

    def listen_mac(self):
        # TODO: impl this, to be threaded
        pass

    async def _send_to_nic(self):
        # TODO: impl this, to be called by _listen_tap
        pass

    # TODO: break this down into its separate parts to be split between
    # this server and SimpleServer
    async def nic_process(
        self, packet: Packet, iface_num: int = 0, tx_ring: int = 0,
        csum_start: int | None = None, csum_offset: int | None = None
    ):
        """Send a packet via the driver, through the NIC and pick it up from the MAC

        Basically having the NIC process the packet

        Parameters
        ----------
        packet: scapy.packet.Packet
            the packet you want to pass through the DUT

        iface_num: int = 0
            which interface number would you like to send the packet from?

        tx_ring: int = 0
            which transmission ring would you like to use?

        csum_start: int | None = None
            yk, I'm not quite sure... sth to do with the checksum

        csum_offset: int | None = None
            yk, I'm not quite sure... sth to do with the checksum

        Usage
        -----
        ```python
        await send_through_nic(tb, test_pkt)
        ```

        or

        ```python
        eth = Ether(src='5A:51:52:53:54:55', dst='DA:D1:D2:D3:D4:D5')
        ip = IP(src='192.168.1.100', dst='192.168.1.101')
        udp = UDP(sport=1, dport=42)
        payload = b"hiya"
        packet = eth / ip / udp / payload

        for iface_num in range(len(tb.driver.interfaces)):
            await simple_packet_firehose(tb, packet, iface_num)
        ```
        """
        iface = self.tb.driver.interfaces[iface_num]

        # transmit the packet using the driver
        await iface.start_xmit(packet.build(), tx_ring, csum_start, csum_offset)

        # catch the packet at the MAC port
        pkt = await self.tb.port_mac[iface_num].tx.recv()

        return pkt



class FaucetServer(TAPServer):
    """Just for playing around"""
    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self):
        # instantiate TAP device
        self.faucet = Tap()

    def listen(self):
        # Send at Layer 2 (Ethernet layer)
        packet = self.faucet.listen()

        print("Got a packet!", end=' ')

        ip_pkt = packet.getlayer(IP)

        if ip_pkt is None:
            print("but it had no IP header...")
            return

        ip_src, ip_dst = ip_pkt.fields["src"], ip_pkt.fields["dst"]

        my_ip = {"10.0.0.1", "10.0.0.255"}
        # if not from our little tap subnet, and not coming to us
        if not (
            ip_src.startswith("10.0.0.") and ip_dst in my_ip
        ):
            if ip_dst == "10.0.0.1":
                print(f"it was from a stranger: {ip_src}")
            else:
                print(f"it wasn't for me: {ip_dst}")
            return
        else:
            print()  # for the newline

        # grab payload
        load = packet.load.decode('utf-8')

        # was testing out this functionality to be ported into testbed:
        # cocotb is stubborn and refuses to be killed externally,
        # so it must be terminated from within
        if load == "die":
            exit(0)
        else:
            ls(packet)

        print("listening for next packet...")

        self.listen()


if __name__ == "__main__":
    tabby = FaucetServer()

    print("listening...")
    while True:
        try:
            tabby.listen()
        except KeyboardInterrupt:
            print("aight, shutting down :)")
            exit(0)
