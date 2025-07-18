# -- coding: utf-8 --
'''
    该程序主要展示如何通过调用驱动程序接口控制AWG以及对AWG进行输出。
'''
import sys
from os.path import dirname, abspath



import numpy as np
import matplotlib.pyplot as plt

sys.path.append(r'E:\PythonQOS\Repository\MeasModule\QOS\Driver\drivers\lib')

from device_interface import DeviceInterface 

dev = DeviceInterface()

'''输入参数：AWG ID、AWG IP、AWG 通道'''
da_id , ip , channel = ('QF10KBE0005', '10.0.200.3', 1)
master_id, master_ip = ('QF10KBE0003', '10.0.200.1')

'''生成正弦波'''
def waves_sine():
    cos_amplitude = 15000
    cos_n = 5000
    x = list(range(cos_n))
    y = 0.5 * cos_amplitude * (1 - np.cos(2 * np.pi * np.array(x) / cos_n))
    return y

ret = 0
trigger_count = 100
trigger_interval = 200e-6

'''连接AWG'''
ret |= dev.da_connect_device(da_id, ip)
'''初始化AWG'''
ret |= dev.da_init_device(da_id)
'''如果设置参数需要通过AWG主板,则需要连接主板并初始化'''
if master_id is not None:
    ret |= dev.da_connect_device(master_id, master_ip)
    ret |= dev.da_init_device(master_id)
if ret != 0:
    print(f'ERROR:da board:[{da_id}] or [{master_id}]connect or init failure ,ret:[{ret}]')
    sys.exit(0)
else:
    print(f'da board:[{da_id}] connect success .')
'''
    设置触发次数触发间隔:
        如果是通过AWG主板触发，则设置主板触发次数和间隔;
        如果是单板触发，则需要设置单板模式。
'''
if master_id is None:
    '''设置单板触发'''
    ret |= dev.set_multi_board(da_id,1)
    '''设置触发次数'''
    ret |= dev.da_set_trigger_count_l1(da_id, trigger_count)
else:
    ret |= dev.da_set_trigger_count_l1(master_id, trigger_count)
    ret |= dev.da_set_trigger_interval_l1(master_id, trigger_interval)

'''单板和多板模式都需要设置触发间隔'''
ret |= dev.da_set_trigger_interval_l1(da_id, trigger_interval)

if ret != 0:
    print(f'ERROR:da board:[{da_id}] set trig failure, ret:[{ret}].')
    sys.exit(0)
else:
    print(f'da board:[{da_id}] set trig success .')
'''生成波形数据'''
wave_data = waves_sine()
'''停止波形输出'''
ret |= dev.da_stop_output_wave(da_id, channel)
'''写波形到通道'''
ret |= dev.da_write_wave(wave_data, da_id, channel, 'i', 0, 0)
'''开始输出波形'''
ret |= dev.da_start_output_wave(da_id, channel)


if master_id is not None:
    '''AWG使能触发'''
    ret |= dev.da_trigger_enable(master_id)
else:
    ret |= dev.da_trigger_enable(da_id)
if ret != 0:
    print(f'ERROR:da board [{da_id}] wave output failure ,ret:[{ret}].')
    sys.exit(0)
else:
    print(f'da board:[{da_id}] wave output success .')

'''AWG断开连接'''
ret = dev.da_disconnect_device(da_id)
if master_id is not None and master_id != da_id:
    ret = dev.da_disconnect_device(master_id)


