# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 13:41:54 2021

@author: YH
"""
import time
import numpy as np
from udp_awg_driver_20220117 import fpgadev
#from udp_awg_ip_addr import devip
import matplotlib.pyplot as plt
import qulab_toolbox.wavedata as WD
import concurrent.futures

slot_id = []
slot_id.append(['192.168.4.10','da',12])
#slot_id.append(['192.168.4.18','da',12])
#slot_id.append(['192.168.4.26','da',12])
#slot_id.append(['192.168.4.34','ad',12])
#slot_id.append(['192.168.4.42','ad',4])
#slot_id.append(['192.168.4.18','ad',4])
dev = fpgadev(slot_id)


#dev.dev_id.da
#dev.dev_id.ad
#dev.dev_id.clock_board
#dev.dev_id.board
#%%
old_id = [['192.168.4.42','ad',4]]
new_id = [['192.168.4.42','ad',4]]

#dev.dev_id.ip_used(slot_id)
#
#dev.dev_id.ip_in_use(slot_id,new_id)
#
#dev.dev_id.set_dev_id(old_id,new_id)

#dev.dev_id.set_init_system_ip(old_id)

dev.dev_id.read_system_id(old_id)


#%%

adc_chennel_num = len(dev.dev_id.ad)
trigger_times = 10000
mul_data_delay = 1000
modle_en = 1
sampling = 1

test_times = 10

###############################system sampling confige#########################
time_start = time.time()


dev.dac_trigger_close()
dev.system_sampling(sampling)

for i in range(len(dev.dev_id.da)):
    dev.dac_Nyquist_cfg(i,Nyquist = 0)

#time.sleep(60*2)

#############################trigger ctrl######################################
trigger_us = 15
trigger_continue = 1


save_len = 16384
demo_ch_num = 1
##############################write dac########################################
#generate data
data_point = []
dac_data = []


if sampling == 0:
    sampleRate=5e9
    adc_trigger_delay = 460
    fout = 100e6
elif sampling == 1:
    sampleRate=4e9
    adc_trigger_delay = 470
    fout = 100e6

#fout = sampleRate/16

sin1=WD.Sin(fout*2*np.pi,0,12e-6,sampleRate)*(2**13-1)


dac_data.append(np.int16(sin1.data))

#generate point
replay_num = 0
dac_trigger_delay = 0
replay_cnt = 1
replay_continue_flag = 0



data_point = []
data_point_i = [0,0,dac_trigger_delay,replay_cnt,replay_continue_flag]
data_point.append(data_point_i)



for i in range(len(dev.dev_id.da)):
    dev.dac_updata(i,dac_data)
    dev.dac_point_updata(i,data_point)


####################################write adc mul data#########################

sin1=WD.Sin(fout*2*np.pi,0,200e-6,sampleRate/2)*(2**13-1)
cos1=WD.Cos(fout*2*np.pi,0,200e-6,sampleRate/2)*(2**13-1)

sin_data = np.int16(sin1.data)[:16384]
cos_data = np.int16(cos1.data)[:16384]


data_bufe = []
data_bufe.append(cos_data)
data_bufe.append(sin_data)

for i in range(adc_chennel_num):
    dev.adc_modle_reset(i,1)
    dev.adc_modle_reset(i,0)
    for modle_num in range(demo_ch_num):
        dev.adc_mul_data_wr(i,modle_num,data_bufe)


fig = plt.figure()


for times in range(test_times):
    
    print('test :',times)
    ###############################system sampling confige#########################
    
    
    dev.dac_trigger_close()
    
    
    for i in range(adc_chennel_num):
        dev.adc_modle_reset(i,1)
    for i in range(adc_chennel_num):
        for modle_num in range(demo_ch_num):
            dev.rd_adc_mul_data_ctrl(i,modle_en,modle_num,adc_trigger_delay+mul_data_delay,trigger_times,save_len)
        dev.rd_adc_data_ctrl(i,modle_en,adc_trigger_delay,trigger_times,save_len+mul_data_delay)
        
    for i in range(adc_chennel_num):
        dev.adc_modle_reset(i,0)

    time.sleep(0.5)
    
    dev.dac_trigger_ctrl(0,trigger_us,trigger_times,trigger_continue)
    
    
    ####################################read adc mul data#########################
    adc_muldata = []
    adc_muldata_i = []
    
#    time.sleep(0.5)
    
    time.sleep(trigger_us/1000000*trigger_times)
    
    time0 = time.time()
#    
    for i in range(adc_chennel_num):
        for modle_num in range(demo_ch_num):
            while 1:
                adc_data_bufe,data_len = dev.rd_adc_mul_data(i,modle_num,trigger_times)
        
                if data_len != -1:
                    break
            adc_muldata_i.append(adc_data_bufe)
        adc_muldata.append(adc_muldata_i)
        adc_muldata_i = []
     
#    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#        futures_t = [executor.submit(dev.get_adc_mul_data,item[0],item[1],item[2]) for item in rd_adc_mul_c]
        
#    for futures_tt in concurrent.futures.as_completed(futures_t):
#        adc_muldata_i.append(futures_tt.result())
#    for i in range(adc_chennel_num):
#        for ii in adc_muldata_i:
#            if dev.adc_chennel[i] is ii[1]:
#                adc_muldata.append(ii[0])
#                break

    time1 = time.time()
    print(time1-time0)
    
#    time2 = time.time()
    
#    adc_data = []
#    adc_data_i = []
#    for i in range(adc_chennel_num):
#        while 1:
#            adc_data_bufe,data_len = dev.rd_adc_data(i,trigger_times,save_len+mul_data_delay)
#            if data_len != -1:
#                break
#        adc_data.append(adc_data_bufe)

    

#    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#        futures_adc_t = [executor.submit(dev.get_adc_data,item[0],item[1],item[2]) for item in rd_adc_c]
        
#    for futures_adc_tt in concurrent.futures.as_completed(futures_adc_t):
#        adc_data_i.append(futures_adc_tt.result())
#    for i in range(adc_chennel_num):
#        for ii in adc_data_i:
#            if dev.adc_chennel[i] is ii[1]:
#                adc_data.append(ii[0])
#                break
            

     
    
#    dac_data_process = []
#    dac_data_process_sub = []
#    mul_data = cos_data[:save_len] + sin_data[:save_len]*1j
#    
#    for i in range(adc_chennel_num):
#        for mul_cnt in range(trigger_times):
#            dac_data_process_sub.append(sum(mul_data*adc_data[i][mul_cnt][mul_data_delay:]))
#        dac_data_process_sub_i = np.array(dac_data_process_sub)
#        dac_data_process.append(dac_data_process_sub_i)
#        dac_data_process_sub = []
    
    for i in range(adc_chennel_num):
        fig.add_subplot(4,4,i+1)
        for ii in range(demo_ch_num):
            plt.plot(adc_muldata[i][ii].real/save_len/2**13,adc_muldata[i][ii].imag/save_len/2**13,'.')
#        plt.plot(dac_data_process[i].real/save_len/2**13,dac_data_process[i].imag/save_len/2**13,'.')
#        fig.add_subplot(4,4,i+4)
#        for ii in range(demo_ch_num):
#            plt.plot(adc_muldata[i+2][ii].real/save_len/2**13,adc_muldata[i+2][ii].imag/save_len/2**13,'.')
#        plt.plot(dac_data_process[i+2].real/save_len/2**13,dac_data_process[i+2].imag/save_len/2**13,'.')
#        
#        fig.add_subplot(4,4,i+7)
#        for ii in range(demo_ch_num):
#            plt.plot(adc_muldata[i+4][ii].real/save_len/2**13,adc_muldata[i+4][ii].imag/save_len/2**13,'.')
#        plt.plot(dac_data_process[i+4].real/save_len/2**13,dac_data_process[i+4].imag/save_len/2**13,'.')
#        fig.add_subplot(4,4,i+10)
#        for ii in range(demo_ch_num):
#            plt.plot(adc_muldata[i+6][ii].real/save_len/2**13,adc_muldata[i+6][ii].imag/save_len/2**13,'.')
#        plt.plot(dac_data_process[i+6].real/save_len/2**13,dac_data_process[i+6].imag/save_len/2**13,'.')

#    time.sleep(0.5)


