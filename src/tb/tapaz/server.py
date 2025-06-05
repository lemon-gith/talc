import asyncio

# from cocotbext.eth.eth_mac import EthMacFrame
# from scapy.packet import Packet

from netlib.iproute import IPRoute
from netlib.tap import Tap


class TAPServer:
    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self, tb):
        # instantiate TAP device
        self.tap = Tap()

        # attach to the tesbench (for access to DUT)
        self.tb = tb

        # get the servers up and running
        self._start()

    def _start(self):
        """Starts tap and mac servers"""
        # TODO: why do I need to wrap functions in while True
        # for asyncio to keep running them?
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.taptask = self.loop.create_task(
            self._serve_tap(), name="TapServer"
        )
        self.mactask = self.loop.create_task(
            self._serve_mac(), name="McServer"
        )

        self.loop.run_forever()


    async def serve_tap(self):
        # TODO: rewrite this code to work for all interfaces
        iface = self.tb.driver.interfaces[0]

        self.tb.log.info("TAPServer.serve_tap: Listening for packet...")

        packet = self.tap.listen()

        self.tb.log.info("TAPServer.serve_tap: Got a packet!")

        await self.tb.port_mac[iface.index*iface.port_count].rx.send(packet)
            
    async def serve_mac(self):
        # TODO: rewrite this code to work for all interfaces
        iface = self.tb.driver.interfaces[0]

        self.tb.log.info("TAPServer.serve_mac: Listening for packet...")

        packet = await self.tb.port_mac[iface.index*iface.port_count].tx.recv()

        self.tb.log.info("TAPServer.serve_mac: Got a packet!")

        self.tap.send(packet)


    async def _serve_tap(self):
        """wrapping serve_tap because I can't figure out asyncio's problems"""
        while True:
            await self.serve_tap()

    async def _serve_mac(self):
        """wrapping serve_mac because I can't figure out asyncio's problems"""
        while True:
            await self.serve_mac()


    async def _send_to_nic(self):
        # TODO: impl this, to be called by serve_tap, _if necessary_,
        # I imagine the translation layer should, at worst, be:
        # pkt: EthMacFrame = port_mac.tx.recv()
        # packet: Packet = Ether(pkt.data)
        pass


class FaucetServer:
    """Just for playing around"""

    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self):
        # instantiate TAP device
        self.faucet = Tap()

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
        # cocotb is stubborn and refuses to be killed externally,
        # so it must be terminated from within
        if load == "die":
            exit(0)
        else:
            ls(packet)

        print("listening for next packet...")

        self.listen()


if __name__ == "__main__":
    from misc_utils import FakeTB

    fiona = TAPServer(FakeTB())

    print("outside loop...")
    # while True:
    #     try:
    #         fiona.listen()
    #     except KeyboardInterrupt:
    #         print("\naight, shutting down :)")
    #         exit(0)
