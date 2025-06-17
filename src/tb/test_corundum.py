# SPDX-License-Identifier: BSD-2-Clause-Views
# Copyright (c) 2021-2023 The Regents of the University of California

# typing imports
from decimal import Decimal
from cocotbext.axi import MemoryRegion
from scapy.packet import Packet

# utility imports
from contextlib import contextmanager

# module imports
import os
import struct
import sys

import scapy.utils
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

import cocotb
from cocotb.triggers import RisingEdge, Timer

from corunlib.testbench import TB

# Note: just importing the fn allows cocotb to reach out and access the test fn
# from tests.test import tell_me_the_truth, tell_me_lies

# import mqnic, if Python can't find it in repo, hijack system PATH
try:
    import corunlib.mqnic as mqnic
except ImportError:
    # attempt import from current directory
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "corunlib"))
    try:
        import corunlib.mqnic as mqnic
    finally:
        # clear this item from PATH once import is complete (polite)
        del sys.path[0]


@contextmanager
def loopback_enabled(tb: TB, enabled: bool = True):
    """temporary loopback enabling utility

    Parameters
    ----------
    tb: TB
        the testbench instance for which you want loopback temporarily enabled
    enabled: bool
        should loopback be enabled?
        this option is useful for parameterised testing

    Returns
    -------
    enabled: bool
        because I need to yield something, since this is technically a generator

    Usage
    -----
    ```
    with loopback_enabled(tb):
        ...
    ```
    """
    tb.loopback_enable = enabled

    # go back to context body
    yield enabled

    tb.loopback_enable = False


# abstract multiple tests into this one heavily-parameterised function
async def simple_packet_firehose(
    tb: TB, interface: mqnic.Interface, count: int = 0, size: int = 0,
    tx_ring: int = 0, enable_loopback: bool = True,
    csum_start: int | None = None, csum_offset: int | None = None,
    header_stack: Packet | None = None,
    data: list[bytearray] | None = None, assert_data: bool = True,
    queues: set[int] | None = None
):
    """Send different configurations of packet barrages over desired interface

    Crucially, this only handles simple, linear firehosing operations, e.g.
    it doesn't support send-all then recv-all, only (send+recv)-all
    (cf. Limitations section for more info.)

    Parameters
    ----------
    tb: TB
        the testbench instance being used for the testing

    interface: mqnic.Interface
        the interface that you would like to firehose packets from

    count: int = 0
        how many packets should be sent?
        default value of 0 will produce no packets

    size: int = 0
        and how large do you want those packets?
        default value of 0 produces empty packets

    tx_ring: int = 0
        which transmission ring would you like to use?

    enable_loopback: bool = True
        should automatic MAC loopback be enabled?
        default value of True will keep this enabled,
        I'm not too sure why you'd want it disabled...

    csum_start: int | None = None
        yk, I'm not quite sure... sth to do with the checksum

    csum_offset: int | None = None
        yk, I'm not quite sure... sth to do with the checksum

    header_stack: Packet | None = None
        just the headers that you want to encapsulate the payload in.
        generally, if this is not `None`,
        you may want to look at setting `assert_data` to `False`, too

    data: list[bytearray] | None = None
        pre-built packets or payloads (if `header_stack` is not `None`)

    assert_data: bool = True
        do you want to assert that the received packet's data == sent payload?
        tends to be disabled for tests using actual packet headers:
        those headers are not in the payload

    queues: set[int] | None = None
        pass a set to be informed of which queues, packets have been recevied at

    Usage
    -----
    ```python
    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 1514)
    ```

    or

    ```python
    eth = Ether(src='5A:51:52:53:54:55', dst='DA:D1:D2:D3:D4:D5')
    ip = IP(src='192.168.1.100', dst='192.168.1.101')
    udp = UDP(sport=1, dport=42)

    for iface in tb.driver.interfaces:
        await simple_packet_firehose(
            tb, iface, 64, 1514,
            header_stack=(eth / ip / udp)
        )
    ```

    Limitations
    -----------
    - `header_stack` cannot use variable values, e.g. IP ranges, port ranges
        - workaround is to build variable headered packets outside
          then pass them in using the `data` kwarg

    DESIGNED FOR THIS:
    ```python
    for i in range(fred):
        send()
        recv()
        assert
    ```
    CANNOT DO THIS:
    ```python
    for i in range(fred):
        send()
        # other logic

    # other logic

    for i in range(fred):
        recv()
        assert
    ```
    """
    if data is None:
        data = [
            bytearray([(x+k) % 256 for x in range(size)]) for k in range(count)
        ]

    if header_stack is None:
        pkts = data
    else:
        pkts = [(header_stack / payload).build() for payload in data]

    # commence firehosing
    with loopback_enabled(tb, enable_loopback):
        for pkt in pkts:
            await interface.start_xmit(pkt, tx_ring, csum_start, csum_offset)

        for k in range(count):
            pkt = await interface.recv()

            if pkt is None:
                raise ValueError("Packet is None")

            tb.log.info("Packet: %s", pkt)

            if assert_data:
                assert pkt.data == pkts[k]

            if interface.if_feature_rx_csum:
                assert pkt.rx_checksum == ~scapy.utils.checksum(
                    bytes(pkt.data[14:])
                ) & 0xffff

            if queues is not None:
                queues.add(pkt.queue)

    return queues


async def dma_bench_test(tb: TB):
    """
    Just the DMA bench test extracted from\\
    `/fpga/app/dma_bench/tb/test_mqnic_core_pcie_us.py`
    """

    app_reg_blocks = mqnic.RegBlockList()
    await app_reg_blocks.enumerate_reg_blocks(tb.driver.app_hw_regs)

    dma_bench_rb = app_reg_blocks.find(0x12348101, 0x00000100)

    if dma_bench_rb is None:
        raise ValueError("dma_bench_rb is None")

    mem: MemoryRegion = tb.rc.mem_pool.alloc_region(16*1024*1024)
    # I can't really add annotations to return type of the library fn
    mem_base: int = mem.get_absolute_address(0) # type: ignore

    tb.log.info("Test DMA")

    # write packet data
    mem[0:1024] = bytearray([x % 256 for x in range(1024)])

    # write pcie read descriptor
    await dma_bench_rb.write_dword(0x100, (mem_base+0x0000) & 0xffffffff)
    await dma_bench_rb.write_dword(0x104, (mem_base+0x0000 >> 32) & 0xffffffff)
    await dma_bench_rb.write_dword(0x108, 0x100)
    await dma_bench_rb.write_dword(0x110, 0x400)
    await dma_bench_rb.write_dword(0x114, 0xAA)

    await Timer(Decimal(2000), 'ns')

    # read status
    val = await dma_bench_rb.read_dword(0x000118)
    tb.log.info("Status: 0x%x", val)
    assert val == 0x800000AA

    # write pcie write descriptor
    await dma_bench_rb.write_dword(0x200, (mem_base+0x1000) & 0xffffffff)
    await dma_bench_rb.write_dword(0x204, (mem_base+0x1000 >> 32) & 0xffffffff)
    await dma_bench_rb.write_dword(0x208, 0x100)
    await dma_bench_rb.write_dword(0x210, 0x400)
    await dma_bench_rb.write_dword(0x214, 0x55)

    await Timer(Decimal(2000), 'ns')

    # read status
    val = await dma_bench_rb.read_dword(0x000218)
    tb.log.info("Status: 0x%x", val)
    assert val == 0x80000055

    tb.log.info("%s", mem.hexdump_str(0x1000, 64))

    assert mem[0:1024] == mem[0x1000:0x1000+1024]

    tb.log.info("Test immediate write")

    # write pcie write descriptor
    await dma_bench_rb.write_dword(0x200, (mem_base+0x1000) & 0xffffffff)
    await dma_bench_rb.write_dword(0x204, (mem_base+0x1000 >> 32) & 0xffffffff)
    await dma_bench_rb.write_dword(0x208, 0x44332211)
    await dma_bench_rb.write_dword(0x210, 0x4)
    await dma_bench_rb.write_dword(0x214, 0x800000AA)

    await Timer(Decimal(2000), 'ns')

    # read status
    val = await dma_bench_rb.read_dword(0x000218)
    tb.log.info("Status: 0x%x", val)
    assert val == 0x800000AA

    tb.log.info("%s", mem.hexdump_str(0x1000, 64))

    assert mem[0x1000:0x1000+4] == b'\x11\x22\x33\x44'

    tb.log.info("Test DMA block operations")

    region_len = 0x2000
    src_offset = 0x0000
    dest_offset = 0x4000

    block_size = 256
    block_stride = block_size
    block_count = 32

    # write packet data
    mem[src_offset:src_offset+region_len] = bytearray([x % 256 for x in range(region_len)])

    # disable interrupts
    await dma_bench_rb.write_dword(0x00C, 0)

    # configure operation (read)
    # DMA base address
    await dma_bench_rb.write_dword(0x380, (mem_base+src_offset) & 0xffffffff)
    await dma_bench_rb.write_dword(0x384, (mem_base+src_offset >> 32) & 0xffffffff)
    # DMA offset address
    await dma_bench_rb.write_dword(0x388, 0)
    await dma_bench_rb.write_dword(0x38c, 0)
    # DMA offset mask
    await dma_bench_rb.write_dword(0x390, region_len-1)
    await dma_bench_rb.write_dword(0x394, 0)
    # DMA stride
    await dma_bench_rb.write_dword(0x398, block_stride)
    await dma_bench_rb.write_dword(0x39c, 0)
    # RAM base address
    await dma_bench_rb.write_dword(0x3c0, 0)
    await dma_bench_rb.write_dword(0x3c4, 0)
    # RAM offset address
    await dma_bench_rb.write_dword(0x3c8, 0)
    await dma_bench_rb.write_dword(0x3cc, 0)
    # RAM offset mask
    await dma_bench_rb.write_dword(0x3d0, region_len-1)
    await dma_bench_rb.write_dword(0x3d4, 0)
    # RAM stride
    await dma_bench_rb.write_dword(0x3d8, block_stride)
    await dma_bench_rb.write_dword(0x3dc, 0)
    # clear cycle count
    await dma_bench_rb.write_dword(0x308, 0)
    await dma_bench_rb.write_dword(0x30c, 0)
    # block length
    await dma_bench_rb.write_dword(0x310, block_size)
    # block count
    await dma_bench_rb.write_dword(0x318, block_count)
    await dma_bench_rb.write_dword(0x31c, 0)
    # start
    await dma_bench_rb.write_dword(0x300, 1)

    for k in range(10):
        cnt = await dma_bench_rb.read_dword(0x318)
        await Timer(Decimal(1000), 'ns')
        if cnt == 0:
            break

    # configure operation (write)
    # DMA base address
    await dma_bench_rb.write_dword(0x480, (mem_base+dest_offset) & 0xffffffff)
    await dma_bench_rb.write_dword(0x484, (mem_base+dest_offset >> 32) & 0xffffffff)
    # DMA offset address
    await dma_bench_rb.write_dword(0x488, 0)
    await dma_bench_rb.write_dword(0x48c, 0)
    # DMA offset mask
    await dma_bench_rb.write_dword(0x490, region_len-1)
    await dma_bench_rb.write_dword(0x494, 0)
    # DMA stride
    await dma_bench_rb.write_dword(0x498, block_stride)
    await dma_bench_rb.write_dword(0x49c, 0)
    # RAM base address
    await dma_bench_rb.write_dword(0x4c0, 0)
    await dma_bench_rb.write_dword(0x4c4, 0)
    # RAM offset address
    await dma_bench_rb.write_dword(0x4c8, 0)
    await dma_bench_rb.write_dword(0x4cc, 0)
    # RAM offset mask
    await dma_bench_rb.write_dword(0x4d0, region_len-1)
    await dma_bench_rb.write_dword(0x4d4, 0)
    # RAM stride
    await dma_bench_rb.write_dword(0x4d8, block_stride)
    await dma_bench_rb.write_dword(0x4dc, 0)
    # clear cycle count
    await dma_bench_rb.write_dword(0x408, 0)
    await dma_bench_rb.write_dword(0x40c, 0)
    # block length
    await dma_bench_rb.write_dword(0x410, block_size)
    # block count
    await dma_bench_rb.write_dword(0x418, block_count)
    await dma_bench_rb.write_dword(0x41c, 0)
    # start
    await dma_bench_rb.write_dword(0x400, 1)

    for k in range(10):
        cnt = await dma_bench_rb.read_dword(0x418)
        await Timer(Decimal(1000), 'ns')
        if cnt == 0:
            break

    tb.log.info("%s", mem.hexdump_str(dest_offset, region_len))

    assert mem[src_offset:src_offset+region_len] == mem[dest_offset:dest_offset+region_len]

    tb.log.info("Test DRAM channels")

    index = 0
    while True:
        dram_test_rb = app_reg_blocks.find(0x12348102, 0x00000100, index)
        index = index+1

        if not dram_test_rb:
            break

        # configure FIFO
        await dram_test_rb.write_dword(0x48, (16*2**20)-1)
        await dram_test_rb.write_dword(0x4C, 0x00000000)

        # reset FIFO and data generator/checker
        await dram_test_rb.write_dword(0x20, 0x00000002)
        await dram_test_rb.write_dword(0x20, 0x00000202)

        await Timer(Decimal(100), 'ns')

        # enable FIFO
        await dram_test_rb.write_dword(0x20, 0x00000001)

        # enable data generation and checking
        await dram_test_rb.write_dword(0x68, 1024)
        await dram_test_rb.write_dword(0x6C, 1024)
        await dram_test_rb.write_dword(0x24, 0x00000101)

        # wait for transfer to complete
        while True:
            val = await dram_test_rb.read_dword(0x24)
            if val == 0:
                break

        await Timer(Decimal(1000), 'ns')


async def single_packet_test(tb: TB, interface: mqnic.Interface):
    """
    This test verifies that the DUT correctly delivers packets, 
    from one end to another; if the feature is enabled,
    it also verifies the EthMacFrame checksum integrity
    
    This test sends a single 'packet' of arbitrary data from the host,
    through the DUT, manually captures the packet at the MAC port,
    resends it back up through the same MAC port,
    and catches it back at the host
    """
    data = bytearray([x % 256 for x in range(1024)])

    await interface.start_xmit(data, 0)

    pkt = await tb.port_mac[interface.index*interface.port_count].tx.recv()
    tb.log.info("Packet: %s", pkt)

    await tb.port_mac[interface.index*interface.port_count].rx.send(pkt)

    pkt = await interface.recv()

    tb.log.info("Packet: %s", pkt)
    if interface.if_feature_rx_csum and pkt is not None:
        assert (
            pkt.rx_checksum == ~scapy.utils.checksum(
                bytes(pkt.data[14:])
            ) & 0xffff
        )


async def basic_checksum_test(tb: TB):
    """
    if the features are enabled,
    this test verifies checksum integrity for both the Tx and Rx,
    for both the interface and the MAC port

    This test sends a single packet with an arbitrary payload from the host,
    through the DUT, manually captures the packet at the MAC port,
    resends it back up through the same MAC port,
    and catches it back at the host
    """
    tb.log.info("RX and TX checksum tests")

    payload = bytes([x % 256 for x in range(256)])
    eth = Ether(src='5A:51:52:53:54:55', dst='DA:D1:D2:D3:D4:D5')
    ip = IP(src='192.168.1.100', dst='192.168.1.101')
    udp = UDP(sport=1, dport=2)
    test_pkt = eth / ip / udp / payload

    # if the tx iface impl transmission csum for UDP packet, compute it
    if tb.driver.interfaces[0].if_feature_tx_csum:
        test_pkt2 = test_pkt.copy()
        test_pkt2[UDP].chksum = scapy.utils.checksum(bytes(test_pkt2[UDP]))

        await tb.driver.interfaces[0].start_xmit(test_pkt2.build(), 0, 34, 6)
    else:
        await tb.driver.interfaces[0].start_xmit(test_pkt.build(), 0)

    # allegedly returns an ETH frame
    pkt = await tb.port_mac[0].tx.recv()
    tb.log.info("Packet: %s", pkt)

    await tb.port_mac[0].rx.send(pkt)

    pkt = await tb.driver.interfaces[0].recv()

    if pkt is None:
        raise ValueError("Packet is None")

    tb.log.info("Packet: %s", pkt)
    # if the rx iface impl transmission csum for UDP packet, check it
    if tb.driver.interfaces[0].if_feature_rx_csum:
        assert pkt.rx_checksum == ~scapy.utils.checksum(bytes(pkt.data[14:])) & 0xffff

    # validate that received ETH packet would build to original packet
    assert Ether(pkt.data).build() == test_pkt.build()


async def queue_map_offset_test(tb: TB):
    for k in range(4):
        await tb.driver.interfaces[0].set_rx_queue_map_indir_table(0, 0, k)

        pkt_queue = await simple_packet_firehose(
            tb, tb.driver.interfaces[0], 1, 1024,
            assert_data=False, queues=set()
        )
        if pkt_queue is None:
            raise ValueError("returned queue was None")

        # pkt_queue should only have one element, if k is that element, good
        assert k in pkt_queue

    # reset indirection table
    await tb.driver.interfaces[0].set_rx_queue_map_indir_table(0, 0, 0)


async def q_map_rss_mask_test(tb: TB):
    await tb.driver.interfaces[0].set_rx_queue_map_rss_mask(0, 0x00000003)

    for k in range(4):
        await tb.driver.interfaces[0].set_rx_queue_map_indir_table(0, k, k)

    pkts = []
    count = 64

    payload = bytes([x % 256 for x in range(256)])
    eth = Ether(src='5A:51:52:53:54:55', dst='DA:D1:D2:D3:D4:D5')
    ip = IP(src='192.168.1.100', dst='192.168.1.101')

    for k in range(count):
        udp = UDP(sport=1, dport=k+0)
        test_pkt = eth / ip / udp / payload

        if tb.driver.interfaces[0].if_feature_tx_csum:
            test_pkt = test_pkt.copy()
            test_pkt[UDP].chksum = scapy.utils.checksum(bytes(test_pkt[UDP]))

        pkts.append(test_pkt.build())

    csum_start, csum_offset = None, None
    if tb.driver.interfaces[0].if_feature_tx_csum:
        csum_start, csum_offset = 34, 6

    queues = await simple_packet_firehose(
        tb, tb.driver.interfaces[0], count,
        queues=set(), assert_data=False, data=pkts,
        csum_start=csum_start, csum_offset=csum_offset
    )

    if queues is None:
        raise ValueError("SPF returned a queues object as None")

    assert len(queues) == 4

    # reset rss mask
    await tb.driver.interfaces[0].set_rx_queue_map_rss_mask(0, 0)


async def all_interfaces_test(tb):
    count = 64

    pkts = [bytearray([(x+k) % 256 for x in range(1514)]) for k in range(count)]

    with loopback_enabled(tb):
        for k, p in enumerate(pkts):
            await tb.driver.interfaces[k % len(tb.driver.interfaces)].start_xmit(p, 0)

        for k in range(count):
            pkt = await tb.driver.interfaces[k % len(tb.driver.interfaces)].recv()

            if pkt is None:
                raise ValueError("Packet is None")

            tb.log.info("Packet: %s", pkt)

            assert pkt.data == pkts[k]

            if tb.driver.interfaces[0].if_feature_rx_csum:
                assert pkt.rx_checksum == ~scapy.utils.checksum(
                    bytes(pkt.data[14:])
                ) & 0xffff


async def all_scheduler_blocks_test(tb: TB, interface: mqnic.Interface):
    for block in interface.sched_blocks:
        await block.schedulers[0].rb.write_dword(mqnic.MQNIC_RB_SCHED_RR_REG_CTRL, 0x00000001)
        await block.interface.set_rx_queue_map_indir_table(block.index, 0, block.index)
        for k in range(len(block.interface.txq)):
            if k % len(block.interface.sched_blocks) == block.index:
                await block.schedulers[0].hw_regs.write_dword(4*k, 0x00000003)
            else:
                await block.schedulers[0].hw_regs.write_dword(4*k, 0x00000000)

        await block.interface.ports[block.index].set_tx_ctrl(mqnic.MQNIC_PORT_TX_CTRL_EN)
        await block.interface.ports[block.index].set_rx_ctrl(mqnic.MQNIC_PORT_RX_CTRL_EN)

    count = 64

    pkts = [bytearray([(x+k) % 256 for x in range(1514)]) for k in range(count)]

    with loopback_enabled(tb):
        queues = set()

        for k, p in enumerate(pkts):
            await interface.start_xmit(p, k % len(interface.sched_blocks))

        for k in range(count):
            pkt = await interface.recv()

            if pkt is None:
                raise ValueError("Packet is None")

            tb.log.info("Packet: %s", pkt)
            # assert pkt.data == pkts[k]
            if interface.if_feature_rx_csum:
                assert pkt.rx_checksum == ~scapy.utils.checksum(bytes(pkt.data[14:])) & 0xffff

            queues.add(pkt.queue)

        assert len(queues) == len(interface.sched_blocks)

    for block in interface.sched_blocks[1:]:
        await block.schedulers[0].rb.write_dword(mqnic.MQNIC_RB_SCHED_RR_REG_CTRL, 0x00000000)
        await interface.set_rx_queue_map_indir_table(block.index, 0, 0)


async def lfc_pause_frame_receiver_test(tb: TB, interface: mqnic.Interface):
    await interface.ports[0].set_lfc_ctrl(
        mqnic.MQNIC_PORT_LFC_CTRL_TX_LFC_EN
        | mqnic.MQNIC_PORT_LFC_CTRL_RX_LFC_EN
    )

    await tb.driver.hw_regs.read_dword(0)

    lfc_xoff = Ether(
        src='DA:D1:D2:D3:D4:D5', dst='01:80:C2:00:00:01', type=0x8808
    ) / struct.pack('!HH', 0x0001, 2000)

    # send signal to pause LFC
    await tb.port_mac[0].rx.send(bytes(lfc_xoff))

    await simple_packet_firehose(tb, interface, 16, 1514)


@cocotb.test
async def full_nic_test(dut):
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
        await interface.sched_blocks[0].schedulers[0].rb.write_dword(mqnic.MQNIC_RB_SCHED_RR_REG_CTRL, 0x00000001)
        for k in range(len(interface.txq)):
            await interface.sched_blocks[0].schedulers[0].hw_regs.write_dword(4*k, 0x00000003)

    # wait for all writes to complete
    await tb.driver.hw_regs.read_dword(0)
    tb.log.info("Init complete")

    # -------------------- All iface, single packet test --------------------

    tb.log.info("Send and receive single packet")

    for interface in tb.driver.interfaces:
        await single_packet_test(tb, interface)

    # -------------------- Basic Rx/Tx Checksum Test --------------------

    tb.log.info("RX and TX checksum tests")

    await basic_checksum_test(tb)

    # -------------------- Queue Mapping Offset Test --------------------

    tb.log.info("Queue mapping offset test")

    await queue_map_offset_test(tb)

    # -------------------- Queue mapping RSS mask test --------------------

    if tb.driver.interfaces[0].if_feature_rss:
        tb.log.info("Queue mapping RSS mask test")

        await q_map_rss_mask_test(tb)

    # -------------------- Packet test: Many Small --------------------

    tb.log.info("Multiple small packets")

    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 60)

    # -------------------- Packet test: Many Large --------------------

    tb.log.info("Multiple large packets")

    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 1514)

    # -------------------- Packet test: Many Huge --------------------

    tb.log.info("Jumbo frames")

    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 9014)

    # ---------------- Packet test: To all interfaces ----------------

    if len(tb.driver.interfaces) > 1:
        tb.log.info("All interfaces")

        await all_interfaces_test(tb)

    # ------------ All Scheduler Blocks Test: Interface 0 ------------

    if len(tb.driver.interfaces[0].sched_blocks) > 1:
        tb.log.info("All interface 0 scheduler blocks")

        await all_scheduler_blocks_test(tb, tb.driver.interfaces[0])

    # ------------------- Rx under paused LFC Test -------------------

    if tb.driver.interfaces[0].if_feature_lfc:
        tb.log.info("Test LFC pause frame RX")

        await lfc_pause_frame_receiver_test(tb, tb.driver.interfaces[0])

    # -------------------- Another kind of test --------------------

    await dma_bench_test(tb)

    # ------------------------- Read Stats -------------------------

    tb.log.info("Read statistics counters")

    await Timer(Decimal(2000), 'ns')

    lst = []

    for k in range(64):
        lst.append(await tb.driver.hw_regs.read_dword(0x020000+k*8))

    print(lst)

    # ---------------- AXI Lite -> App interface Test ----------------

    tb.log.info("Test AXI lite interface to application")

    await tb.driver.app_hw_regs.write_dword(0, 0x11223344)

    print(await tb.driver.app_hw_regs.read_dword(0))

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# cocotb-test
