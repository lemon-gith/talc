import cocotb
from decimal import Decimal
from cocotb.triggers import Timer

from cocotbext.eth import EthMacFrame

from scapy.layers.inet import IP, UDP, TCP
from scapy.layers.l2 import Ether
from scapy.packet import Packet

from netlib.iproute import IPRoute


class SimpleServer:
    """The server emulating the host logic, has no knowledge of the TAP"""
    # instantiate ip helper
    ipr = IPRoute()

    def __init__(self, tb, app_id: int = 0):
        """a simple server :)

        Parameters
        ----------
        tb: TB
            the testbench instance being used for the testing

        app_id: int = 0
            which app do you want the server to run:

            0. echo
            1. ping
            2. counter
        """
        # attach to the tesbench (for access to DUT)
        self.tb = tb

        # if you write more apps, add them here
        self.apps = [
            self.echo,
            self.ping,
            self.counter,
        ]

        if app_id >= len(self.apps):
            err_msg = f"err (SimpleServer.__init__): invalid app_id, {app_id}, "

            if app_id == len(self.apps):
                err_msg += f"there are only {len(self.apps)} apps available"
            else:
                err_msg += f"the {len(self.apps)} available apps are 0-indexed"

            raise ValueError(err_msg)

        self.app = self.apps[app_id]

        addr_info = self.ipr.get_addr_info()

        self.eth_addr = addr_info['eth'][0]['addr']
        self.ip_addr = addr_info['ip'][0]['addr']

        # save for later, just in case
        self.addr_info = addr_info

        # finally, get the server started
        cocotb.start_soon(self._serve())


    def echo(self, packet: Packet):
        """just blindly sends the exact same packet out"""
        self.tb.log.info("SimpleServer.serve.echo: send it back!")
        return packet

    def ping(self, packet: Packet):
        """just readjusts source and destination values, then returns"""
        self.tb.log.info("SimpleServer.serve.ping: tweaking addresses")
        if Ether in packet:
            packet[Ether].dst = packet[Ether].src
            packet[Ether].src = self.eth_addr
        if IP in packet:
            packet[IP].dst = packet[IP].src
            packet[IP].src = self.ip_addr
        if UDP in packet:
            packet[UDP].sport, packet[UDP].dport = (
                packet[UDP].dport, packet[UDP].sport
            )
        # adding this for completeness for now
        if TCP in packet:
            packet[TCP].sport, packet[TCP].dport = (
                packet[TCP].dport, packet[TCP].sport
            )

        return packet

    def counter(self, packet: Packet):
        """just increments the value and sends it back"""
        self.tb.log.info("SimpleServer.serve.counter: trying to count")
        try:
            packet.load = bytes(str(int(packet.load) + 1), encoding='ascii')
        except ValueError as e:
            self.tb.log.warning(f"warn (SimpleServer.counter):\n{e}")
            packet.load = "0"

        # wrap in ping to sort out src/dst
        return self.ping(packet)

    def _handler(self, packet: Packet):
        self.tb.log.info("SimpleServer.serve._handler: handling packet")
        return self.app(packet)


    def _insidious_insider(self, packet: Packet):
        """this one is out to get you...

        Just a little function that tests whether or not
        the packet is passed through DUT correctly
        """
        class YouHaveBeenPoisoned(BaseException): ...
        # these are the commands that will initiate shutdown of the testbench
        wakewords = {"terminate", "die", "exit", "quit", "kill"}


        if not hasattr(packet, 'load'):
            self.tb.log.info(
                f"SimpleServer.serve._insidious_insider: payload DNE - {packet}"
            )
            return

        try:
            payload = packet.load.decode('utf-8')
        except UnicodeDecodeError as err:
            self.tb.log.info(
                "SimpleServer.serve._insidious_insider: "
                + f"payload is not valid UTF-8 ({err}) - {packet}"
            )
            return

        self.tb.log.info(
            "<CORYSUMMARY> SimpleServer.serve._insidious_insider:"
            + f"inspecting - {payload}"
        )
        if payload in wakewords:
            raise YouHaveBeenPoisoned(
                "SimpleServer.serve._insidious_insider:"
                + f"received wakeword '{payload}'"
            )


    async def serve(self):
        # TODO: rewrite this code to work for all interfaces
        iface = self.tb.driver.interfaces[0]

        self.tb.log.info("SimpleServer.serve: Listening for data...")

        pkt: EthMacFrame = await iface.recv()

        # turn EthMacFrame.data (raw bytes) into scapy packet for ease-of-use
        packet = Ether(pkt.data)

        self.tb.log.info(
            f"<CORYSUMMARY> SimpleServer.serve: Handling packet - {packet!r}"
        )

        self._insidious_insider(packet)
        packet = self._handler(packet)

        self.tb.log.info(
            f"<CORYSUMMARY> SimpleServer.serve: App response - {packet!r}"
        )

        bytepacket = packet.build()

        # TODO: extend server support for all other start_xmit args
        await iface.start_xmit(bytepacket, 0)

        self.tb.log.info(
            f"SimpleServer.serve: Packet transmitted - {bytepacket!r}"
        )

    async def _serve(self):
        """wrapping serve because I think the code looks neater this way?"""
        while True:
            await self.serve()
            await Timer(Decimal(2), 'us')


if __name__ == "__main__":
    from mock_utils import FakeTB

    # this no longer works with the cocotb-linked system :(
    sara = SimpleServer(FakeTB(), app_id=2)
