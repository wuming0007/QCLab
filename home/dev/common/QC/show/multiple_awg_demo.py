# -- coding: utf-8 --
'''
    该程序主要展示如何通过调用驱动程序接口控制AWG以及对AWG进行输出。
'''
import sys
from os.path import dirname, abspath


import QOS.Gate.wavedata as WD
import numpy as np
from util import step_function

sys.path.append(r'E:\PythonQOS\Repository\MeasModule\QOS\Driver\drivers\lib')

from device_interface import DeviceInterface 

dev = DeviceInterface()

'''输入参数：AWG ID、AWG IP、AWG 通道'''
# da_list = [('QF10K4N0046', '10.0.200.73')]
# master_da_board = ('QF10K4N0046', '10.0.200.73')

da_list = [
    ('QF10KBE0003', '10.0.200.1'), ('QF10KBE0004', '10.0.200.2'),('QF10KBE0005', '10.0.200.3'),('QF10KBE0006', '10.0.200.4'),('QF10KBE0002', '10.0.200.5'),('QF10KBE0007', '10.0.200.6'),('QF10KBE0009', '10.0.200.7'),
    ('QF10KBE0008', '10.0.200.11'),('QF10KBE0010', '10.0.200.12'),('QF10L4S0004', '10.0.200.13'),('QF10L4S0007', '10.0.200.14'),('QF10L4S0006', '10.0.200.15'),('QF10L4S0003', '10.0.200.16')
]
master_da_board = ('QF10KBE0003', '10.0.200.1')


'''生成正弦波'''
def waves_cos():
    cos_amplitude = 15000
    cos_n = 5000
    x = list(range(cos_n))
    y = 0.5 * cos_amplitude * (np.cos(2 * np.pi * np.array(x) / cos_n))
    return y


def waves_sine():
    cos_amplitude = 15000
    cos_n = 5000
    x = list(range(cos_n))
    y = 0.5 * cos_amplitude * (np.sin(2 * np.pi * np.array(x) / cos_n))
    # y1 = WD.Cos(2*np.pi*50e6, phi=0, width=30e-6, sRate=2e9)*15000
    y1 = WD.DC(0.5e-6,2e9)*32000|(WD.Blank(38e-6,2e9))
    return y1.real


def wave_rectangle():
    amp_temp = 1500
    width = 3000
    n = 5000
    x = list(range(n))
    y = amp_temp * (step_function(np.arange(n)
                                  - step_function(np.arange(n) - width, n), (n-width)))
    wave_data = y * np.cos(2 * np.pi * 0 * np.array(x))
    return wave_data


def wave_gaussian():
    amplitude = 15000
    n = 500
    r_sigma = 1
    x = list(range(n))
    y = amplitude * np.exp(-0.5 * pow((np.array(x) - 0.5 * n) / n * r_sigma, 2))
    wave_data = y * np.cos(2 * np.pi * 0 * np.array(x))
    return wave_data

ret = 0
trigger_count = 100
trigger_interval = 200e-6

for da_id, ip in da_list:
    '''连接AWG'''
    ret |= dev.da_connect_device(da_id, ip)
    '''初始化AWG'''
    ret |= dev.da_init_device(da_id)
if ret != 0:
    print(f'ERROR:all da boards connect and init failure.')
    sys.exit(0)
else:
    print(f'all da boards connect and init success.')

'''如果主板在da_board_list中，则不需要重复连接'''
if master_da_board not in da_list:
    ret |= dev.da_connect_device(master_da_board[0], master_da_board[1])
    ret |= dev.da_init_device(master_da_board[0])
if ret != 0:
    print(f'ERROR:[{master_da_board[0]}] connect or init failure ,ret:[{ret}]')
    sys.exit(0)
else:
    print(f'[{master_da_board[0]}] connect and init success .')

'''
    设置触发次数触发间隔:
        如果是通过AWG主板触发，则设置主板触发次数和间隔;
        如果是单板触发，则需要设置单板模式。
'''
'''生成波形数据'''
wave_data = waves_sine()

ret = dev.da_set_trigger_count_l1(master_da_board[0], trigger_count)
ret |= dev.da_set_trigger_interval_l1(master_da_board[0], trigger_interval)
if ret != 0:
    print(f'ERROR:master da board [{master_da_board[0]}] set param failure ,ret:[{ret}].')
    sys.exit(0)
else:
    print(f'master da board [{master_da_board[0]}] set param success .')

for da_id, ip in da_list:
    '''设置触发次数'''
    ret = dev.da_set_trigger_count_l1(da_id, trigger_count)
    '''设置触发间隔'''
    ret |= dev.da_set_trigger_interval_l1(da_id, trigger_interval)
    if ret != 0:
        print(f'ERROR:da board:[{da_id}] set trig failure, ret:[{ret}].')
        sys.exit(0)
    else:
        print(f'da board:[{da_id}] set trig success .')

    '''停止波形输出'''
    ret = dev.da_stop_output_wave(da_id, 0)
    for channel in range(1, 5):
        
        '''写波形到通道'''
        ret = dev.da_write_wave(wave_data, da_id, channel, 'i', 1, 0)
        if ret != 0:
            print(f'ERROR:da board [{da_id}] wave output failure ,ret:[{ret}].')
            sys.exit(0)
        else:
            print(f'da board:[{da_id}] wave output success .')
    ret = dev.da_start_output_wave(da_id, 0)

    '''开始输出波形'''
    

'''AWG使能触发'''
ret = dev.da_trigger_enable(master_da_board[0])
if ret != 0:
    print(f'ERROR:master da board [{master_da_board[0]}] trigger enable failure ,ret:[{ret}].')
    sys.exit(0)
else:
    print(f'master da board [{master_da_board[0]}] trigger enable success .')

target_list = [da_id for da_id, ip in da_list]
target_list.append(master_da_board[0])
target_list = list(set(target_list))
for target in target_list:
    '''AWG断开连接'''
    ret = dev.da_disconnect_device(target)
    if ret != 0:
        print(f'ERROR:master da board [{target}] disconnect failure ,ret:[{ret}].')
    else:
        print(f'master da board [{target}] disconnect success .')


