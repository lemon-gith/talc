from threading import Thread, current_thread
import os
import sys
import time

# from pyutils.netlib.tap import Tap
from tapaz import TAPServer
from host.application import SimpleServer


import cocotb
from corunlib.testbench import TB
from corunlib import mqnic

# these are just a sanity check, to test that cocotb is still working correctly
# expected behaviour: first one should PASS, second one should FAIL
from tests.test import tell_me_the_truth, tell_me_lies  # noqa: F401 <- for ruff


@cocotb.test
async def run_testbed(dut):
    # ---------------- DUT initialisation, copied over ----------------
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

    # TODO: instantiate servers

    tabby = TAPServer()

    # tb.log.info("Send a single packet: client.py test")
    print("listening...")
    while True:
        tabby.listen()

    # tabby = TAPClient()

    # payload = bytes(
    #     b"Greetings, weary traveller. Wait no, it is I who has travelled..."
    # )
    # udp = UDP(sport=12345, dport=8200)
    # ip = IP(src="10.0.0.2", dst="10.0.0.1")
    # eth = Ether(src="5A:51:52:53:54:55", dst="ff:ff:ff:ff:ff:ff")
    # test_pkt = eth / ip / udp / payload

    # pkt = await nic_process(tb, test_pkt)

    # print(f"ETH PACKET INFORMATION: {pkt.data}")

    # tabby.send(pkt)
    # time.sleep(5)

    # try to see if you can get the checksum working for a basic send
    # if tb.driver.interfaces[0].if_feature_tx_csum:
        # test_pkt2 = test_pkt.copy()
        # test_pkt2[UDP].chksum = scapy.utils.checksum(bytes(test_pkt2[UDP]))

        # await tb.driver.interfaces[0].start_xmit(test_pkt2.build(), 0, 34, 6)
