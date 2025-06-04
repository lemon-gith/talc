# typing imports
from scapy.packet import Packet

# module imports
import os
import struct
import sys

import scapy.utils
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

import cocotb
from corunlib.testbench import TB
from corunlib import mqnic

# these are just a sanity check, to test that cocotb is still working correctly
# expected behaviour: first one should PASS, second one should FAIL
from tests.test import tell_me_the_truth, tell_me_lies  # noqa: F401 <- for ruff


async def nic_process(
    tb: TB, packet: Packet, iface_num: int = 0, tx_ring: int = 0,
    csum_start: int | None = None, csum_offset: int | None = None
):
    """Send a packet via the driver, through the NIC and pick it up from the MAC

    Basically having the NIC process the packet

    Parameters
    ----------
    tb: TB
        the testbench instance being used for the testing

    packet: scapy.packet.Packet
        the packet you want the DUT to send

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
    iface = tb.driver.interfaces[iface_num]

    # transmit the packet using the driver
    await iface.start_xmit(packet.build(), tx_ring, csum_start, csum_offset)

    # catch the packet at the MAC port
    pkt = await tb.port_mac[iface_num].tx.recv()

    return pkt


@cocotb.test
async def run_testbed(dut):
    # -------------------- DUT initialisation, copied from  --------------------
    # Initialise TestBench DUT instance
    tb = TB(dut, msix_count=2**len(dut.core_pcie_inst.irq_index))

    await tb.init()

    tb.log.info("Init driver")
    if (device := tb.rc.find_device(tb.dev.functions[0].pcie_id)) is not None:
        await tb.driver.init_pcie_dev(device)
    for interface in tb.driver.interfaces:
        await interface.open()

    # enable queues
    tb.log.info("Enable queues")
    for interface in tb.driver.interfaces:
        await interface.sched_blocks[0].schedulers[0].rb.write_dword(
            mqnic.MQNIC_RB_SCHED_RR_REG_CTRL, 0x00000001
        )
        for k in range(len(interface.txq)):
            await interface.sched_blocks[0].schedulers[0].hw_regs.write_dword(
                4*k, 0x00000003
            )

    # wait for all writes to complete
    await tb.driver.hw_regs.read_dword(0)
    tb.log.info("Init complete")

    # -------------------- Start interactive testbed --------------------

    tb.log.info("Send and receive single packet")
