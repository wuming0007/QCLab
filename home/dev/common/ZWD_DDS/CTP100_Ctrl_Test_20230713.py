# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 17:26:14 2022

@author: YH
"""
from clk_fout_dev import clk_fout_dev

dev = clk_fout_dev('192.168.4.200')

#%%
#dev.system_sampling_cmd_send(dev.dev_id[0],0x04,1)
dev.system_sampling(0)
#%%

trigger_time = 0.8

trigger_ch = 1


#trigger_ref 001 参考上升沿，101参考下降沿，011捕获上升沿，111捕获下降沿，000正常内部输出或外部bypass输出
trigger_parameter = []
for i in range(20):
    # trigger_parameter.append({'trigger_source':0,'trigger_continue':1,'trigger_block_en':1,'trigger_ref':0,
    #                           'trigger_times':1000,'trigger_us':200,'trigger_delay':0})
    trigger_parameter.append({'trigger_source':0,'trigger_continue':1,'trigger_block_en':1,'trigger_ref':0,'trigger_times':1000,'trigger_us':200,'trigger_delay':i*trigger_time})

#trigger_parameter_t = []
#trigger_parameter_t.append({'trigger_source':1,'trigger_continue':1,'trigger_block_en':1,'trigger_ref':1,'trigger_times':1000,'trigger_us':200,'trigger_delay':i*trigger_time})

dev.trigger_close()
for trigger_ch in range(10):
    dev.trigger_ctrl(trigger_ch+1,trigger_parameter[trigger_ch])
#dev.trigger_ctrl(2,trigger_parameter_t[0])
#dev.trigger_ctrl(6,trigger_parameter[0])
#dev.trigger_ctrl(14,trigger_parameter_t[0])

dev.trigger_open()

#%%

trigger_time = 0.8

#trigger_ref 001(1) 参考上升沿，101(5)参考下降沿，011(3)捕获上升沿，111(7)捕获下降沿，000(0)正常内部输出或外部bypass输出
trigger_parameter = []

trigger_parameter.append({'trigger_source':0,'trigger_continue':1,'trigger_block_en':1,'trigger_ref':1,
                          'trigger_times':5000,'trigger_us':200,'trigger_delay':0})
trigger_parameter.append({'trigger_source':0,'trigger_continue':1,'trigger_block_en':1,'trigger_ref':0,
                          'trigger_times':1000,'trigger_us':200,'trigger_delay':0})
trigger_parameter.append({'trigger_source':0,'trigger_continue':1,'trigger_block_en':1,'trigger_ref':0,
                          'trigger_times':1000,'trigger_us':200,'trigger_delay':0})
dev.trigger_close()
for trigger_ch in range(3):
    dev.trigger_ctrl(trigger_ch+1,trigger_parameter[trigger_ch])
#dev.trigger_ctrl(1,trigger_parameter[0])
#dev.trigger_ctrl(6,trigger_parameter[0])
#dev.trigger_ctrl(14,trigger_parameter_t[0])

dev.trigger_open()


#%%
trigger_ch = 1
dev.trigger_ch_close(trigger_ch)
dev.trigger_ch_open(trigger_ch)
trigger_ch = 2
dev.trigger_ch_close(trigger_ch)
dev.trigger_ch_open(trigger_ch)

#%%
old_ip = '192.168.1.200'
new_ip = '192.168.1.200'

new_mac = '0.10.53.1.254.200'


#
# dev.set_dev_ip(old_ip,new_ip)
###
# dev.set_dev_mac(old_ip,new_mac)

# dev.set_init_ip(old_ip)

dev.read_system_ip(old_ip)

