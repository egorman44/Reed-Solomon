# ----------------------------------------------------------------------
#  Copyright (c) 2024 Egor Smirnov
#
#  Licensed under terms of the MIT license
#  See https://github.com/egorman44/Reed-Solomon/blob/main/LICENSE
#    for license terms
# ----------------------------------------------------------------------

# All tests are lacoted here:
import os
import argparse
from config import RsConfig
import cocotb
from cocotb.runner import get_runner
from config import PRJ_DIR, N_LEN, K_LEN, T_LEN, REDUNDANCY, FCR, MSG_DURATION, SYMB_WIDTH
import random
from rs_packets_builder import RsPacketsBuilder
from rs_interface_builder import RsIfBuilder
from rs_env import RsEnv
from errors_builder import ErrorsBuilder
from cocotb.regression import TestFactory
from axis import parse_flow_ctrl, FlowCtrl

class IfContainer():

    def __init__(self):
        self.if_name = ''
        self.if_ptr = None
        self.if_packets = []        

def parse_command_line():
    
    args = argparse.ArgumentParser(add_help=True)
    
    args.add_argument("-l", "--hdl_toplevel",
                      dest="hdl_toplevel",
                      required=True,
                      help='Set hdl top level. For Example RsSynd, RsBm, RsChien, RsForney, RsDecTop.'
                      )
    
    args.add_argument("-t", "--testcase",
                      dest="testcase",
                      required=False,
                      default=None,
                      help='Set testcases you want to run. Check available test in rs_testcases.py.'
                      )

    args.add_argument("-s", "--seed",
                      dest="seed",
                      required=False,
                      default=None,
                      help='Set run seed.'
                      )

    args.add_argument("-f" , '--flow_ctrl', 
                      required=False,
                      default='(1,0)',
                      help="Tuple: --flow_ctrl '(3, 1)' or Dict: --flow_ctrl \"{'tvalid_high_limit': 5, 'tvalid_low_limit': 2}\" , where the first digit represents the maximum number of cycles tvalid stays high, and the second digit represents the number of cycles tvalid stays low."
    )
    
    args.add_argument("-d", "--delay",
                      dest="delay",
                      required=False,
                      default=0,
                      help="Specify the packet delay. Must be an integer or one of the following types: 'random', 'no_delay', 'short', 'medium'."
                      )

    
    return args.parse_args()    

def build_and_run():
    sim = os.getenv("SIM", "verilator")
    runner = get_runner(sim)
    sv_top = args.hdl_toplevel+".sv"
    runner.build(
        defines={},
        parameters={},
        verilog_sources=[PRJ_DIR / sv_top],
        includes={},
        hdl_toplevel=args.hdl_toplevel,
        build_args=[ '--timing', '--assert' , '--trace' , '--trace-structs', '--trace-max-array', '512', '--trace-max-width', '512'],
        always=True,
    )
    
    runner.test(hdl_toplevel=args.hdl_toplevel,
                test_module='rs_decoder',
                testcase=args.testcase,
                )
            
    

'''
TESTS:

'''
def get_if(top_level):
    if top_level == 'RsSynd':
        s_if = ['sAxisIf']
        m_if = ['syndIf'] 
    elif top_level == 'RsBm':
        s_if = ['syndIf'] 
        m_if = ['errLocIf'] 
    elif top_level == 'RsChien':
        s_if = ['errLocIf'] 
        m_if = ['errPosIf'] 
    elif top_level == 'RsForney':
        s_if = ['errPosIf', 'syndIf'] 
        m_if = ['errValIf'] 
    elif top_level == 'RsDecoder':
        s_if = ['sAxisIf'] 
        m_if = ['errValIf', 'errPosOutIf']
    elif top_level == 'RsBlockRecovery':
        s_if = ['sAxisIf']
        m_if = ['mAxisIf']         
    else:
        raise ValueError(f"Not expected value for top_level = {top_level}")
    return s_if, m_if

async def decoder_test(dut, error_type, pkt_num = 1, msg_pattern='random'):
    
    print(f"delay = {os.environ['DELAY']}")
    print(f"flow_ctrl = {os.environ['FLOW_CTRL']}")
    flow_ctrl = parse_flow_ctrl(os.environ['FLOW_CTRL'])
    
    s_if_containers = []
    m_if_containers = []
    
    if_builder = RsIfBuilder(dut)

    err_builder = ErrorsBuilder(N_LEN, T_LEN, SYMB_WIDTH)
    
    # Get interfaces
    s_if_list, m_if_list = get_if(dut._name)
    for if_name in s_if_list:
        if_container = IfContainer()
        if_container.if_name = if_name
        if_container.if_ptr = if_builder.get_if(if_name)
        s_if_containers.append(if_container)
    for if_name in m_if_list:
        if_container = IfContainer()
        if_container.if_name = if_name
        if_container.if_ptr = if_builder.get_if(if_name)
        m_if_containers.append(if_container)        
    # Generate packets
    pkt_builder = RsPacketsBuilder(K_LEN, REDUNDANCY, FCR)
    for i in range(pkt_num):
        err_num = T_LEN
        err_pos, err_val = err_builder.generate_error(error_type)
        pkt_builder.generate_msg(msg_pattern, os.environ['DELAY'])
        pkt_builder.encode_msg()
        pkt_builder.corrupt_msg(err_pos, err_val)
        for i in range(len(s_if_containers)):
            s_pkt = pkt_builder.get_pkt(s_if_containers[i].if_name)
            s_pkt.print_pkt()
            s_if_containers[i].if_packets.append(s_pkt)
        for i in range (len(m_if_containers)):
            mon_pkt = pkt_builder.get_pkt(m_if_containers[i].if_name)
            if mon_pkt is not None:
                mon_pkt.print_pkt()
                m_if_containers[i].if_packets.append(mon_pkt)
        #pkt_builder.debug_msg()
        
    # Build environment
    env = RsEnv(dut)
    env.build_env(s_if_containers, m_if_containers, flow_ctrl)
    await env.run()
    env.post_run()
    
@cocotb.test()
async def random_error_test(dut):
    await decoder_test(dut, 'random_error', 100)
    
@cocotb.test()
async def cover_all_errors_test(dut):
    await decoder_test(dut, 'cover_all_errors', T_LEN)

@cocotb.test()
async def error_burst_test(dut):
    await decoder_test(dut, 'error_burst', 2*MSG_DURATION)

@cocotb.test()
async def min_max_test(dut):
    await decoder_test(dut, 'min_max', 100)
    
@cocotb.test()
async def uncorrupted_msg_test(dut):
    await decoder_test(dut, 'uncorrupted_msg', 2*MSG_DURATION)

@cocotb.test()
async def incr_ptrn_test(dut):
    await decoder_test(dut, 'random_error', 1,'increment')

# Register test dynamically

if __name__ == "__main__":    
    args = parse_command_line()
    if args.seed:
        os.environ["RANDOM_SEED"] = args.seed
    # Set argumets that are used in the test:
    os.environ["DELAY"] = str(args.delay)
    os.environ["FLOW_CTRL"] = str(args.flow_ctrl)
    build_and_run()
