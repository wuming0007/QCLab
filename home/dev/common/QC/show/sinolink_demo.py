# -- coding: utf-8 --
import sys
from os.path import dirname, abspath

project_path = dirname(dirname(abspath(__file__)))
sys.path.append(project_path+r'/lib')

from device_interface import DeviceInterface

dev = DeviceInterface()
'''微波源ID、微波源ip、微波源端口'''
mws_id = "MWS_Sinolink_005"
mws_ip = "10.0.1.244"
mws_port = 2000
'''微波源连接、设置、查询、断开连接'''
ret = 0
ret = dev.mws_connect(mws_id, mws_ip, mws_port)
ret = dev.mws_set(mws_id, (('FREQ', 5e9), ('POWER', 20), ('OUTPUT', 1)))
res = dev.mws_query(mws_id, (('FREQ', 'POWER', 'OUTPUT')))
print(res)
ret = dev.mws_disconnect(mws_id)

