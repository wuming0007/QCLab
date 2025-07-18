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
import math
import numpy as np
from pathlib import Path
QA_DRIVER_VER = 'QA驱动版本 : V1.0-20250523'
#from fpgaaddr import addr
path_new =  str(Path(__file__).parent/'pcie_driver.dll')
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
        print(QA_DRIVER_VER)
        
        # self.dc1v = 5917

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
            self.adc_mul_times = []
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
            for ch_i in range(12):
                self.da_ch.append([])
            for ch_i in range(12):
                self.ad_ch.append([])
                self.adc_mul_times.append(np.zeros(16))
            for i in range(BoardNum):
                print(BoardSlot[i],BoardType[i])
                if BoardType[i]==0x11:#hex(11)
                    
                    if BoardSlot[i] == 0:
                        self.BoardInfo[str(i)]=['adda','slot'+str(BoardSlot[i])]
    
                        for ch_i in range(4):
                            self.da_ch[ch_i] = ['slot'+str(BoardSlot[i]),ch_i,'8ad8da']
                        for ch_i in range(4):
                            self.ad_ch[ch_i] = ['slot'+str(BoardSlot[i]),3-ch_i,'8ad8da']
                    elif BoardSlot[i] == 1:
                        self.BoardInfo[str(i)]=['adda','slot'+str(BoardSlot[i])]
    
                        for ch_i in range(4):
                            self.da_ch[ch_i+4] = ['slot'+str(BoardSlot[i]),ch_i,'8ad8da']
                        for ch_i in range(4):
                            self.ad_ch[ch_i+4] = ['slot'+str(BoardSlot[i]),3-ch_i,'8ad8da']
                    elif BoardSlot[i] == 2:
                        self.BoardInfo[str(i)]=['adda','slot'+str(BoardSlot[i])]
    
                        for ch_i in range(4):
                            self.da_ch[ch_i+8] = ['slot'+str(BoardSlot[i]),ch_i,'8ad8da']
                        for ch_i in range(4):
                            self.ad_ch[ch_i+8] = ['slot'+str(BoardSlot[i]),3-ch_i,'8ad8da']

                     
                self.fpga.dll.sys_open(i)

        if BoardNum>0:
            ver  = self.readReg(0x100,'slot'+str(BoardSlot[0]))
            ver_t= self.readReg(0x101,'slot'+str(BoardSlot[0]))
            ver_s="PL固件版本 : V{:.1f}-{}".format(ver / 10, ver_t)
            print(ver_s)
            ver  = self.readReg(0x102,'slot'+str(BoardSlot[0]))
            ver_t= self.readReg(0x103,'slot'+str(BoardSlot[0]))
            ver_s="PS固件版本 : V{:.1f}-{}".format(ver / 10, ver_t)	
            print(ver_s)
            
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
    
    def pcie_wr_fbdata(self,slot,chennel_num,data):
        
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

            self.fpga_dma_write_bysize(slot,0xa2000000+0x100000*chennel_num+0x10000*i,data_wr_bufe_i,pcie_dma_wr_len*2)

        pbuf = None
        return 'ok'


    def pcie_rd_data(self,slot,chennel_num,data_len):
        
        pcie_dma_rd_len = 512*1024
        
        baseaddr = 0xa0000000 + 0x100000*chennel_num
        
      
        data_buf_i = []
        
        data_test,state = self.return_data_by_size(baseaddr,pcie_dma_rd_len,pcie_dma_rd_len,slot)
        
        data_buf_i = ctypes.POINTER(ctypes.c_int)(data_test)
        
        
        return np.int32(data_buf_i[:data_len])
    
    def pcie_wr_data64bit(self,slot,chennel_num,addr,data):
        
        pcie_dma_wr_len = 2048*4
        
        data_len = np.ceil(len(data[0])*2/pcie_dma_wr_len).astype(int)*pcie_dma_wr_len

        data_wr_bufe = np.zeros(data_len)
        data_wr_bufe[:len(data[0])*2] = np.reshape(data, (1,-1),order='f')
        
        data_wr_bufe = np.reshape(data_wr_bufe,(data_len//pcie_dma_wr_len,pcie_dma_wr_len))
        

        
        pbuf = ctypes.create_string_buffer(pcie_dma_wr_len*8)
        for i in range(len(data_wr_bufe)):
#            data_wr_bufe_i = np.int16(data_wr_bufe[i])
#            data_wr_bufe_i = ctypes.cast(data_wr_bufe_i.ctypes.data, ctypes.POINTER(ctypes.c_short))

            pbuf.raw = np.int64(data_wr_bufe[i])

            data_wr_bufe_i = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_short))

            self.fpga_dma_write_bysize(slot,addr+pcie_dma_wr_len*4*i,data_wr_bufe_i,pcie_dma_wr_len*2)

        pbuf = None
        return 'ok'
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
    
    def pcie_rd_data8bit(self,slot,chennel_num,addr,data_len):
        
        pcie_dma_rd_len = 2048*4
        
        data_len_rd =  np.ceil(data_len/pcie_dma_rd_len).astype(int)*pcie_dma_rd_len
        
        data_buf_i = []
        
        data_test,state = self.return_data_by_size(addr,data_len_rd,pcie_dma_rd_len,slot)
        data_buf_i = ctypes.POINTER(ctypes.c_int8)(data_test)
        
        data_buf_o = np.int8(data_buf_i[:data_len])
        
        return data_buf_o


    def pcie_serial_write(self,data,slot):
        for send_cnt in range(len(data)):
            for i in range(10):
                if (self.readReg(0x400+2,slot) & 0x08) == 0:
                    break
                else:
                    time.sleep(0.01)
        
            self.writeReg(0x400+1,data[send_cnt],slot)
            
        return len(data)
    
    def pcie_serial_read(self,slot,time_out):
        recv_data = []
        recv_num = 0
        time0 = time.time()
        
        while 1:
            if (self.readReg(0x400+2,slot) & 0x01) == 1:
                recv_data.append(np.uint8(self.readReg(0x400,slot)))
                recv_num+=1
            if recv_num == 32:
                return recv_data
            time1 = time.time()
            if time1-time0>time_out:
                return 'time_out'
            
    def pcie_serial_reset_input_buffer(self,slot):
        while 1:
            if (self.readReg(0x400+2,slot) & 0x01) == 1:
                self.readReg(0x400,slot)
            else:
                break
        return
            
                
    def pcie_serial_send_cmd(self,send_data):
        slot = 'slot0'
        self.pcie_serial_reset_input_buffer(slot)
        
        while 1:
            self.pcie_serial_write(send_data,slot)
            recv_data = self.pcie_serial_read(slot,0.5)

            if recv_data[:-1] == send_data[2:33]:
#                        print('cmd send done!')
                break 
        
        return recv_data

    
    def trigger_ctrl(self,trigger_source,trigger_us,trigger_num,trigger_continue):
        #trigger_source 0 为内部触发，1为外部触发
        #trigger_us 触发周期单位us
        #trigger_num 触发次数，当trigger_continue为1时无效
        #trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
#        global sampling_g

            
        trigger_times = np.uint32(trigger_num)
        trigger_us_cnt = np.uint32(round(trigger_us/0.160)-1)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x55))
        
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x01))
        fband_data_buf.append(np.uint8(0x01))
        fband_data_buf.append(np.uint8(trigger_source))
        fband_data_buf.append(np.uint8(trigger_continue))
        fband_data_buf.append(np.uint8(trigger_times>>24 & 0xff))
        fband_data_buf.append(np.uint8(trigger_times>>16 & 0xff))
        fband_data_buf.append(np.uint8(trigger_times>>8 & 0xff))
        fband_data_buf.append(np.uint8(trigger_times & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt>>24 & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt>>16 & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt>>8 & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt & 0xff))
        for i in range(18):
            fband_data_buf.append(np.uint8(0x00))
        
        
        fband_data_buf.append(np.uint8(0x55))
        fband_data_buf.append(np.uint8(0xaa))
        
        self.pcie_serial_send_cmd(fband_data_buf)

        return 'ok'

    def trigger_close(self):
        #关闭触发
        fband_data_buf=[]
        
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x55))
        
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x01))
        for i in range(28):
            fband_data_buf.append(np.uint8(0x00))
        
        fband_data_buf.append(np.uint8(0x55))
        fband_data_buf.append(np.uint8(0xaa))
        
        self.pcie_serial_send_cmd(fband_data_buf)
        
        return 'ok'
    

    def write_dac_data(self,slot,chennel_num,dac_data):
        
            
        self.pcie_wr_data(slot,chennel_num,dac_data)
            
        return 
    
    
    def dac_replay_type(self,chennel_num,replay_type):
        
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return 'error'

        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        
        self.writeReg(0x8000 + 0x400*ch_num + 5,np.uint32(replay_type),slot)
        
        return 'ok'    
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
            return 'error'

        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]

        dac_data_i = np.int16(dac_data*(2**13-1))
        
        data_len = len(dac_data_i)
        
        if data_len > 16384*32:
            print('data too len!!!')
            return 'error，data too len!!!'
        
        self.dac_ch_ctrl(slot,ch_num,data_len-1,trigger_delay,replay_times,replay_continue,0)
        self.write_dac_data(slot,ch_num,dac_data_i)
        self.dac_ch_ctrl(slot,ch_num,data_len-1,trigger_delay,replay_times,replay_continue,1)

        return 'ok'

    def dac_close(self,chennel_num):
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return 'error'
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        # print(slot,ch_num)
        self.writeReg(0x8000 + 0x400*ch_num + 1,0,slot)
        
        return 'ok'
    
    def dac_open(self,chennel_num):
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return 'error'
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        
        self.writeReg(0x8000 + 0x400*ch_num + 1,1,slot)
        
        return 'ok'
    
    
    def rd_adc_data_ctrl(self,adc_chennel_num,trigger_delay,times,save_len):
        #ADC数据存储控制
        #adc_chennel_num 为ADC通道数,从0开始
        #modle_en 为模块使能，1为使能工作，0为不工作
        #trigger_delay 为解调通道对应数据延时精度为ADC的采样点
        #times 为存储次数，
        #save_len 为存储长度，最大存储深度为131072个样点，52.4288us
        
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return 'error'
        if save_len > 131072:
            print('读取数据超出最大长度，最大长度为52.4288us')
            return 'error'
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]

        self.writeReg(0x4000 + 0x400*ch_num+0,1,slot)
        self.writeReg(0x4000 + 0x400*ch_num+1,np.uint32(trigger_delay),slot)
        self.writeReg(0x4000 + 0x400*ch_num+2,np.uint32(save_len),slot)
        self.writeReg(0x4000 + 0x400*ch_num+3,np.uint32(times-1),slot)
        
        self.writeReg(0x4000 + 0x400*ch_num+0,0,slot)
        
        
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
            return 'error'
        if save_len > 131072:
            print('读取数据超出最大长度，最大长度为52.4288us')
            return 'error'
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        
        save_state_i = self.readReg(0x4000 + 0x400*ch_num+2,slot)
        
        # print(save_state_i)
        if (save_state_i&1) == 0:
            read_data_len = -1
            # print('adc data save ',self.readReg(0x4000 + 0x400*ch_num+3,slot),'times!')
            return [],read_data_len
        else:
            adc_data = self.pcie_rd_data(slot,ch_num,save_len)

            return adc_data,save_len
    
    
    def rd_adc_mul_data_ctrl(self,adc_chennel_num=0,trigger_delay=0,times=0,mul_f_len=0,mul_f=[]):
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
            return 'error'
        if len(mul_f) > 16:
            print('frequency too lang')
            return 'error'
        if mul_f_len > 2**32:
            print('读取数据超出最大长度，最大长度为1.71s')
            return 'error'
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        # print(slot,ch_num)
        
        dds_phase_amp = 2**25
        adc_fs = 2.5e9
        
        mul_start_phase = []
        mul_f_phase = []
        
        sampling_start_time = []
        sampling_end_time = []
        # print(mul_f)
        for i in range(len(mul_f)):
            start_t = []
            end_t = []
            mul_start_phase.append(np.uint32(mul_f[i][0]/2/np.pi*dds_phase_amp))
            mul_f_phase.append(np.uint32(mul_f[i][1]/adc_fs*dds_phase_amp))
            for j in range(len(mul_f[i][2])):
                start_t.append(mul_f[i][2][j][0])
                end_t.append(mul_f[i][2][j][1])
            sampling_start_time.append(start_t)
            sampling_end_time.append(end_t)
            self.adc_mul_times[adc_chennel_num][i] = len(sampling_start_time[i])

        # print('sampling_start_time',adc_chennel_num,sampling_start_time,self.adc_mul_times[adc_chennel_num])
        # print(sampling_end_time)
        self.writeReg(0x6000 + 0x400*ch_num+0,1,slot)

        self.writeReg(0x6000 + 0x400*ch_num+1,np.uint32(trigger_delay),slot)
        self.writeReg(0x6000 + 0x400*ch_num+2,np.uint32(times-1),slot)
        self.writeReg(0x6000 + 0x400*ch_num+3,np.uint32(mul_f_len),slot)

        # for i in range(16):
        #     self.writeReg(0x6000 + 0x400*ch_num+2*i+4,0,slot)
        for i in range(16):
            self.writeReg(0x6000 + 0x400*ch_num+4+i,0,slot)
        
        for i in range(len(mul_f)):
            
            self.writeReg(0x6000 + 0x400*ch_num+4+i,1,slot)
            self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+0x3fe,np.uint32(mul_start_phase[i]%2**18),slot)
            self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+0x3ff,np.uint32(mul_start_phase[i]/2**18),slot)
            self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+0x3fc,np.uint32(mul_f_phase[i]%2**18),slot)
            self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+0x3fd,np.uint32(mul_f_phase[i]/2**18),slot)
            self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+0x3fa,np.uint32((len(sampling_start_time[i]))%2**18),slot)
            self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+0x3fb,np.uint32((len(sampling_start_time[i]))/2**18),slot)

            
            for j in range(len(sampling_start_time[i])):
                self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+2*j,np.uint32(sampling_start_time[i][j]),slot)
                self.writeReg(0xc000 + 0x4000*ch_num+0x400*i+2*j+1,np.uint32(sampling_end_time[i][j]),slot)
        
            
        # self.writeReg(0x6000 + 0x400*ch_num+20,np.uint32(mul_f_len),slot)
        
        self.writeReg(0x6000 + 0x400*ch_num+0,0,slot)
        
        
        
        return 'ok'
    
    def adc_mul_restart(self,):
        #ADC解调模块控制
        
        for i in range(len(self.ad_ch)):
        # for i in range(6,12):
            slot = self.ad_ch[i][0]
            ch_num = self.ad_ch[i][1]
#            if self.readReg(0x6000 + 0x400*ch_num+0,slot) == 0:
#                print(slot,ch_num)
            self.writeReg(0x6000 + 0x400*ch_num+0,1,slot)
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
            return 'error'
        if modle_num >= 16:
            print('modle_num too lang!')
            return 'error'
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        
        # if ch_num == 0:
        #     baseaddr = 0x500000000 + 0x20000000*ch_num + 0x2000000*modle_num
        # else:
        #     baseaddr = 0x000000000 + 0x20000000*ch_num + 0x2000000*modle_num
        
        baseaddr = 0x500000000 + 0x20000000*ch_num + 0x2000000*modle_num

        save_state_i = self.readReg(0x6000 + 0x400*ch_num+2,slot)

#        print(save_state_i)
        if (save_state_i & 1) == 0:
            read_data_len = -1
            # print('adc mul ',self.readReg(0x6000 + 0x400*ch_num+1,slot),'times!')
            return [],read_data_len
        else:
            # print('adc_mul_times',modle_num,self.adc_mul_times[adc_chennel_num][modle_num])
            read_data_len = int(times * self.adc_mul_times[adc_chennel_num][modle_num])
            adc_data = self.pcie_rd_data64bit(slot,ch_num,baseaddr,read_data_len)
#            adc_data_o = np.reshape(adc_data,(2,-1),order='F')
            recv_data = adc_data[0] + adc_data[1]*1j
            return recv_data,read_data_len


    def adc_mul_decision_ctrl(self,adc_chennel_num=0,decision_in=[]):
        
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return 'error'
        if len(decision_in) > 16:
            print('frequency too lang')
            return 'error'
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        
        for i in range(len(decision_in)):
            revolve_vector_real = np.int32(decision_in[i][0].real*(2**17-1))
            revolve_vector_imag = np.int32(decision_in[i][0].imag*(2**17-1))
            decision_value = np.int64(decision_in[i][1].real*(2**43-1))
    #        print(revolve_vector_real,revolve_vector_imag,decision_value)
            
            self.writeReg(0x6000 + 0x400*ch_num+i*4+36,revolve_vector_real,slot)
            self.writeReg(0x6000 + 0x400*ch_num+i*4+37,revolve_vector_imag,slot)
            self.writeReg(0x6000 + 0x400*ch_num+i*4+38,decision_value&0xffffffff,slot)
            self.writeReg(0x6000 + 0x400*ch_num+i*4+39,int(decision_value>>32)&0xffffffff,slot)
        
        return 'ok'

    def rd_adc_mul_decision_cnt(self,adc_chennel_num,modle_num):
        if adc_chennel_num > (len(self.ad_ch)-1) or adc_chennel_num < 0:
            print('未找到adc通道：',adc_chennel_num)
            return 'error'
        if modle_num > 16:
            print('modle_num too lang!')
            return 'error'
        
        slot = self.ad_ch[adc_chennel_num][0]
        ch_num = self.ad_ch[adc_chennel_num][1]
        
        save_state_i = self.readReg(0x6000 + 0x400*ch_num+2,slot)
        
        if (save_state_i & 1) == 0:
            decision_cnt = -1
            return decision_cnt
        else:
            decision_cnt = self.readReg(0x6000 + 0x400*ch_num+modle_num*4+36,slot)
            return decision_cnt
    
    def dac_offset_flash(self,chennel_num,offset,password):
        if chennel_num > 15 or chennel_num < 8:
            print('非Z-PULSE通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        print(ch_num)
        self.writeReg(0x8000 + 0x400*ch_num + 5,np.int32(offset),slot)
        
        self.set_dc_offset_to_flash(ch_num,password,offset,slot)
        self.offset = self.read_dc_offset()
        return
    
    def dac_offset(self,chennel_num,offset):
        if chennel_num > 15 or chennel_num < 8:
            print('非Z-PULSE通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        
        self.writeReg(0x8000 + 0x400*ch_num + 5,np.int32(offset),slot)
        
        return
    
    def set_ch_offset(self,chennel_num,offset):
        if chennel_num > 15 or chennel_num < 8:
            print('非Z-PULSE通道：',chennel_num)
            return
        self.dac_offset(chennel_num,np.round(self.dc1v * offset + self.offset[chennel_num-8]))
        
        return
    
    def rfdac_SetNyquistZone(self,NyquistZone,board_num):
        
        slot = self.da_ch[board_num*4][0]
        print(slot)
        cmd_reg = 1
        
        self.writeReg(2+cmd_reg,np.uint32(NyquistZone),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        print('设置slot',board_num,'为Nyquist-',NyquistZone)
        return 'ok'
    
    def rfdac_sampling(self,sampling,board_num):
        
        slot = self.da_ch[board_num*4][0]
        cmd_reg = 8
        self.writeReg(2+cmd_reg,np.uint32(sampling),slot)
        self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
        sampling_set = self.readReg(11,slot)
        print(slot)
        if sampling_set % 200 ==0 and sampling == sampling_set:
            print('设置slot',board_num,'采样率',sampling,'成功.')
        else:
            print('设置slot',board_num,'采样率',sampling,'失败！实际采样率为 :',sampling_set,'采样率不支持！！！')
        
        
        # slot = self.da_ch[8][0]
        # cmd_reg = 8
        # self.writeReg(2+cmd_reg,np.uint32(sampling),slot)
        # self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        # while 1:
        #     if self.readReg(0x0,slot)==0:
        #         break
        #     else:
        #         time.sleep(0.01)
        # sampling_set = self.readReg(11,slot)
        # print(slot)
        # if sampling_set % 200 ==0 and sampling == sampling_set:
        #     print('设置采样率',sampling,'成功！！！')
        # else:
        #     print('设置采样率',sampling,'失败！实际采样率为 :',sampling_set,'采样率不支持！')
        
        
        # slot = self.da_ch[16][0]
        # cmd_reg = 8
        # self.writeReg(2+cmd_reg,np.uint32(sampling),slot)
        # self.writeReg(0,np.uint32(cmd_reg<<1)+1,slot)
        # while 1:
        #     if self.readReg(0x0,slot)==0:
        #         break
        #     else:
        #         time.sleep(0.01)
        # sampling_set = self.readReg(11,slot)
        # print(slot)
        # if sampling_set % 200 ==0 and sampling == sampling_set:
        #     print('设置采样率',sampling,'成功！！！')
        # else:
        #     print('设置采样率',sampling,'失败！实际采样率为 :',sampling_set,'采样率不支持！')
            
        
        return

    def set_fan_speed(self,fan_speed):

        
        fan_speed_lh = np.uint32(fan_speed * 2**24)

        fband_data_buf=[]
        
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x55))
        
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(fan_speed_lh>>24 & 0xff))
        fband_data_buf.append(np.uint8(fan_speed_lh>>16 & 0xff))
        fband_data_buf.append(np.uint8(fan_speed_lh>>8 & 0xff))
        fband_data_buf.append(np.uint8(fan_speed_lh & 0xff))
        for i in range(25):
            fband_data_buf.append(np.uint8(0x00))
        
        fband_data_buf.append(np.uint8(0x55))
        fband_data_buf.append(np.uint8(0xaa))
        
        self.pcie_serial_send_cmd(fband_data_buf)
        
        
        
        
        return 
    
    
    def adc_coef(self,adc_ch,password):
        if adc_ch > (len(self.ad_ch)-1) or adc_ch < 0:
            print('未找到adc通道：',adc_ch)
            return 'error'
        
        slot = self.ad_ch[adc_ch][0]
        cmd_reg_addr = 16
        
        self.writeReg(2+cmd_reg_addr,(np.uint32(password)<<3)+adc_ch,slot)
        self.writeReg(0,np.uint32(cmd_reg_addr<<1)+1,slot)
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)

    def read_dc_offset(self,):
        slot = 'slot1'
        cmd_reg_addr = 32
        dc_offset = np.int32(np.zeros(8))
        for i in range(8):
            dc_offset[7-i] = np.int32(self.readReg(cmd_reg_addr+i,slot))
        
        return dc_offset
    
    def set_dc_offset_to_flash(self,dc_ch_num,password,offset,slot):
        
        cmd_reg_addr = 17
        
        self.writeReg(2+cmd_reg_addr,(np.uint32(password)<<3)+dc_ch_num,slot)
        self.writeReg(32+dc_ch_num,np.int32(offset),slot)
        self.writeReg(0,np.uint32(cmd_reg_addr<<1)+1,slot)
        
        while 1:
            if self.readReg(0x0,slot)==0:
                break
            else:
                time.sleep(0.01)
                
        return
        

#%%:
if __name__=='__main__':
    dev=fpgadev()  
    
