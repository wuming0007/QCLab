# -- coding: utf-8 --
'''
    该程序主要展示如何控制ZDC。
'''

import sys
from os.path import dirname, abspath

project_path = dirname(dirname(abspath(__file__)))
sys.path.append(project_path+r'/lib')

from device_interface import DeviceInterface

dev = DeviceInterface()
'''
    输入参数：
        dc_id：ZDC ID
        dc_ip：ZDC IP地址
        dc_port：ZDC 端口，默认5000
'''
dc_id = "DC1"
dc_ip = "10.0.200.25"
dc_port = 5000

'''设置ZDC输出电压值为0'''
ret = dev.dc_set(dc_id,dc_ip ,dc_port,1, ('VOLT', 0))# 电压值(范围为-7到7)
'''查询ZDC输出电压值'''
ret,volt = dev.dc_query(dc_id,dc_ip,dc_port,1,'VOLT')
print (f'dc:[{dc_id}] query volt value:[{volt}].')
