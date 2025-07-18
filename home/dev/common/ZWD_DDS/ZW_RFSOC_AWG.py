# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 13:59:51 2022

@author: NUC1165G7
"""


import ctypes
import struct
import time
import pickle
import copy
from ctypes import string_at
from binascii import hexlify
import sys
from pathlib import Path
import math
import numpy as np
#import matplotlib.pyplot as plt

#from fpgaaddr import addr
path_new =  str(Path(__file__).parent/'ZW_XDMA_PLL_20221230.dll')

#%  为了读取板卡信息所做的类
class StructPointer(ctypes.Structure):
	        _fields_ = [("BoardNum", ctypes.c_int),("BoardSlot", ctypes.c_int*10),("BoardType", ctypes.c_int*10) ]
class dma_data(ctypes.Structure):
            _fields_ = [("Data_Test",ctypes.c_short *4096)]
class dma_data_sum(ctypes.Structure):
            _fields_ = [("Data_Test",ctypes.c_int *2048)]
class fpgadevdll(object):
    def __init__(self):
        self.dll = ctypes.WinDLL(path_new)
#        self.dll_i = ctypes.WinDLL(path)

#global sampling_g
#sampling_g = 0

#%主类 实现各种功能      
class fpgadev(object):
    _instance = None
    _initflag=False
    def __new__(cls,):
        if cls._instance==None:
            cls._instance = super(fpgadev, cls).__new__(cls)  
        else:
           print('已经实例化了对象')
        return cls._instance 
    def __init__(self):
        self.board_number=0
        self.BoardNumID=0
        if fpgadev._initflag==False:
            
            self.closefalg=True
            self.boardtypeflag='0'
            self.temp=ctypes.c_int32(0)
            self.StructInfo = StructPointer()
            self.fpga=fpgadevdll()
            self.fpga.dll.ALL_Sys_Init.rgtypes = [StructPointer] #ctypes.POINTER(StructPointer)
            aa=self.fpga.dll.ALL_Sys_Init(ctypes.byref(self.StructInfo))
            self.BoardInfo={}
            self.da_ch = []
            self.ad_ch = []
            if aa==-1:
                print('出错，已经初始化？？')
                self.boardinfo()
                sys.exit()
            else:
                self.boardinfo()
                fpgadev._initflag=True
        else:
            self.boardinfo()

        
        
    def return_data(self,addr,slot):
       for borad_id in range(self.board_number):
         if slot == self.BoardInfo[str(borad_id)][1]:
            self.data_test = dma_data()
            self.fpga.dll.dma_return_data.rgtypes = [dma_data,ctypes.c_int , ctypes.c_longlong , ctypes.c_int] #ctypes.POINTER(StructPointer)
            self.fpga.dll.dma_return_data(ctypes.byref(self.data_test),borad_id,ctypes.c_longlong(addr),8192)
            Data_Test = self.data_test.Data_Test   
            return Data_Test
    def return_data_by_size(self,dma_addr,size,pcie_dma_rd_len,slot):
        for borad_id in range(self.board_number):
            if slot == self.BoardInfo[str(borad_id)][1]:
                borad_id_i = borad_id
        data_test = (ctypes.c_ubyte *(size))()
        self.fpga.dll.dma_return_data_by_size.rgtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int , ctypes.c_longlong , ctypes.c_int, ctypes.c_int] #ctypes.POINTER(StructPointer)
        state = self.fpga.dll.dma_return_data_by_size(data_test,borad_id_i,ctypes.c_longlong(dma_addr),ctypes.c_int(size),ctypes.c_int(pcie_dma_rd_len))
        
        return data_test,state
    
    
        
    def boardinfo(self):
        BoardNum=self.StructInfo.BoardNum
        self.board_number = BoardNum
        BoardSlot=self.StructInfo.BoardSlot
        BoardType=self.StructInfo.BoardType
        print('现在一共有'+str(BoardNum)+'个板卡')
        
        if fpgadev._initflag==False:
            for ch_i in range(24):
                self.da_ch.append([])
            #     self.ad_ch.append([])
            for i in range(BoardNum):
                print(BoardSlot[i],BoardType[i])

                if BoardType[i]==0x22:
#                    print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':4da')
                    self.BoardInfo[str(i)]=['8da','slot'+str(BoardSlot[i])]
                    if BoardSlot[i] == 2:
                        for ch_i in range(8):
                            self.da_ch[ch_i+16] = ['slot'+str(BoardSlot[i]),ch_i,'8da']
                    elif BoardSlot[i] == 1:
                        for ch_i in range(8):
                            self.da_ch[ch_i+8] = ['slot'+str(BoardSlot[i]),ch_i,'8da']
                    else:
                        for ch_i in range(8):
                            self.da_ch[ch_i] = ['slot'+str(BoardSlot[i]),ch_i,'8da']


                     
                self.fpga.dll.sys_open(i)
#                    self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
     
#                    zz = self.fpga.dll.sys_open_ecc(i)
#                    self.Board_marknum['DC_BoardNumID']=zz

            
        print(self.BoardInfo)
        if len(self.ad_ch)!=0:
            print('ad：',len(self.ad_ch))
        if len(self.da_ch)!=0:
            print('da：',len(self.da_ch))
    
    def opencard(self,slot):
        for i in range(self.board_number):
            if slot == self.BoardInfo[str(i)][1]:
                return self.fpga.dll.sys_open(i)
            else:
                pass
           
        print('错误，没有此板卡')
    def closecard(self,slot):
        for i in range(self.board_number):
             if slot == self.BoardInfo[str(i)][1]:
                return self.fpga.dll.sys_close(i)
    def fpga_dma_write(self,bus_id,addr,data):
        size = 4096
#        print(size)
        pcie_fpga_dma_write = self.fpga.dll.sys_dma_write  # 取得函数
        pcie_fpga_dma_write.argtypes = [ctypes.c_int,ctypes.c_longlong,ctypes.POINTER(ctypes.c_short), ctypes.c_int]
        return pcie_fpga_dma_write(bus_id,addr,data,size)
    
    
    def fpga_dma_write_bysize(self,slot,addr,data,size):
        for borad_id in range(self.board_number):
            if slot == self.BoardInfo[str(borad_id)][1]:
                pcie_fpga_dma_write = self.fpga.dll.sys_dma_write  # 取得函数
                pcie_fpga_dma_write.argtypes = [ctypes.c_int,ctypes.c_longlong,ctypes.POINTER(ctypes.c_short), ctypes.c_int]
                return pcie_fpga_dma_write(borad_id,addr,data,size)
        
        
        
        
        
    def fpga_dma_read(self,bus_id,addr,size):
        pcie_fpga_dma_read = (self.fpga.dll.sys_dma_read)
        pcie_fpga_dma_read.argtypes = [ctypes.c_int,ctypes.c_longlong, ctypes.c_longlong]
        return ctypes.c_uint64(pcie_fpga_dma_read(bus_id,addr,size))
    def readReg(self,addr,slot):
        for i in range(self.board_number):
           if slot == self.BoardInfo[str(i)][1]:
               self.fpga.dll.sys_read32(0,addr*4,ctypes.byref(self.temp),i)
               return self.temp.value
#        if  self.closefalg:
#            print('错误,已经关闭板卡')
#        else:
            
    
    def writeReg(self,addr,data,slot=''):
        for i in range(self.board_number):
            if slot == self.BoardInfo[str(i)][1]:
                return self.fpga.dll.sys_write32(0,addr*4,int(data),i)
#        if  self.closefalg:
#            print('错误,已经关闭板卡')
#        else:

    def pcie_wr_data(self,slot,chennel_num,data):
        
        pcie_dma_wr_len = 2048*16
        
        data_len = np.ceil(len(data)/pcie_dma_wr_len).astype(int)*pcie_dma_wr_len
        
        data_wr_bufe = np.zeros(data_len)
        data_wr_bufe[:len(data)] = data
        
        data_wr_bufe = np.reshape(data_wr_bufe,(data_len//pcie_dma_wr_len,pcie_dma_wr_len))
        

        
        pbuf = ctypes.create_string_buffer(pcie_dma_wr_len*2)
        for i in range(len(data_wr_bufe)):
#            data_wr_bufe_i = np.int16(data_wr_bufe[i])
#            data_wr_bufe_i = ctypes.cast(data_wr_bufe_i.ctypes.data, ctypes.POINTER(ctypes.c_short))

            pbuf.raw = np.int16(data_wr_bufe[i])

            data_wr_bufe_i = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_short))

            self.fpga_dma_write_bysize(slot,0xa1000000+0x100000*chennel_num+0x10000*i,data_wr_bufe_i,pcie_dma_wr_len*2)

        pbuf = None
        return 'ok'


    def pcie_rd_data(self,slot,chennel_num,data_len):
        
        pcie_dma_rd_len = 128*1024
        
        baseaddr = 0xa0000000 + 0x100000*chennel_num
        
      
        data_buf_i = []
        
        data_test,state = self.return_data_by_size(baseaddr,pcie_dma_rd_len,pcie_dma_rd_len,slot)
        
        
        data_buf_i = ctypes.POINTER(ctypes.c_int)(data_test)
        
        
        return np.int32(data_buf_i[:data_len])

    def pcie_rd_data64bit(self,slot,chennel_num,addr,data_len):
        
        pcie_dma_rd_len = 2048*4
        
        data_len_rd =  np.ceil((data_len*8)/pcie_dma_rd_len).astype(int)*pcie_dma_rd_len
        
        data_buf_i = []
        
        data_test,state = self.return_data_by_size(addr,data_len_rd*2,pcie_dma_rd_len*2,slot)
        data_buf_i = ctypes.POINTER(ctypes.c_longlong)(data_test)
        
        data_buf_o = []
        data_buf_o.append(np.int64(data_buf_i[:data_len*2:2]))
        data_buf_o.append(np.int64(data_buf_i[1:data_len*2:2]))
        
        return data_buf_o


    def trigger_ctrl(self,trigger_source,trigger_us,trigger_num,trigger_continue):
        #trigger_source 0 为内部触发，1为外部触发
        #trigger_us 触发周期单位us
        #trigger_num 触发次数，当trigger_continue为1时无效
        #trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
#        global sampling_g
        
        for i in range(len(self.BoardInfo)):
            slot = self.BoardInfo[str(i)][1]

            trigger_times = np.uint32(trigger_num)
            
            trigger_us_cnt = np.uint32(round(trigger_us/0.160))
            
    #        if sampling_g == 0:
    #            trigger_us_cnt = np.uint32(round(trigger_us/0.0064))
    #        else:
    #            trigger_us_cnt = np.uint32(round(trigger_us/0.008))
    
            trigger_pm = ((trigger_source&0x1)<<1) + ((trigger_continue&0x1)<<2) + (trigger_times<<3)
    #        print(hex(trigger_pm))
            self.writeReg(0x400,trigger_pm,slot)
            self.writeReg(0x401,trigger_us_cnt,slot)
            trigger_pm = trigger_pm + 1
            self.writeReg(0x400,trigger_pm,slot)

        return 'ok'

    def trigger_close(self):
        #关闭触发
        for i in range(len(self.BoardInfo)):
            slot = self.BoardInfo[str(i)][1]

            trigger_pm = 0
            self.writeReg(0x400,trigger_pm,slot)
        
        return 'ok'
    
#    def system_sampling_cmd_send(self,board_id,cmd,sampling):
#        
#        fband_data_buf=[]
#        fband_data_buf.append(np.uint8(0xaa))
#        fband_data_buf.append(np.uint8(0x02))
#        fband_data_buf.append(np.uint8(cmd))
#        fband_data_buf.append(np.uint8(sampling))
#        for i in range(28):
#            fband_data_buf.append(np.uint8(0x00))
#        if board_id == 0:
#            self.serial_send_cmd(fband_data_buf)
#        else:
#            slot = self.BoardInfo[str(board_id-1)][1]
#            self.pcie_serial_send_cmd(slot,fband_data_buf)
#        
#        return 'ok'
#    
#    def system_sampling(self,sampling,step,self_set):
#        #切换采样率 0 为5Gsps；1 为4Gsps
#        global sampling_g
#        sampling_g = sampling
#        
#        self.trigger_close()
#        
#        for i in range(len(self.da_ch)):
#            slot = self.da_ch[i][0]
#            ch_num = self.da_ch[i][1]
#    
#            self.dac_ch_ctrl(slot,ch_num,1,0)
#            self.dac_ch_ctrl(slot,ch_num,0,0)
#        
#        if sampling == 0:
#            trigger_time = 6.4
#        else:
#            trigger_time = 8
#        
#        if self_set == 1:
#            
#            self.system_sampling_cmd_send(0,0x06,sampling)
#            time.sleep(2)
#            print('1/6...')
#            
#            self.trigger_ctrl(0,trigger_time,10,0)
#            
#            time.sleep(0.5)
#            
#            self.system_sampling_cmd_send(0,0x07,sampling)
#            time.sleep(0.5)
#            print('2/6...')
#            
#            self.trigger_ctrl(0,trigger_time,10,0)
#            
#            time.sleep(0.5)
#            
#            self.system_sampling_cmd_send(0,0x04,sampling)
#            
#            time.sleep(0.5)
#            print('3/6...')
#            
#            for i in range(self.board_number):
#                self.system_sampling_cmd_send(i+1,0x01,sampling)
#            
#            time.sleep(5)
#            print('4/6...')
#        
#            self.trigger_ctrl(0,trigger_time,10,0)
#            
#            time.sleep(0.5*self.board_number)
#            
#            for i in range(self.board_number):
#                self.system_sampling_cmd_send(i+1,0x02,sampling)
#                
#            time.sleep(0.5*self.board_number)
#            print('5/6...')
#            
#            self.trigger_ctrl(0,trigger_time,10,0)
#            
#            for i in range(self.board_number):
#                self.system_sampling_cmd_send(i+1,0x03,sampling)
#            
#            print('6/6...')
#            time.sleep(5)
#            print('done!')
#        else:
#            if step == 0:
#                self.system_sampling_cmd_send(0,0x03,sampling)
#            elif step == 1:
#                self.system_sampling_cmd_send(0,0x07,sampling)
#                self.trigger_ctrl(1,10,0,0)
#            elif step == 2:
#                self.system_sampling_cmd_send(0,0x04,sampling)
#            elif step == 3:
#                for i in range(self.board_number):
#                    self.system_sampling_cmd_send(i+1,0x01,sampling)
#            elif step == 4:
#                for i in range(self.board_number):
#                    self.system_sampling_cmd_send(i+1,0x02,sampling)
#            elif step == 5:
#                for i in range(self.board_number):
#                    self.system_sampling_cmd_send(i+1,0x03,sampling)
#
#        return
#
#    def dac_Nyquist_cfg(self,chennel_num,Nyquist):
#        #切换频域
#        #dac_chennel_in 为DAC通道数,从1开始
#        #Nyquist 为DAC工作模式，0 为正常模式；1 为mix模式，适合高频段
#        
#        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
#            print('未找到dac通道：',chennel_num)
#            return
#        
#        slot = self.da_ch[chennel_num][0]
#        ch_num = self.da_ch[chennel_num][1]
#        
#        fband_data_buf=[]
#        fband_data_buf.append(np.uint8(0xaa))
#        fband_data_buf.append(np.uint8(0x02))
#        fband_data_buf.append(np.uint8(0x04))
#        fband_data_buf.append(np.uint8(ch_num))
#        fband_data_buf.append(np.uint8(Nyquist))
#        for j in range(27):
#            fband_data_buf.append(np.uint8(0x00))
#        self.pcie_serial_send_cmd(slot,fband_data_buf)
#        return


    def write_dac_data(self,slot,chennel_num,dac_data):
        
            
        self.pcie_wr_data(slot,chennel_num,dac_data)
            
        return 
        
    def dac_ch_ctrl(self,slot,chennel_num,replay_len,trigger_delay,replay_times,replay_continue,dac_en):

        if dac_en == 0:
            self.writeReg(0x8000 + 0x400*chennel_num + 1,0,slot)
        else:
            self.writeReg(0x8000 + 0x400*chennel_num + 1,0,slot)
            self.writeReg(0x8000 + 0x400*chennel_num + 2,np.uint32(replay_len),slot)
            self.writeReg(0x8000 + 0x400*chennel_num + 3,np.uint32(trigger_delay),slot)
            self.writeReg(0x8000 + 0x400*chennel_num + 4,np.uint32(replay_times+(replay_continue<<31)),slot)
            self.writeReg(0x8000 + 0x400*chennel_num + 1,1,slot)
        
        return 'ok'
        

    def dac_updata(self,chennel_num,trigger_delay,replay_times,replay_continue,dac_data):
        #dac_chennel_num为dac通道号，从0开始
        
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        # print(slot,ch_num)
        data_len = len(dac_data)
        if data_len > 15360*32:
            print('data too len!!!')
            return
        
        self.dac_ch_ctrl(slot,ch_num,data_len,trigger_delay,replay_times,replay_continue,0)
        # print(slot,ch_num)
        self.write_dac_data(slot,ch_num,dac_data)
        # print(slot,ch_num)
        self.dac_ch_ctrl(slot,ch_num,data_len,trigger_delay,replay_times,replay_continue,1)

        return

    def dac_close(self,chennel_num):
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        print(slot,ch_num)
        self.writeReg(0x8000 + 0x400*chennel_num + 1,0,slot)
        
        return
    
    def dac_open(self,chennel_num):
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        
        self.writeReg(0x8000 + 0x400*chennel_num + 1,1,slot)
        
        return
    
    
    
#    def adc_modle_reset(self,adc_chennel_num,modle_reset):
#        #ADC模块总复位
#        #adc_chennel_num 为ADC通道数,从0开始
#        #modle_reset 为ADC模块总复位，0 为正常模式；1 为复位
#
#        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
#            print('未找到adc通道：',adc_chennel_num)
#            return
#        
#        adc_chennel_num = adc_chennel_num//2*2+(adc_chennel_num%2+1)%2
#        
#        slot = self.ad_ch[adc_chennel_num][0]
#        ch_num = self.ad_ch[adc_chennel_num][1]
#        
#        self.writeReg(0x400*(ch_num+1),np.uint32(modle_reset),slot)
#        return 'ok'
    
    def rd_adc_data_ctrl(self,adc_chennel_num,trigger_delay,times,save_len):
        #ADC数据存储控制
        #adc_chennel_num 为ADC通道数,从0开始
        #modle_en 为模块使能，1为使能工作，0为不工作
        #trigger_delay 为解调通道对应数据延时精度为ADC的采样点
        #times 为存储次数，
        #save_len 为存储长度，最大存储深度为5342494720个样点，2.13s
        
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        
        self.writeReg(0x6000 + 0x400*ch_num+0,1,slot)
        self.writeReg(0x6000 + 0x400*ch_num+5,np.uint32(trigger_delay),slot)
        self.writeReg(0x6000 + 0x400*ch_num+6,np.uint32(save_len),slot)
        self.writeReg(0x6000 + 0x400*ch_num+7,np.uint32(times),slot)
        
        self.writeReg(0x6000 + 0x400*ch_num+0,0,slot)
        
        
        return 'ok'
    
    def rd_adc_data(self,adc_chennel_num,times,save_len):
        #ADC存储数据读取
        #slot_dac 为ADC通道数
        #times 为读取的解调次数
        #save_len 为每次存储深度
        #返回值为存储数据和数据长度，其中存储未完成数据长度返回-1
        #存储数据格式为二维数据，其中第一维为times，第二维为save_len
        
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        
        save_state_i = self.readReg(0x6000 + 0x400*ch_num+5,slot)
        
#        print(save_state_i)
        if (save_state_i&1) == 0:
            read_data_len = -1
#            print('adc data save ',self.readReg(0x6000 + 0x400*ch_num+6,slot),'times!')
            return [],read_data_len
        else:
            adc_data = self.pcie_rd_data(slot,ch_num,save_len)

            return adc_data,save_len
    
    
    def rd_adc_mul_data_ctrl(self,adc_chennel_num=0,trigger_delay=0,times=0,mul_f=[]):
        #ADC解调模块控制
        #adc_chennel_num 为ADC通道数,从0开始
        #modle_en 为模块使能，1为使能工作，0为不工作
        #modle_num 为解调通道号 0~11总共12路
        #trigger_delay 为解调通道对应数据延时精度为ADC的采样点
        #times 为解调次数，最大为163840
        #save_len 为解调长度最大16384
#        self.adc_modle_reset(slot_dac,1)
        
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return
        if len(mul_f) > 32:
            print('frequency too lang')
            return
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]

        
        dds_phase_amp = 2**25
        adc_fs = 2.5e9
        
        mul_start_phase = []
        mul_f_phase = []
        mul_f_len = []
        
        for i in range(len(mul_f)):
            mul_start_phase.append(np.uint32(mul_f[i][0]/2/np.pi*dds_phase_amp))
            mul_f_phase.append(np.uint32(mul_f[i][1]/adc_fs*dds_phase_amp))
            mul_f_len.append(mul_f[i][2])
            
#        print(mul_start_phase,mul_f_phase,mul_f_len)
        adc_mul_data_len = max(mul_f_len)
        
        self.writeReg(0x6000 + 0x400*ch_num+0,1,slot)
        
        self.writeReg(0x6000 + 0x400*ch_num+1,np.uint32(trigger_delay),slot)
        self.writeReg(0x6000 + 0x400*ch_num+2,np.uint32(adc_mul_data_len),slot)
        self.writeReg(0x6000 + 0x400*ch_num+3,np.uint32(times),slot)
        self.writeReg(0x6000 + 0x400*ch_num+4,np.uint32(len(mul_f)),slot)
        
        for i in range(len(mul_f)):
            self.writeReg(0x4000 + 0x400*ch_num+4*i+0,mul_start_phase[i],slot)
            self.writeReg(0x4000 + 0x400*ch_num+4*i+1,mul_f_phase[i],slot)
            self.writeReg(0x4000 + 0x400*ch_num+4*i+2,mul_f_len[i],slot)
        
        
        
        
        self.writeReg(0x6000 + 0x400*ch_num+0,0,slot)
        
        
        
        return 'ok'
       
    def rd_adc_mul_data(self,adc_chennel_num,modle_num,times):
        #ADC解调结果读取
        #slot_dac 为ADC通道数
        #modle_num 为解调模块通道号，0~11
        #times 为读取的解调次数
        #返回值为解调结果数据和数据长度，其中解调未完成数据长度返回-1
        #解调结果数据格式为复数二维数据，其中第一维为times，第二维为复数结果
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return
        if modle_num > 32:
            print('modle_num too lang!')
            return
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]

        baseaddr = 0x500000000 + 0x20000000*ch_num + 0x1000000*modle_num
        
        save_state_i = self.readReg(0x6000 + 0x400*ch_num+1,slot)
        
#        print(save_state_i)
        if (save_state_i & 1) == 0:
            read_data_len = -1
#            print('adc mul ',self.readReg(0x6000 + 0x400*ch_num+3,slot),'times!')
            return [],read_data_len
        else:
            read_data_len = times
            adc_data = self.pcie_rd_data64bit(slot,ch_num,baseaddr,read_data_len)
#            adc_data_o = np.reshape(adc_data,(2,-1),order='F')
            recv_data = adc_data[0] + adc_data[1]*1j
            return recv_data,read_data_len

    
    def rfdac_SetNyquistZone(self,NyquistZone):
        
        slot = self.da_ch[18][0]
        
        cmd_reg = 1
        
        self.writeReg(2+cmd_reg,np.uint32(NyquistZone),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)

        slot = self.da_ch[9][0]
        
        cmd_reg = 1
        
        self.writeReg(2+cmd_reg,np.uint32(NyquistZone),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        
        slot = self.da_ch[0][0]
        
        cmd_reg = 1
        
        self.writeReg(2+cmd_reg,np.uint32(NyquistZone),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        
        return
    
    def rfadc_SetNyquistZone(self,NyquistZone):
        slot = self.ad_ch[0][0]
        
        cmd_reg = 2
        
        self.writeReg(2+cmd_reg,np.uint32(NyquistZone),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        return
    
    def rfdac_SetDecoderMode(self,DecoderMode):
        slot = self.ad_ch[0][0]
        
        cmd_reg = 3
        
        self.writeReg(2+cmd_reg,np.uint32(DecoderMode),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        return
    
    def rfadc_SetCalibrationMode(self,CalibrationMode):
        slot = self.ad_ch[0][0]
        
        cmd_reg = 4
        
        self.writeReg(2+cmd_reg,np.uint32(CalibrationMode),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        return
    
    def rfdac_SetDACVOP(self,DACVOP):
#        DACVOP : 100%->40500 uA 
#        Range 2250 - 40500 uA with 25 uA resolution
        slot = self.ad_ch[0][0]
        
        DACVOP_bufe = DACVOP*(40500-2250) + 2250
        
        cmd_reg = 5
        
        self.writeReg(2+cmd_reg,np.uint32(DACVOP_bufe),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        return
    
    def rfadc_SetDSA(self,Attenuation):
        
#        Range 0 - 27 dB with 1 dB resolution for Production Si
        
        slot = self.ad_ch[0][0]
        
        cmd_reg = 6
        
        self.writeReg(2+cmd_reg,np.float32(Attenuation),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        return
    
    def rfadc_SetDither(self,Dither):
        
        slot = self.ad_ch[0][0]
        
        cmd_reg = 7
        
        self.writeReg(2+cmd_reg,np.uint32(Dither),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        time.sleep(0.05)
        return
    
#    def adc_mul_data_wr(self,adc_chennel_num,modle_num,generate_data):
#        #ADC解调模块数据写入，数据为复数，generate_data【0】为实部，generate_data【1】为虚部
#        #adc_chennel_num 为ADC通道数,从0开始
#        #modle_num 为解调通道号 0~11总共12路
#        #generate_data 为解调通道对应数据
#        
#        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
#            print('未找到adc通道：',adc_chennel_num)
#            return
#            
#        adc_chennel_num = adc_chennel_num//2*2+(adc_chennel_num%2+1)%2
#            
#        slot = self.ad_ch[adc_chennel_num][0]
#        ch_num = self.ad_ch[adc_chennel_num][1]
#        
#        
#        start_addr = 0x11000000 + modle_num*2**16 + ch_num * 0x200000
#        
#        generate_data = np.reshape(generate_data,(1,-1),order='F')
#        
#        dma_wr_len = 2048*16
#        
#        data_wr_bufe = np.zeros(dma_wr_len)
#        
#        data_wr_bufe[:len(generate_data[0])] = generate_data[0]
#        
#        pbuf = ctypes.create_string_buffer(dma_wr_len*2)
#        pbuf.raw = np.int16(data_wr_bufe)
#        
#        data_wr_bufe_i = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_short))
#
#        self.fpga_dma_write_bysize(slot,start_addr,data_wr_bufe_i,dma_wr_len*2)
#        
#        
#        pbuf = None
#        return 'ok'

    def rfdac_sampling(self,sampling):
        
        for i in range(3):
            slot = self.da_ch[i*8][0]

            print(slot)
            cmd_reg = 8
            
            self.writeReg(2+cmd_reg,np.uint32(sampling),slot)
            self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
            
            while 1:
                if self.readReg(0x0,slot)==0:
                    break
                else:
                    time.sleep(0.01)
            sampling_set = self.readReg(11,slot)
            if sampling_set % 200 ==0 and sampling == sampling_set:
                print('设置采样率',sampling,'成功！！！')
            else:
                print('设置采样率',sampling,'失败！实际采样率为 :',sampling_set,'采样率不支持！')
        
        return

#%%:
if __name__=='__main__':
    dev=fpgadev()  
    
