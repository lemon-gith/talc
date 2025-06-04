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
