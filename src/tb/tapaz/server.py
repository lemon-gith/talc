import cocotb
from cocotb.triggers import Timer
from decimal import Decimal

from cocotbext.eth.eth_mac import EthMacFrame
from scapy.layers.l2 import Ether
# from scapy.packet import Packet

from netlib.iproute import IPRoute
from netlib.tap import Tap


class TAPServer:
    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self, tb):
        # instantiate TAP device
        self.tap = Tap(no_ip=True)

        # attach to the tesbench (for access to DUT)
        self.tb = tb

        # get the servers up and running
        cocotb.start_soon(self._serve_mac())
        cocotb.start_soon(self._serve_tap())


    async def serve_tap(self):
        # TODO: rewrite this code to work for all interfaces
        iface = self.tb.driver.interfaces[0]

        self.tb.log.info("TAPServer.serve_tap: Listening for packets...")

        # Note: this is the important blocking call,
        # nothing super interesting should happen until a packet is received.
        packet = self.tap.listen()

        self.tb.log.info(
            f"<CORYSUMMARY> TAPServer.serve_tap: Got a frame! - {packet!r}"
        )

        # EthMacRx.send actually wraps raw bytes in EthMacFrame for us!
        # its constructor also safely transfers data from one EMF to another, so
        # I'm wrapping it just in case a cosmic ray makes it skips that line...
        frame = EthMacFrame(packet.build())

        self.tb.log.info(
            f"<CORYSUMMARY> TAPServer.serve_tap: repacked frame - {frame!r}"
        )

        # as we're currently locked to iface 0, this should be using port_mac 0
        await self.tb.port_mac[iface.index*iface.port_count].rx.send(frame)

        self.tb.log.info("TAPServer.serve_tap: frame sent to DUT!")


    async def serve_mac(self):
        # TODO: rewrite this code to work for all interfaces
        iface = self.tb.driver.interfaces[0]

        self.tb.log.info("TAPServer.serve_mac: Listening for packet...")

        frame = await self.tb.port_mac[iface.index*iface.port_count].tx.recv()

        self.tb.log.info(
            f"<CORYSUMMARY> TAPServer.serve_mac: Got a frame - {frame}"
        )

        # extract payload from their L2 frame, then wrap with a scapy L2 header
        eth_frame = Ether(frame.data)
        self.tap.send(eth_frame)

        self.tb.log.info(
            f"<CORYSUMMARY> TAPServer.serve_mac: Sent frame - {eth_frame!r}"
        )

    async def _serve_tap(self):
        """wrapping serve_tap so it'll run 'til the test comes crumbling down"""
        while True:
            await self.serve_tap()
            await Timer(Decimal(12), 'us')

    async def _serve_mac(self):
        """wrapping serve_tap so it'll run 'til the cows come home"""
        while True:
            await self.serve_mac()
            await Timer(Decimal(2), 'us')


class FaucetServer:
    """Just for playing around

    Just for testing Tap() functionality
    """

    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self, **kwargs):
        # instantiate TAP device
        self.faucet = Tap(**kwargs)

    def listen(self):
        # since these modules are only needed in here
        from scapy.layers.inet import IP
        from scapy.packet import ls

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
        # SIGINT wouldn't shut down cocotb, so to terminate it from within...
        # this has now become the '_insidious_insider' testing function :)
        if load == "die":
            exit(0)
        else:
            ls(packet)

        print("listening for next packet...")

        self.listen()


# I don't think TAPServer still works with cocotb-linked system :(
if __name__ == "__main__":
    # from mock_utils import FakeTB

    fiona = FaucetServer()
