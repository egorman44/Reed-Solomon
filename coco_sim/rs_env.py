# ----------------------------------------------------------------------
#  Copyright (c) 2024 Egor Smirnov
#
#  Licensed under terms of the MIT license
#  See https://github.com/egorman44/Reed-Solomon/blob/main/LICENSE
#    for license terms
# ----------------------------------------------------------------------

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import Join
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import with_timeout

from tb_utils import reset_dut
from tb_utils import custom_clock
from tb_utils import watchdog_set
from tb_utils import assert_signal

from scoreboard import Comparator
from axis import AxisDriver, AxisResponder, AxisMonitor, FlowCtrl

from config import MSG_DURATION
from config import SINGLE_CLOCK
from config import AXIS_CLOCK
from config import CORE_CLOCK
import re

class RsEnv():
    
    def __init__(self, dut):        
        self.s_drivers = []
        self.m_monitors = []
        self.comparators = []
        self.dut = dut
    
    def build_env(self, s_if_containers, m_if_containers, flow_ctrl: FlowCtrl=FlowCtrl()):
        self.s_if_containers = s_if_containers
        self.m_if_containers = m_if_containers
        
        for i in range (len(self.s_if_containers)):
            self.s_drivers.append(AxisDriver(name=f's_drv{i}',
                                             axis_if=self.s_if_containers[i].if_ptr,
                                             flow_ctrl = flow_ctrl
                                             ))
        for i in range (len(self.m_if_containers)):
            self.comparators.append(Comparator(name=f'comp_{self.m_if_containers[i].if_name}'))
            
            self.m_monitors.append(AxisMonitor(name=f'm_mon_{self.m_if_containers[i].if_name}',
                                               axis_if=self.m_if_containers[i].if_ptr,
                                               aport=self.comparators[i].port_out
                                               ))
            
            self.comparators[i].port_prd = self.m_if_containers[i].if_packets.copy()
                    
    
    async def run(self):
        await cocotb.start(reset_dut(self.dut.reset,200,1))
        if not SINGLE_CLOCK:
            await cocotb.start(reset_dut(self.dut.io_coreRst,200,1))
            
        await Timer(50, units = "ns")        
        await cocotb.start(custom_clock(self.dut.clock, 1000/AXIS_CLOCK))
        if not SINGLE_CLOCK:
            await cocotb.start(custom_clock(self.dut.io_coreClock, 1000/CORE_CLOCK))

        # Start assertion for FIFO full
        await cocotb.start(assert_signal(self.dut.clock,self.dut.reset, self.dut.io_fifoFull))
        for m_mon in self.m_monitors:
            await cocotb.start(m_mon.mon_if())
        
        await FallingEdge(self.dut.reset)
        for i in range(10):
            await RisingEdge(self.dut.clock)
        
        # Send packets
        s_coroutings = []
        for pkt_num in range(len(self.s_if_containers[0].if_packets)):
            for i in range(len(self.s_drivers)):            
                s_coroutings.append(cocotb.start_soon(with_timeout(self.s_drivers[i].send_pkt(self.s_if_containers[i].if_packets[pkt_num]), 10_000, 'us')))
            for corouting in s_coroutings:
                await Join(corouting)
                
        # TODO: add delay based on latency
        for i in range(MSG_DURATION+400):
            await RisingEdge(self.dut.clock)
            
        #await watchdog_set(self.dut.clock, self.comparators)
        
    def post_run(self):
        print("post_run()")
        for comp in self.comparators:
            print(type(comp))
            comp.compare()
