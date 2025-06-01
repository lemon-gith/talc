# SPDX-License-Identifier: BSD-2-Clause-Views
# Copyright (c) 2021-2023 The Regents of the University of California

# typing imports
from decimal import Decimal
from cocotbext.axi import MemoryRegion
from scapy.packet import Packet

# utility imports
from contextlib import contextmanager

# module imports
import logging
import os
import struct
import sys

import scapy.utils
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

import cocotb_test.simulator
import pytest

import cocotb
from cocotb.log import SimLog
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from cocotbext.axi import AxiStreamBus
from cocotbext.axi import AxiSlave, AxiBus, SparseMemoryRegion
from cocotbext.eth import EthMac
from cocotbext.pcie.core import RootComplex
from cocotbext.pcie.xilinx.us import UltraScalePlusPcieDevice

# TODO: these are just a sanity check for now, remove this line later
# just importing the fn will allow cocotb to reach out and access the test fn
from tests.test import tell_me_the_truth, tell_me_lies  # noqa: F401


# import mqnic, if Python can't find it in repo, hijack system PATH
try:
    import mqnic
except ImportError:
    # attempt import from current directory
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    try:
        import mqnic
    finally:
        # clear this item from PATH once import is complete (polite)
        del sys.path[0]


# TODO: where should I put this class?
class TB(object):
    def __init__(self, dut, msix_count=32):
        self.dut = dut

        self.log = SimLog("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        # PCIe
        self.rc = RootComplex()

        self.rc.max_payload_size = 0x1  # 256 bytes
        self.rc.max_read_request_size = 0x2  # 512 bytes

        # TODO: it would probably be good to be able to be able to swap this out
        self.dev = UltraScalePlusPcieDevice(
            # configuration options
            pcie_generation=3,
            # pcie_link_width=16,
            user_clk_frequency=250e6,
            alignment="dword",
            cq_straddle=len(dut.pcie_if_inst.pcie_us_if_cq_inst.rx_req_tlp_valid_reg) > 1,
            cc_straddle=len(dut.pcie_if_inst.pcie_us_if_cc_inst.out_tlp_valid) > 1,
            rq_straddle=len(dut.pcie_if_inst.pcie_us_if_rq_inst.out_tlp_valid) > 1,
            rc_straddle=len(dut.pcie_if_inst.pcie_us_if_rc_inst.rx_cpl_tlp_valid_reg) > 1,
            rc_4tlp_straddle=len(dut.pcie_if_inst.pcie_us_if_rc_inst.rx_cpl_tlp_valid_reg) > 2,
            pf_count=1,
            max_payload_size=1024,
            enable_client_tag=True,
            enable_extended_tag=True,
            enable_parity=False,
            enable_rx_msg_interface=False,
            enable_sriov=False,
            enable_extended_configuration=False,

            pf0_msi_enable=False,
            pf0_msi_count=32,
            pf1_msi_enable=False,
            pf1_msi_count=1,
            pf2_msi_enable=False,
            pf2_msi_count=1,
            pf3_msi_enable=False,
            pf3_msi_count=1,
            pf0_msix_enable=True,
            pf0_msix_table_size=msix_count-1,
            pf0_msix_table_bir=0,
            pf0_msix_table_offset=0x00010000,
            pf0_msix_pba_bir=0,
            pf0_msix_pba_offset=0x00018000,
            pf1_msix_enable=False,
            pf1_msix_table_size=0,
            pf1_msix_table_bir=0,
            pf1_msix_table_offset=0x00000000,
            pf1_msix_pba_bir=0,
            pf1_msix_pba_offset=0x00000000,
            pf2_msix_enable=False,
            pf2_msix_table_size=0,
            pf2_msix_table_bir=0,
            pf2_msix_table_offset=0x00000000,
            pf2_msix_pba_bir=0,
            pf2_msix_pba_offset=0x00000000,
            pf3_msix_enable=False,
            pf3_msix_table_size=0,
            pf3_msix_table_bir=0,
            pf3_msix_table_offset=0x00000000,
            pf3_msix_pba_bir=0,
            pf3_msix_pba_offset=0x00000000,

            # signals
            # Clock and Reset Interface
            user_clk=dut.clk,
            user_reset=dut.rst,
            # user_lnk_up
            # sys_clk
            # sys_clk_gt
            # sys_reset
            # phy_rdy_out

            # Requester reQuest Interface
            rq_bus=AxiStreamBus.from_prefix(dut, "m_axis_rq"),
            pcie_rq_seq_num0=dut.s_axis_rq_seq_num_0,
            pcie_rq_seq_num_vld0=dut.s_axis_rq_seq_num_valid_0,
            pcie_rq_seq_num1=dut.s_axis_rq_seq_num_1,
            pcie_rq_seq_num_vld1=dut.s_axis_rq_seq_num_valid_1,
            # pcie_rq_tag0
            # pcie_rq_tag1
            # pcie_rq_tag_av
            # pcie_rq_tag_vld0
            # pcie_rq_tag_vld1

            # Requester Completion Interface
            rc_bus=AxiStreamBus.from_prefix(dut, "s_axis_rc"),

            # Completer reQuest Interface
            cq_bus=AxiStreamBus.from_prefix(dut, "s_axis_cq"),
            # pcie_cq_np_req
            # pcie_cq_np_req_count

            # Completer Completion Interface
            cc_bus=AxiStreamBus.from_prefix(dut, "m_axis_cc"),

            # Transmit Flow Control Interface
            # pcie_tfc_nph_av=dut.pcie_tfc_nph_av,
            # pcie_tfc_npd_av=dut.pcie_tfc_npd_av,

            # Configuration Management Interface
            cfg_mgmt_addr=dut.cfg_mgmt_addr,
            cfg_mgmt_function_number=dut.cfg_mgmt_function_number,
            cfg_mgmt_write=dut.cfg_mgmt_write,
            cfg_mgmt_write_data=dut.cfg_mgmt_write_data,
            cfg_mgmt_byte_enable=dut.cfg_mgmt_byte_enable,
            cfg_mgmt_read=dut.cfg_mgmt_read,
            cfg_mgmt_read_data=dut.cfg_mgmt_read_data,
            cfg_mgmt_read_write_done=dut.cfg_mgmt_read_write_done,
            # cfg_mgmt_debug_access

            # Configuration Status Interface
            # cfg_phy_link_down
            # cfg_phy_link_status
            # cfg_negotiated_width
            # cfg_current_speed
            cfg_max_payload=dut.cfg_max_payload,
            cfg_max_read_req=dut.cfg_max_read_req,
            # cfg_function_status
            # cfg_vf_status
            # cfg_function_power_state
            # cfg_vf_power_state
            # cfg_link_power_state
            # cfg_err_cor_out
            # cfg_err_nonfatal_out
            # cfg_err_fatal_out
            # cfg_local_error_out
            # cfg_local_error_valid
            # cfg_rx_pm_state
            # cfg_tx_pm_state
            # cfg_ltssm_state
            cfg_rcb_status=dut.cfg_rcb_status,
            # cfg_obff_enable
            # cfg_pl_status_change
            # cfg_tph_requester_enable
            # cfg_tph_st_mode
            # cfg_vf_tph_requester_enable
            # cfg_vf_tph_st_mode

            # Configuration Received Message Interface
            # cfg_msg_received
            # cfg_msg_received_data
            # cfg_msg_received_type

            # Configuration Transmit Message Interface
            # cfg_msg_transmit
            # cfg_msg_transmit_type
            # cfg_msg_transmit_data
            # cfg_msg_transmit_done

            # Configuration Flow Control Interface
            cfg_fc_ph=dut.cfg_fc_ph,
            cfg_fc_pd=dut.cfg_fc_pd,
            cfg_fc_nph=dut.cfg_fc_nph,
            cfg_fc_npd=dut.cfg_fc_npd,
            cfg_fc_cplh=dut.cfg_fc_cplh,
            cfg_fc_cpld=dut.cfg_fc_cpld,
            cfg_fc_sel=dut.cfg_fc_sel,

            # Configuration Control Interface
            # cfg_hot_reset_in
            # cfg_hot_reset_out
            # cfg_config_space_enable
            # cfg_dsn
            # cfg_bus_number
            # cfg_ds_port_number
            # cfg_ds_bus_number
            # cfg_ds_device_number
            # cfg_ds_function_number
            # cfg_power_state_change_ack
            # cfg_power_state_change_interrupt
            cfg_err_cor_in=dut.status_error_cor,
            cfg_err_uncor_in=dut.status_error_uncor,
            # cfg_flr_in_process
            # cfg_flr_done
            # cfg_vf_flr_in_process
            # cfg_vf_flr_func_num
            # cfg_vf_flr_done
            # cfg_pm_aspm_l1_entry_reject
            # cfg_pm_aspm_tx_l0s_entry_disable
            # cfg_req_pm_transition_l23_ready
            # cfg_link_training_enable

            # Configuration Interrupt Controller Interface
            # cfg_interrupt_int
            # cfg_interrupt_sent
            # cfg_interrupt_pending
            # cfg_interrupt_msi_enable
            # cfg_interrupt_msi_mmenable
            # cfg_interrupt_msi_mask_update
            # cfg_interrupt_msi_data
            # cfg_interrupt_msi_select
            # cfg_interrupt_msi_int
            # cfg_interrupt_msi_pending_status
            # cfg_interrupt_msi_pending_status_data_enable
            # cfg_interrupt_msi_pending_status_function_num
            # cfg_interrupt_msi_sent
            # cfg_interrupt_msi_fail
            cfg_interrupt_msix_enable=dut.cfg_interrupt_msix_enable,
            cfg_interrupt_msix_mask=dut.cfg_interrupt_msix_mask,
            cfg_interrupt_msix_vf_enable=dut.cfg_interrupt_msix_vf_enable,
            cfg_interrupt_msix_vf_mask=dut.cfg_interrupt_msix_vf_mask,
            cfg_interrupt_msix_address=dut.cfg_interrupt_msix_address,
            cfg_interrupt_msix_data=dut.cfg_interrupt_msix_data,
            cfg_interrupt_msix_int=dut.cfg_interrupt_msix_int,
            cfg_interrupt_msix_vec_pending=dut.cfg_interrupt_msix_vec_pending,
            cfg_interrupt_msix_vec_pending_status=dut.cfg_interrupt_msix_vec_pending_status,
            cfg_interrupt_msix_sent=dut.cfg_interrupt_msix_sent,
            cfg_interrupt_msix_fail=dut.cfg_interrupt_msix_fail,
            # cfg_interrupt_msi_attr
            # cfg_interrupt_msi_tph_present
            # cfg_interrupt_msi_tph_type
            # cfg_interrupt_msi_tph_st_tag
            cfg_interrupt_msi_function_number=dut.cfg_interrupt_msi_function_number,

            # Configuration Extend Interface
            # cfg_ext_read_received
            # cfg_ext_write_received
            # cfg_ext_register_number
            # cfg_ext_function_number
            # cfg_ext_write_data
            # cfg_ext_write_byte_enable
            # cfg_ext_read_data
            # cfg_ext_read_data_valid
        )

        # self.dev.log.setLevel(logging.DEBUG)

        self.rc.make_port().connect(self.dev)

        self.driver = mqnic.Driver()

        self.dev.functions[0].configure_bar(0, 2**len(dut.core_pcie_inst.axil_ctrl_araddr), ext=True, prefetch=True)
        if hasattr(dut.core_pcie_inst, 'pcie_app_ctrl'):
            self.dev.functions[0].configure_bar(2, 2**len(dut.core_pcie_inst.axil_app_ctrl_araddr), ext=True, prefetch=True)

        core_inst = dut.core_pcie_inst.core_inst

        # Ethernet
        self.port_mac: list[EthMac] = []

        eth_int_if_width = len(core_inst.m_axis_tx_tdata) / len(core_inst.m_axis_tx_tvalid)
        eth_clock_period = 6.4
        eth_speed = 10e9

        if eth_int_if_width == 64:
            # 10G
            eth_clock_period = 6.4
            eth_speed = 10e9
        elif eth_int_if_width == 128:
            # 25G
            eth_clock_period = 2.56
            eth_speed = 25e9
        elif eth_int_if_width == 512:
            # 100G
            eth_clock_period = 3.102
            eth_speed = 100e9

        for iface in core_inst.iface:
            for k in range(len(iface.port)):
                cocotb.start_soon(Clock(iface.port[k].port_rx_clk, eth_clock_period, units="ns").start())
                cocotb.start_soon(Clock(iface.port[k].port_tx_clk, eth_clock_period, units="ns").start())

                iface.port[k].port_rx_rst.setimmediatevalue(0)
                iface.port[k].port_tx_rst.setimmediatevalue(0)

                mac = EthMac(
                    tx_clk=iface.port[k].port_tx_clk,
                    tx_rst=iface.port[k].port_tx_rst,
                    tx_bus=AxiStreamBus.from_prefix(iface.interface_inst.port[k].port_inst.port_tx_inst, "m_axis_tx"),
                    tx_ptp_time=iface.port[k].port_tx_ptp_ts_tod,
                    tx_ptp_ts=iface.interface_inst.port[k].port_inst.port_tx_inst.s_axis_tx_cpl_ts,
                    tx_ptp_ts_tag=iface.interface_inst.port[k].port_inst.port_tx_inst.s_axis_tx_cpl_tag,
                    tx_ptp_ts_valid=iface.interface_inst.port[k].port_inst.port_tx_inst.s_axis_tx_cpl_valid,
                    rx_clk=iface.port[k].port_rx_clk,
                    rx_rst=iface.port[k].port_rx_rst,
                    rx_bus=AxiStreamBus.from_prefix(iface.interface_inst.port[k].port_inst.port_rx_inst, "s_axis_rx"),
                    rx_ptp_time=iface.port[k].port_rx_ptp_ts_tod,
                    ifg=12, speed=eth_speed
                )

                self.port_mac.append(mac)

        dut.eth_tx_status.setimmediatevalue(2**len(core_inst.m_axis_tx_tvalid)-1)
        dut.eth_tx_fc_quanta_clk_en.setimmediatevalue(2**len(core_inst.m_axis_tx_tvalid)-1)
        dut.eth_rx_status.setimmediatevalue(2**len(core_inst.m_axis_tx_tvalid)-1)
        dut.eth_rx_lfc_req.setimmediatevalue(0)
        dut.eth_rx_pfc_req.setimmediatevalue(0)
        dut.eth_rx_fc_quanta_clk_en.setimmediatevalue(2**len(core_inst.m_axis_tx_tvalid)-1)

        # DDR
        self.ddr_group_size = core_inst.DDR_GROUP_SIZE.value
        self.ddr_ram = []
        self.ddr_axi_if = []
        if hasattr(core_inst, 'ddr'):
            ram = None
            for i, ch in enumerate(core_inst.ddr.dram_if_inst.ch):
                cocotb.start_soon(Clock(ch.ch_clk, 3.332, units="ns").start())
                ch.ch_rst.setimmediatevalue(0)
                ch.ch_status.setimmediatevalue(1)

                if i % self.ddr_group_size == 0:
                    ram = SparseMemoryRegion()
                    self.ddr_ram.append(ram)
                self.ddr_axi_if.append(AxiSlave(AxiBus.from_prefix(ch, "axi_ch"), ch.ch_clk, ch.ch_rst, target=ram))

        # HBM
        self.hbm_group_size = core_inst.HBM_GROUP_SIZE.value
        self.hbm_ram = []
        self.hbm_axi_if = []
        if hasattr(core_inst, 'hbm'):
            ram = None
            for i, ch in enumerate(core_inst.hbm.dram_if_inst.ch):
                cocotb.start_soon(Clock(ch.ch_clk, 2.222, units="ns").start())
                ch.ch_rst.setimmediatevalue(0)
                ch.ch_status.setimmediatevalue(1)

                if i % self.hbm_group_size == 0:
                    ram = SparseMemoryRegion()
                    self.hbm_ram.append(ram)
                self.hbm_axi_if.append(AxiSlave(AxiBus.from_prefix(ch, "axi_ch"), ch.ch_clk, ch.ch_rst, target=ram))

        dut.ctrl_reg_wr_wait.setimmediatevalue(0)
        dut.ctrl_reg_wr_ack.setimmediatevalue(0)
        dut.ctrl_reg_rd_data.setimmediatevalue(0)
        dut.ctrl_reg_rd_wait.setimmediatevalue(0)
        dut.ctrl_reg_rd_ack.setimmediatevalue(0)

        cocotb.start_soon(Clock(dut.ptp_clk, 6.4, units="ns").start())
        dut.ptp_rst.setimmediatevalue(0)
        cocotb.start_soon(Clock(dut.ptp_sample_clk, 8, units="ns").start())

        dut.s_axis_stat_tdata.setimmediatevalue(0)
        dut.s_axis_stat_tid.setimmediatevalue(0)
        dut.s_axis_stat_tvalid.setimmediatevalue(0)

        self.loopback_enable = False
        cocotb.start_soon(self._run_loopback())

    async def init(self):

        for mac in self.port_mac:
            mac.rx.reset.setimmediatevalue(0)
            mac.tx.reset.setimmediatevalue(0)

        self.dut.ptp_rst.setimmediatevalue(0)

        for ram in self.ddr_axi_if + self.ddr_axi_if:
            ram.write_if.reset.setimmediatevalue(0)

        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)

        for mac in self.port_mac:
            mac.rx.reset.setimmediatevalue(1)
            mac.tx.reset.setimmediatevalue(1)

        self.dut.ptp_rst.setimmediatevalue(1)

        for ram in self.ddr_axi_if + self.ddr_axi_if:
            ram.write_if.reset.setimmediatevalue(1)

        await FallingEdge(self.dut.rst)
        await Timer(Decimal(100), 'ns')

        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)

        for mac in self.port_mac:
            mac.rx.reset.setimmediatevalue(0)
            mac.tx.reset.setimmediatevalue(0)

        self.dut.ptp_rst.setimmediatevalue(0)

        for ram in self.ddr_axi_if + self.ddr_axi_if:
            ram.write_if.reset.setimmediatevalue(0)

        await self.rc.enumerate()

    async def _run_loopback(self):
        while True:
            await RisingEdge(self.dut.clk)

            if self.loopback_enable:
                for mac in self.port_mac:
                    if not mac.tx.empty():
                        await mac.rx.send(await mac.tx.recv())


@contextmanager
def loopback_enabled(tb: TB, enabled: bool = True):
    """temporary loopback enabling utility

    Parameters
    ----------
    tb: TB
        the testbench instance for which you want loopback temporarily enabled
    enabled: bool
        should this be enabled? useful for parameterised testing

    Returns
    -------
    enabled: bool
        because I need to yield something, since this is technically a generator

    Usage
    -----
    with loopback_enabled(tb):
        ...
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
        nyom

    interface: mqnic.Interface
        nyom

    count: int
        how many packets should be sent?

    size: int
        and how large do you want those packets?

    enable_loopback: bool
        should automatic MAC loopback be enabled?\n
        // TODO: should we keep this? Add other parameters

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


async def single_packet_test(tb: TB):
    """
    TODO: write this up
    """
    tb.log.info("Send and receive single packet")

    for interface in tb.driver.interfaces:
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
    TODO: nyom
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
    await single_packet_test(tb)
    # ^this test actually also tests that every interface can do this
    # similarly to the All Interfaces test, a few tests down

    # -------------------- Another kind of test? --------------------

    tb.log.info("RX and TX checksum tests")

    await basic_checksum_test(tb)

    # -------------------- Another kind of test? --------------------

    tb.log.info("Queue mapping offset test")

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

    # -------------------- Another kind of test? --------------------
    # no, wait, this is a reconfiguration from ^2,

    # keep the config in here, since I don't think it'd be nice to add to the fn
    
    if tb.driver.interfaces[0].if_feature_rss:
        tb.log.info("Queue mapping RSS mask test")

        await tb.driver.interfaces[0].set_rx_queue_map_rss_mask(0, 0x00000003)

        for k in range(4):
            await tb.driver.interfaces[0].set_rx_queue_map_indir_table(0, k, k)

        tb.loopback_enable = True

        queues = set()

        for k in range(64):
            payload = bytes([x % 256 for x in range(256)])
            eth = Ether(src='5A:51:52:53:54:55', dst='DA:D1:D2:D3:D4:D5')
            ip = IP(src='192.168.1.100', dst='192.168.1.101')
            udp = UDP(sport=1, dport=k+0)
            test_pkt = eth / ip / udp / payload

            if tb.driver.interfaces[0].if_feature_tx_csum:
                test_pkt2 = test_pkt.copy()
                test_pkt2[UDP].chksum = scapy.utils.checksum(bytes(test_pkt2[UDP]))

                await tb.driver.interfaces[0].start_xmit(test_pkt2.build(), 0, 34, 6)
            else:
                await tb.driver.interfaces[0].start_xmit(test_pkt.build(), 0)

        for k in range(64):
            pkt = await tb.driver.interfaces[0].recv()

            if pkt is None:
                raise ValueError("Packet is None")

            tb.log.info("Packet: %s", pkt)
            if tb.driver.interfaces[0].if_feature_rx_csum:
                assert pkt.rx_checksum == ~scapy.utils.checksum(bytes(pkt.data[14:])) & 0xffff

            queues.add(pkt.queue)

        assert len(queues) == 4

        tb.loopback_enable = False

        # reset rss mask
        await tb.driver.interfaces[0].set_rx_queue_map_rss_mask(0, 0)

    # -------------------- Another kind of test? --------------------

    tb.log.info("Multiple small packets")

    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 60)

    # -------------------- Another kind of test? --------------------

    tb.log.info("Multiple large packets")

    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 1514)

    # -------------------- Similar test to above --------------------

    tb.log.info("Jumbo frames")

    await simple_packet_firehose(tb, tb.driver.interfaces[0], 64, 9014)

    # --------------- Same test as above^2, but on all ifs ---------------

    if len(tb.driver.interfaces) > 1:
        tb.log.info("All interfaces")

        count = 64

        pkts = [bytearray([(x+k) % 256 for x in range(1514)]) for k in range(count)]

        tb.loopback_enable = True

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

        tb.loopback_enable = False

    # -------------------- Another kind of test? --------------------

    if len(tb.driver.interfaces[0].sched_blocks) > 1:
        tb.log.info("All interface 0 scheduler blocks")

        for block in tb.driver.interfaces[0].sched_blocks:
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

        tb.loopback_enable = True

        queues = set()

        for k, p in enumerate(pkts):
            await tb.driver.interfaces[0].start_xmit(p, k % len(tb.driver.interfaces[0].sched_blocks))

        for k in range(count):
            pkt = await tb.driver.interfaces[0].recv()

            if pkt is None:
                raise ValueError("Packet is None")

            tb.log.info("Packet: %s", pkt)
            # assert pkt.data == pkts[k]
            if tb.driver.interfaces[0].if_feature_rx_csum:
                assert pkt.rx_checksum == ~scapy.utils.checksum(bytes(pkt.data[14:])) & 0xffff

            queues.add(pkt.queue)

        assert len(queues) == len(tb.driver.interfaces[0].sched_blocks)

        tb.loopback_enable = False

        for block in tb.driver.interfaces[0].sched_blocks[1:]:
            await block.schedulers[0].rb.write_dword(mqnic.MQNIC_RB_SCHED_RR_REG_CTRL, 0x00000000)
            await tb.driver.interfaces[0].set_rx_queue_map_indir_table(block.index, 0, 0)

    # -------------------- Another kind of test? --------------------

    if tb.driver.interfaces[0].if_feature_lfc:
        tb.log.info("Test LFC pause frame RX")

        await tb.driver.interfaces[0].ports[0].set_lfc_ctrl(mqnic.MQNIC_PORT_LFC_CTRL_TX_LFC_EN | mqnic.MQNIC_PORT_LFC_CTRL_RX_LFC_EN)
        await tb.driver.hw_regs.read_dword(0)

        lfc_xoff = Ether(src='DA:D1:D2:D3:D4:D5', dst='01:80:C2:00:00:01', type=0x8808) / struct.pack('!HH', 0x0001, 2000)

        await tb.port_mac[0].rx.send(bytes(lfc_xoff))

        await simple_packet_firehose(tb, tb.driver.interfaces[0], 16, 1514)

    # -------------------- Another kind of test --------------------
    # TODO: do I want this or not?
    # await dma_bench_test(tb)

    tb.log.info("Read statistics counters")

    await Timer(Decimal(2000), 'ns')

    lst = []

    for k in range(64):
        lst.append(await tb.driver.hw_regs.read_dword(0x020000+k*8))

    print(lst)

    # -------------------- Another kind of test? --------------------

    tb.log.info("Test AXI lite interface to application")

    await tb.driver.app_hw_regs.write_dword(0, 0x11223344)

    print(await tb.driver.app_hw_regs.read_dword(0))

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# cocotb-test
