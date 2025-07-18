# -- coding: utf-8 --
import sys
import time
from os.path import dirname, abspath

project_path = dirname(dirname(abspath(__file__)))
sys.path.append(project_path+r'/lib')
from device_interface import DeviceInterface

dev = DeviceInterface()
host_mac = "00-50-56-87-c8-9F"
ad_boards_list = [('QE10K4N0010', '00-00-00-00-00-5A')]  # 列出DAQ
n = 10
ret = 0


time.sleep(n*60)

for ad_id, ad_mac in ad_boards_list:
    '''连接DAQ'''
    ret |= dev.ad_connect_device(ad_id, host_mac, ad_mac)
    '''DAQ 复位操作， 复位之前需要等待10分钟'''
    ret |= dev.ad_reset_fpge(ad_id)
    if ret != 0:
        print(f'AD board {ad_id} connect/reset error!!!')

print(f'all ad board reset success .')

for ad_id, ad_mac in ad_boards_list:
    '''连接DAQ'''
    ret |= dev.ad_connect_device(ad_id, host_mac, ad_mac)
    ret |= dev.ad_init_device(ad_id)
    ret |= dev.ad_disconnect_device(ad_id)
    if ret != 0:
        print(f'AD board {ad_id} connect/init/disconnect error!!!')

print(f'all ad board connect init disconnect success!!!')
