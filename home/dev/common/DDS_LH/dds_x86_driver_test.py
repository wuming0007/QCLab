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
import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports
# from fpgaaddr import addr

from pathlib import Path
#userDLL_path=os.getcwd()+'\\'+"UdpDLL0125.dll"
path_new = str(Path(__file__).parent/'QUbit_XDMA_DLL_3UAWG_test.dll')
# path_new =  '.\\QUbit_XDMA_DLL_3UAWG_test.dll'

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

global sampling_g
sampling_g = 0

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
#        for borad_id in range(self.board_number):
#            self.fpga.dll.sys_write32(0,0x1000,1,borad_id)
        
        self.find_serial_port()
#        print(self.find_serial_port())
#        self.serialport = serial.Serial()  #/dev/ttyUSB0
#        self.serialport.port = 'COM5'
#        self.serialport.baudrate = 115200
#        self.serialport.bytesize = 8
#        self.serialport.parity = serial.PARITY_NONE
#        self.serialport.stopbits = 1
#        self.serialport.timeout = 0.5
#        self.serialport.open()
#        
#        if self.serialport.isOpen() == 0:
#            print("open serial failed")
        
        
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
                data_test = (ctypes.c_ubyte *(size))()
                self.fpga.dll.dma_return_data_by_size.rgtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int , ctypes.c_longlong , ctypes.c_int, ctypes.c_int] #ctypes.POINTER(StructPointer)
                state = self.fpga.dll.dma_return_data_by_size(data_test,borad_id,ctypes.c_longlong(dma_addr),ctypes.c_int(size),ctypes.c_int(pcie_dma_rd_len))
                
                return data_test,state
        
    def boardinfo(self):
        BoardNum=self.StructInfo.BoardNum
        self.board_number = BoardNum
        BoardSlot=self.StructInfo.BoardSlot
        BoardType=self.StructInfo.BoardType
        print('现在一共有'+str(BoardNum)+'个板卡')
#         print(BoardSlot[0],BoardType[0])
        if fpgadev._initflag==False:
            for i in range(BoardNum):
                if BoardType[i]==17:#hex(11)
#                    print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':2ad2da')
                    self.BoardInfo[str(i)]=['2ad2da','slot'+str(BoardSlot[i])]
                    self.da_ch.append(['slot'+str(BoardSlot[i]),0,'2ad2da'])
                    self.da_ch.append(['slot'+str(BoardSlot[i]),1,'2ad2da'])
                    self.ad_ch.append(['slot'+str(BoardSlot[i]),0,'2ad2da'])
                    self.ad_ch.append(['slot'+str(BoardSlot[i]),1,'2ad2da'])
#                    self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
#                    self.Board_marknum['2DA2AD']=i
#                    zz = self.fpga.dll.sys_open_ecc(i)
#                    self.Board_marknum['2DA2AD_BoardNumID']=zz
                if BoardType[i]==51:
#                    print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':4da')
                    self.BoardInfo[str(i)]=['4da','slot'+str(BoardSlot[i])]
                    self.da_ch.append(['slot'+str(BoardSlot[i]),0,'4da'])
                    self.da_ch.append(['slot'+str(BoardSlot[i]),1,'4da'])
                    self.da_ch.append(['slot'+str(BoardSlot[i]),2,'4da'])
                    self.da_ch.append(['slot'+str(BoardSlot[i]),3,'4da'])
#                    self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
#                    zz = self.fpga.dll.sys_open_ecc(i)
#                    self.Board_marknum['6DA_BoardNumID']=zz
                if BoardType[i]==0x22:
#                    print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':4ad')
                    self.BoardInfo[str(i)]=['4ad','slot'+str(BoardSlot[i])]
                    self.ad_ch.append(['slot'+str(BoardSlot[i]),0,'4ad'])
                    self.ad_ch.append(['slot'+str(BoardSlot[i]),1,'4ad'])
                    self.ad_ch.append(['slot'+str(BoardSlot[i]),2,'4ad'])
                    self.ad_ch.append(['slot'+str(BoardSlot[i]),3,'4ad'])
                     
                self.fpga.dll.sys_open(i)
#                    self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
     
#                    zz = self.fpga.dll.sys_open_ecc(i)
#                    self.Board_marknum['DC_BoardNumID']=zz
        da_ch_bufe = copy.deepcopy(self.da_ch)
        for i in range(len(da_ch_bufe)):
            if da_ch_bufe[i][0] == 'slot0':
                self.da_ch[da_ch_bufe[i][1]] = da_ch_bufe[i]
            elif da_ch_bufe[i][0] == 'slot1':
                if da_ch_bufe[i][2] == "4da":
                    self.da_ch[da_ch_bufe[i][1]+4] = da_ch_bufe[i]
                elif da_ch_bufe[i][2] == "2ad2da":
                    self.da_ch[da_ch_bufe[i][1]+2] = da_ch_bufe[i]
            elif da_ch_bufe[i][0] == 'slot2':
                if da_ch_bufe[i][2] == "4da":
                    self.da_ch[da_ch_bufe[i][1]+8] = da_ch_bufe[i]
                elif da_ch_bufe[i][2] == "2ad2da":
                    self.da_ch[da_ch_bufe[i][1]+4] = da_ch_bufe[i]
                
        ad_ch_bufe = copy.deepcopy(self.ad_ch)
        for i in range(len(ad_ch_bufe)):
            if ad_ch_bufe[i][0] == 'slot0':
                self.ad_ch[ad_ch_bufe[i][1]] = ad_ch_bufe[i]
            elif ad_ch_bufe[i][0] == 'slot1':
                if ad_ch_bufe[i][2] == "4ad":
                    self.ad_ch[ad_ch_bufe[i][1]+4] = ad_ch_bufe[i]
                elif ad_ch_bufe[i][2] == "2ad2da":
                    self.ad_ch[ad_ch_bufe[i][1]+2] = ad_ch_bufe[i]
            elif ad_ch_bufe[i][0] == 'slot2':
                if ad_ch_bufe[i][2] == "4ad":
                    self.ad_ch[ad_ch_bufe[i][1]+8] = ad_ch_bufe[i]
                elif ad_ch_bufe[i][2] == "2ad2da":
                    self.ad_ch[ad_ch_bufe[i][1]+4] = ad_ch_bufe[i]
            
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

    def pcie_wr_data(self,slot,chennel_num,addr,data):
        
        pcie_dma_wr_len = 2048*16
        
        data_len = np.ceil(len(data)/pcie_dma_wr_len).astype(int)*pcie_dma_wr_len
        
        data_wr_bufe = np.zeros(data_len)
        data_wr_bufe[:len(data)] = data
        
        data_wr_bufe = np.reshape(data_wr_bufe,(data_len//pcie_dma_wr_len,pcie_dma_wr_len))
    
        data_len_pcie = np.ceil(data_len/8).astype(int)
        data_addr_ddr = addr//20
        data_addr_ddr_sub = addr%20
        data_len_ddr = data_len//20
        data_len_ddr_sub = data_len%20
        
        baseaddr = 0x40*(chennel_num+1)
        self.writeReg(baseaddr,1,slot)
        self.writeReg(baseaddr,0,slot)
        self.writeReg(baseaddr+1,data_len_pcie,slot)
        self.writeReg(baseaddr+3,data_addr_ddr,slot)
        self.writeReg(baseaddr+4,data_addr_ddr_sub,slot)
        self.writeReg(baseaddr+5,data_len_ddr,slot)
        self.writeReg(baseaddr+6,data_len_ddr_sub,slot)
        
        self.writeReg(baseaddr+7,0,slot)#0write
        
        self.writeReg(baseaddr+2,1,slot)
        self.writeReg(baseaddr+2,0,slot)
        

        
        pbuf = ctypes.create_string_buffer(pcie_dma_wr_len*2)
        for i in range(len(data_wr_bufe)):
#            data_wr_bufe_i = np.int16(data_wr_bufe[i])
#            data_wr_bufe_i = ctypes.cast(data_wr_bufe_i.ctypes.data, ctypes.POINTER(ctypes.c_short))

            pbuf.raw = np.int16(data_wr_bufe[i])

            data_wr_bufe_i = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_short))

            self.fpga_dma_write_bysize(slot,0x10000000+0x20000*chennel_num,data_wr_bufe_i,pcie_dma_wr_len*2)

        pbuf = None
        return 'ok'

    def pcie_rd_data(self,slot,chennel_num,addr,data_len):
        
        pcie_dma_rd_len = 2048*8
        
        data_len_rd =  np.ceil(data_len/pcie_dma_rd_len).astype(int)*pcie_dma_rd_len
        
        data_addr_ddr = addr//20
        data_addr_ddr_sub = addr%20
        data_len_ddr = data_len_rd//20
        data_len_ddr_sub = data_len_rd%20
        
        baseaddr = 0x40*(chennel_num+1)
        
        self.writeReg(baseaddr,1,slot)
        self.writeReg(baseaddr,0,slot)
        
        self.writeReg(baseaddr+3,data_addr_ddr,slot)
        self.writeReg(baseaddr+4,data_addr_ddr_sub,slot)
        self.writeReg(baseaddr+5,data_len_ddr,slot)
        self.writeReg(baseaddr+6,data_len_ddr_sub,slot)
        
        self.writeReg(baseaddr+7,1,slot)#0write
        
        self.writeReg(baseaddr+2,1,slot)
        self.writeReg(baseaddr+2,0,slot)
      
        data_buf_i = []
        
        data_test,state = self.return_data_by_size(0x10000000+0x20000*chennel_num,data_len_rd*2,pcie_dma_rd_len*2,slot)
        data_buf_i = ctypes.POINTER(ctypes.c_short)(data_test)
        

        
        return data_buf_i[:data_len]



    def pcie_serial_write(self,data,slot):
        for send_cnt in range(len(data)):
            for i in range(10):
                if (self.readReg(0x20+2,slot) & 0x08) == 0:
                    break
                else:
                    time.sleep(0.01)
        
            self.writeReg(0x20+1,data[send_cnt],slot)
            
        return len(data)
    
    def pcie_serial_read(self,slot,time_out):
        recv_data = []
        recv_num = 0
        time0 = time.time()
        
        while 1:
            if (self.readReg(0x20+2,slot) & 0x01) == 1:
                recv_data.append(np.uint8(self.readReg(0x20,slot)))
                recv_num+=1
            if recv_num == 32:
                return recv_data
            time1 = time.time()
            if time1-time0>time_out:
                return 'time_out'
            
    def pcie_serial_reset_input_buffer(self,slot):
        while 1:
            if (self.readReg(0x20+2,slot) & 0x01) == 1:
                self.readReg(0x20,slot)
            else:
                break
        return
            
                
    def pcie_serial_send_cmd(self,slot,send_data):
                        
        self.pcie_serial_reset_input_buffer(slot)
        
        while 1:
            self.pcie_serial_write(send_data,slot)
            recv_data = self.pcie_serial_read(slot,0.5)
            
            if recv_data == send_data:
#                        print('cmd send done!')
                break  
    
    

    def serial_send_cmd(self,send_data):
        
        send_data = bytes(send_data)
        self.serialport.reset_input_buffer()
        while 1:
            self.serialport.write(send_data)
            recv_data = self.serialport.read_all()
            
            if recv_data == send_data:
#                print('cmd send done!')
                return recv_data

    def find_serial_port(self):
        port_list = list(serial.tools.list_ports.comports())
        
        for i in range(len(port_list)):
            if port_list[i][0] == 'COM1':
                continue
            self.serialport = serial.Serial()  #/dev/ttyUSB0
            self.serialport.port = port_list[i][0]
            self.serialport.baudrate = 115200
            self.serialport.bytesize = 8
            self.serialport.parity = serial.PARITY_NONE
            self.serialport.stopbits = 1
            self.serialport.timeout = 0.3
            self.serialport.open()
            
            fband_data_buf=np.uint8(np.arange(32)+1)
            recv_com_data = self.serial_send_cmd(fband_data_buf)
            recv_com_data_i = np.zeros(len(recv_com_data))
            for ii in range(len(recv_com_data)):
                recv_com_data_i[ii] = np.uint8(recv_com_data[ii])
            recv_com_data_i = np.uint8(recv_com_data_i)
            if list(recv_com_data_i) == list(fband_data_buf):
    #            serialport.close()
                return port_list[i][0]
            else:
                self.serialport.close()
        
        return

    def trigger_ctrl(self,trigger_source,trigger_us,trigger_num,trigger_continue):
        #trigger_source 0 为内部触发，1为外部触发
        #trigger_us 触发周期单位us
        #trigger_num 触发次数，当trigger_continue为1时无效
        #trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        global sampling_g
        
        trigger_times = np.uint32(trigger_num)
        if sampling_g == 0:
            trigger_us_cnt = np.uint32(round(trigger_us/0.0064))
        else:
            trigger_us_cnt = np.uint32(round(trigger_us/0.008))
        trigger_block_en0 = 1
        trigger_block_en1 = 1
        trigger_block_en2 = 1
        trigger_block_en3 = 1
        trigger_block_en4 = 1
        trigger_block_en5 = 1
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x00))
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
        fband_data_buf.append(np.uint8(trigger_block_en0))
        fband_data_buf.append(np.uint8(trigger_block_en1))
        fband_data_buf.append(np.uint8(trigger_block_en2))
        fband_data_buf.append(np.uint8(trigger_block_en3))
        fband_data_buf.append(np.uint8(trigger_block_en4))
        fband_data_buf.append(np.uint8(trigger_block_en5))
        for i in range(13):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
        
        self.serial_send_cmd(fband_data_buf)

        return 'ok'

    def trigger_close(self):
        #关闭触发
        
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x02))
        for i in range(29):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
        self.serial_send_cmd(fband_data_buf)
        
        return 'ok'
    
    def system_sampling_cmd_send(self,board_id,cmd,sampling):
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(cmd))
        fband_data_buf.append(np.uint8(sampling))
        for i in range(28):
            fband_data_buf.append(np.uint8(0x00))
        if board_id == 0:
            self.serial_send_cmd(fband_data_buf)
        else:
            slot = self.BoardInfo[str(board_id-1)][1]
            self.pcie_serial_send_cmd(slot,fband_data_buf)
        
        return 'ok'
    
    def system_sampling(self,sampling,step,self_set):
        #切换采样率 0 为5Gsps；1 为4Gsps
        global sampling_g
        sampling_g = sampling
        
        self.trigger_close()
        
        for i in range(len(self.da_ch)):
            slot = self.da_ch[i][0]
            ch_num = self.da_ch[i][1]
    
            self.dac_ch_ctrl(slot,ch_num,1,0)
            self.dac_ch_ctrl(slot,ch_num,0,0)
        
        if sampling == 0:
            trigger_time = 6.4
        else:
            trigger_time = 8
        
        if self_set == 1:
            
            self.system_sampling_cmd_send(0,0x06,sampling)
            time.sleep(2)
            
            self.trigger_ctrl(0,trigger_time,10,0)
            
            time.sleep(0.5)
            
            self.system_sampling_cmd_send(0,0x07,sampling)
            time.sleep(0.5)
            
            self.trigger_ctrl(0,trigger_time,10,0)
            
            time.sleep(0.5)
            
            self.system_sampling_cmd_send(0,0x04,sampling)
            
            time.sleep(0.5)
            
            for i in range(self.board_number):
                self.system_sampling_cmd_send(i+1,0x01,sampling)
            
            time.sleep(5)
        
            self.trigger_ctrl(0,trigger_time,10,0)
            
            time.sleep(0.5*self.board_number)
            
            for i in range(self.board_number):
                self.system_sampling_cmd_send(i+1,0x02,sampling)
                
            time.sleep(0.5*self.board_number)
            
            self.trigger_ctrl(0,trigger_time,10,0)
            
            for i in range(self.board_number):
                self.system_sampling_cmd_send(i+1,0x03,sampling)
            
            time.sleep(5)
            
        else:
            if step == 0:
                self.system_sampling_cmd_send(0,0x03,sampling)
            elif step == 1:
                self.system_sampling_cmd_send(0,0x07,sampling)
                self.trigger_ctrl(1,10,0,0)
            elif step == 2:
                self.system_sampling_cmd_send(0,0x04,sampling)
            elif step == 3:
                for i in range(self.board_number):
                    self.system_sampling_cmd_send(i+1,0x01,sampling)
            elif step == 4:
                for i in range(self.board_number):
                    self.system_sampling_cmd_send(i+1,0x02,sampling)
            elif step == 5:
                for i in range(self.board_number):
                    self.system_sampling_cmd_send(i+1,0x03,sampling)

        return

    def dac_Nyquist_cfg(self,chennel_num,Nyquist):
        #切换频域
        #dac_chennel_in 为DAC通道数,从1开始
        #Nyquist 为DAC工作模式，0 为正常模式；1 为mix模式，适合高频段
        
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x04))
        fband_data_buf.append(np.uint8(ch_num))
        fband_data_buf.append(np.uint8(Nyquist))
        for j in range(27):
            fband_data_buf.append(np.uint8(0x00))
        self.pcie_serial_send_cmd(slot,fband_data_buf)
        return


    def write_dac_data(self,slot,chennel_num,dac_data):
        
        dac_data_bufe = dac_data
        
        if np.size(dac_data_bufe[0]) == 1:
            dac_data_bufe = [dac_data_bufe]
        
        dac_data_point = []
        
        start_addr = 0
        data_len = 0
        
        for i in range(len(dac_data_bufe)):
            data_message = []
            start_addr = start_addr + data_len
            data_len = len(dac_data_bufe[i])
            
            data_message.append(start_addr//20)
            data_message.append(start_addr%20)
            data_message.append((data_len+start_addr%20)//20)
            data_message.append((data_len+start_addr%20)%20)
            dac_data_point.append(data_message)
            
            self.pcie_wr_data(slot,chennel_num,start_addr,dac_data_bufe[i])
            
        return dac_data_point
        
    def dac_ch_ctrl(self,slot,chennel_num,dac_reset,dac_en):

        self.writeReg(0x40*(chennel_num+1),dac_reset+dac_en*2,slot)
        
        return 'ok'
        
    def dac_data_point(self,slot,chennel_num,data_point):
        
        dac_data_point_bufe = data_point
        
        if np.size(dac_data_point_bufe[0]) == 1:
            dac_data_point_bufe = [dac_data_point_bufe]
    
        data_len = np.ceil(len(data_point)*16/2048).astype(int)*2048
    
        data_wr_bufe = np.zeros(data_len)
        reg_data = []
        for i in range(len(dac_data_point_bufe)):
            reg_data.append(np.uint16(dac_data_point_bufe[i][0]))
            reg_data.append(np.uint16(dac_data_point_bufe[i][0]>>16))
            reg_data.append(np.uint16(dac_data_point_bufe[i][1]))
            reg_data.append(np.uint16(0))
            reg_data.append(np.uint16(dac_data_point_bufe[i][2]))
            reg_data.append(np.uint16(dac_data_point_bufe[i][2]>>16))
            reg_data.append(np.uint16(dac_data_point_bufe[i][3]))
            reg_data.append(np.uint16(0))
        
        data_wr_bufe[:len(data_point)*8] = np.reshape(reg_data,-1)
        data_wr_bufe = np.reshape(data_wr_bufe,(data_len//2048,2048))
        
        pbuf = ctypes.create_string_buffer(4096)
        
        for i in range(len(data_wr_bufe)):
#            data_wr_bufe_i = np.int16(data_wr_bufe[i])
#            data_wr_bufe_i = ctypes.cast(data_wr_bufe_i.ctypes.data, ctypes.POINTER(ctypes.c_short))
#            self.fpga_dma_write_bysize(slot,0x100000+0x20000*chennel_num+0x1000*i,data_wr_bufe_i,4096)
        
            pbuf.raw = np.int16(data_wr_bufe[i])
            data_wr_bufe_i = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_short))
            self.fpga_dma_write_bysize(slot,0x100000+0x20000*chennel_num+0x1000*i,data_wr_bufe_i,4096)

        pbuf = None
        
        
        return 'ok'
    
    def dac_replay_point(self,slot,chennel_num,data_point):
        
        dac_point_bufe = data_point
        if np.size(dac_point_bufe[0]) == 1:
            dac_point_bufe = [dac_point_bufe]
        
        data_len = np.ceil(len(data_point)*16/2048).astype(int)*2048
    
        data_wr_bufe = np.zeros(data_len)
        
        reg_data = []
        for i in range(len(dac_point_bufe)):
            reg_data.append(np.uint16(dac_point_bufe[i][0]))
            reg_data.append(np.uint16(dac_point_bufe[i][1]))
            reg_data.append(np.uint16(dac_point_bufe[i][2]))
            reg_data.append(np.uint16(dac_point_bufe[i][2]>>16))
            reg_data.append(np.uint16(dac_point_bufe[i][3]))
            reg_data.append(np.uint16(dac_point_bufe[i][3]>>16) + np.uint16(dac_point_bufe[i][4]<<15))
            reg_data.append(0)
            reg_data.append(0)
        
        data_wr_bufe[:len(data_point)*8] = np.reshape(reg_data,-1)
        data_wr_bufe = np.reshape(data_wr_bufe,(data_len//2048,2048))
#        for i in range(len(data_wr_bufe)):
#            data_wr_bufe_i = np.int16(data_wr_bufe[i])
#            data_wr_bufe_i = ctypes.cast(data_wr_bufe_i.ctypes.data, ctypes.POINTER(ctypes.c_short))
#            self.fpga_dma_write_bysize(slot,0x200000+0x20000*chennel_num+0x1000*i,data_wr_bufe_i,4096)

        pbuf = ctypes.create_string_buffer(4096)
        
        for i in range(len(data_wr_bufe)):
            pbuf.raw = np.int16(data_wr_bufe[i])
            data_wr_bufe_i = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_short))
            self.fpga_dma_write_bysize(slot,0x200000+0x20000*chennel_num+0x1000*i,data_wr_bufe_i,4096)

        pbuf = None

    def dac_updata(self,chennel_num,dac_data):
        #dac_chennel_num为dac通道号，从0开始
        
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]

        self.dac_ch_ctrl(slot,ch_num,1,0)
        self.dac_ch_ctrl(slot,ch_num,0,0)
        dac_data_point_bufe = self.write_dac_data(slot,ch_num,dac_data)
        
        self.dac_data_point(slot,ch_num,dac_data_point_bufe)

        return

    
    
    def dac_point_updata(self,chennel_num,data_point):
        #dac_chennel_num为dac通道号，从1开始
        if chennel_num > (len(self.da_ch)-1) or chennel_num < 0:
            print('未找到dac通道：',chennel_num)
            return
        
        slot = self.da_ch[chennel_num][0]
        ch_num = self.da_ch[chennel_num][1]
        
        self.dac_ch_ctrl(slot,ch_num,1,0)
        self.dac_ch_ctrl(slot,ch_num,0,0)
        self.dac_replay_point(slot,ch_num,data_point)
        
        self.dac_ch_ctrl(slot,ch_num,0,1)

        return


    def dac_ch_close(self,slot,chennel_num,dac_chennel):
        for i in range(self.board_number):
            if slot == self.BoardInfo[str(i)][1]:
                if ((self.BoardInfo[str(i)][0] == '2ad2da') and (chennel_num<2)) or ((self.BoardInfo[str(i)][0] == '4da') and (chennel_num<4)):

                    self.dac_ch_ctrl(slot,chennel_num,1,0)
                    self.dac_ch_ctrl(slot,chennel_num,0,0)
                    
                else:
                    
                    print('未找到dac通道：',chennel_num)
                    return




#%%:
if __name__=='__main__':
    dev=fpgadev()  
    
