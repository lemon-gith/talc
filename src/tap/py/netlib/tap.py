from scapy.layers.tuntap import TunTapInterface
from scapy.sendrecv import sendp, srp, srp1

from scapy.packet import Packet

from pathlib import Path
import subprocess
import time

from netlib.iproute import IPRoute

ipr = IPRoute()

class UsageError(BaseException): ...


class Tap:
    """A wrapper around a linux tap interface"""
    def __init__(
        self, devname: str = "tap0", is_client: bool = False,
        no_su: bool = False, config_script: Path = Path("")
    ):
        """Either create and setup or attach to existing tap interface

        Parameters
        ----------
        devname: str = "tap0"
            The name of the device you want to setup, should be "tap"-something

        is_client: bool = False
            Is this Tap() instance a client to an existing Tap device, or not?

        config_path: pathlib.Path = ""
            the path to the interface configuration script,
            this MUST be set, if no_su is set to True

        no_su: bool = False
            set to True if you cannot run this script as root

            Note: should this be the case, you must at least do these 3 things:

            1. You must at least give your python intepreter these capabilities:
            `cap_net_admin,cap_net_raw=eip`

            2. You must have authenticated your superuser in the same terminal,
            within the past 5 minutes
            (or however long your `timestamp_timeout` is set to)

            3. You must provide a shell file that will setup and configure
            the tap interface once it's created here, , e.g.
            ```
        #!/bin/bash

        devname=${1:-tap0}

        sudo ip link set $devname up
        sudo ip addr add 10.0.0.1/24 dev $devname
            ```
        """
        self.dev = devname
        self.is_client = is_client

        # check if this device already exists
        out = ipr.link("show", self.dev)
        if out.is_ok:
            if is_client:
                print(f"Device '{self.dev}' already exists, using that...")
                return
            else:
                raise RuntimeError(
                    f"err (tap): Device '{self.dev}' already exists!"
                )

        # instantiate our wrapped tap device :D
        self.tap = TunTapInterface(devname, mode_tun=False)

        # set device up and give it an ip address
        if no_su:  # either without superuser, but lots of manual work
            if not config_script.exists():
                raise RuntimeError(
                    "You didn't pass a valid path to a config script"
                )

            out = subprocess.run(
                config_script.resolve(),
                capture_output=True, text=True, encoding='utf-8'
            )
            if out.returncode != 0:
                raise RuntimeError(f"err (tap): {out.stderr}")
        else:  # or with superuser privileges, which is easier
            out = ipr.link('set', self.dev, 'up')

            if out.is_ok:
                out = out.unwrap()
            else:
                err = out.unwrap_err()
                print(f"err (tap):\n{err}")
                return

            out = ipr.addr("add", "10.0.0.1/24", "dev", self.dev)

            if out.is_ok:
                out = out.unwrap()
            else:
                err = out.unwrap_err()
                print(f"err (tap):\n{err}")
                return

        # give it a bit of time, idk
        time.sleep(1)

    def listen(self):
        if self.is_client:
            raise UsageError("err (tap): a client instance may not listen")

        packet = None
        while packet is None:
            packet = self.tap.recv()

        return packet

    def send(self, packet: Packet):
        """
        Parameters
        ----------
        packet: Packet
            the packet you wish to send to the TAP interface
        """
        if self.is_client:
            sendp(packet, iface=self.dev)
        else:
            self.tap.send(packet)

    def send_recv1(self, packet: Packet, timeout:int = 500):
        """Send a packet and receive the first response

        Just a wrapper around `scapy.sendrecv.srp1`,
        that sends and receives to the TAP interface

        Parameters
        ----------
        packet: Packet
            the packet you wish to send to the TAP interface
        """
        return srp1(packet, iface=self.dev, timeout=timeout)

    def send_recv(self, packet: Packet, timeout:int = 500):
        """Send a packet and returns all responses

        Just a wrapper around `scapy.sendrecv.srp`,
        that sends and receives to the TAP interface

        Parameters
        ----------
        packet: Packet
            the packet you wish to send to the TAP interface
        """
        return srp(packet, iface=self.dev, timeout=timeout)

    async def _handle(self):
        pass
