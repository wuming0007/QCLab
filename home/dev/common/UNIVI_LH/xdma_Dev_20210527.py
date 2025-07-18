# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 07:15:22 2009
fpga 驱动 wz
调用dll文件，分别对板卡进行识别以及简单的函数的实现。
与地址分离应该，次类中应该不包含地址。
@author: wz
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
# import matplotlib.pyplot as plt
from pathlib import Path

from .fpgaaddr import addr
path_new =  str(Path(__file__).parent/'QUbit_XDMA_DLL_20211108.dll')



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
        print('################## XDMA loaded',self.dll)
#        self.dll_i = ctypes.WinDLL(path)
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
        self.demodulation_result={'demo_now_data':0,'demo_now_compare_times':0,'Cnt_0':0,'Cnt_1':0,'demo_sum_data':0}
        self.allchanel_compare_value=[0]*21
        self.allchanel_compare_len=[0]*21
        if fpgadev._initflag==False:
            
            self.closefalg=True
            self.boardtypeflag='0'
            self.temp=ctypes.c_int32(0)
            self.StructInfo = StructPointer()
            self.fpga=fpgadevdll()
            self.fpga.dll.ALL_Sys_Init.rgtypes = [StructPointer] #ctypes.POINTER(StructPointer)
            aa=self.fpga.dll.ALL_Sys_Init(ctypes.byref(self.StructInfo))
            self.BoardInfo={}
            self.Board_marknum={}
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
         if slot== self.BoardInfo[str(borad_id)][1]:
            self.data_test = dma_data()
            self.fpga.dll.dma_return_data.rgtypes = [dma_data,ctypes.c_int , ctypes.c_longlong , ctypes.c_int] #ctypes.POINTER(StructPointer)
            self.fpga.dll.dma_return_data(ctypes.byref(self.data_test),borad_id,ctypes.c_longlong(addr),8192)
            Data_Test = self.data_test.Data_Test   
            return Data_Test
    def return_data_by_size(self,dma_addr,lenth,slot):
       for borad_id in range(self.board_number):
         if slot== self.BoardInfo[str(borad_id)][1]:
            data_test = (ctypes.c_ubyte *(lenth*8192))()
            self.fpga.dll.dma_return_data_by_size.rgtypes = [ctypes.POINTER(ctypes.c_ubyte),ctypes.c_int , ctypes.c_longlong , ctypes.c_int] #ctypes.POINTER(StructPointer)
            state = self.fpga.dll.dma_return_data_by_size(data_test,borad_id,ctypes.c_longlong(dma_addr),lenth*8192)
            return data_test,state
    def return_sum_data(self,addr,slot):
       for borad_id in range(self.board_number):
         if slot== self.BoardInfo[str(borad_id)][1]:
            self.data_test = dma_data_sum()
            self.fpga.dll.dma_return_data.rgtypes = [dma_data,ctypes.c_int , ctypes.c_longlong , ctypes.c_int] #ctypes.POINTER(StructPointer)
            self.fpga.dll.dma_return_data(ctypes.byref(self.data_test),borad_id,ctypes.c_longlong(addr),8192)
            Data_Test = self.data_test.Data_Test   
            return Data_Test
        
    def boardinfo(self):
         BoardNum=self.StructInfo.BoardNum
         self.board_number = BoardNum
         BoardSlot=self.StructInfo.BoardSlot
         BoardType=self.StructInfo.BoardType
         print('现在一共有'+str(BoardNum)+'个板卡')
         if fpgadev._initflag==False:
             for i in range(BoardNum):
                 if BoardType[i]==17:#hex(11)
                     print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':两AD两DA(2DA2AD)')
                     self.BoardInfo[str(i)]=['2DA2AD','slot'+str(BoardSlot[i])]
                     self.Board_marknum['2DA2AD']=i
#                     self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
#                     self.Board_marknum['2DA2AD']=i
#                     zz = self.fpga.dll.sys_open_ecc(i)
#                     self.Board_marknum['2DA2AD_BoardNumID']=zz
                 if BoardType[i]==34:
                     print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':时钟板(Clock)')
                     self.BoardInfo[str(i)]=['Clock','slot'+str(BoardSlot[i])]
                     self.Board_marknum['Clock']=i
#                     self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
#                     self.Board_marknum['Clock']=i
#                     zz = self.fpga.dll.sys_open_ecc(i)
#                     self.Board_marknum['Clock_BoardNumID']=zz
                 if BoardType[i]==51:
                     print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':六DA板(6DA)')
                     self.BoardInfo[str(i)]=['6DA','slot'+str(BoardSlot[i])]
                     self.Board_marknum['6DA']=i
#                     self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
#                     zz = self.fpga.dll.sys_open_ecc(i)
#                     self.Board_marknum['6DA_BoardNumID']=zz
                 if BoardType[i]==68:
                     print(str(i)+'号板卡,槽位'+str(BoardSlot[i])+':偏置板(DC)')
                     self.BoardInfo[str(i)]=['DC','slot'+str(BoardSlot[i])]
                     self.Board_marknum['DC']=i
                 self.fpga.dll.sys_open(i)
#                     self.Board_marknum[i][1]='slot'+str(BoardSlot[i])
     
#                     zz = self.fpga.dll.sys_open_ecc(i)
#                     self.Board_marknum['DC_BoardNumID']=zz
         print(self.BoardInfo) 
         print(self.Board_marknum) 
    def opencard(self,slot):
        for i in range(self.board_number):
            if slot== self.BoardInfo[str(i)][1]:
                return self.fpga.dll.sys_open(i)
            else:
                pass
           
        print('错误，没有此板卡')
    def closecard(self,slot):
        for i in range(self.board_number):
             if slot== self.BoardInfo[str(i)][1]:
                return self.fpga.dll.sys_close(i)
    def fpga_dma_write(self,bus_id,addr,data):
        size = 4096
#        print(size)
        pcie_fpga_dma_write = self.fpga.dll.sys_dma_write  # 取得函数
        pcie_fpga_dma_write.argtypes = [ctypes.c_int,ctypes.c_longlong,ctypes.POINTER(ctypes.c_short), ctypes.c_int]
        return pcie_fpga_dma_write(bus_id,addr,data,size)
    
    
    def fpga_dma_write_bysize(self,bus_id,addr,data,size):
        pcie_fpga_dma_write = self.fpga.dll.sys_dma_write  # 取得函数
        pcie_fpga_dma_write.argtypes = [ctypes.c_int,ctypes.c_longlong,ctypes.POINTER(ctypes.c_short), ctypes.c_int]
        return pcie_fpga_dma_write(bus_id,addr,data,size)
        
        
        
        
        
    def fpga_dma_read(self,bus_id,addr,size):
        pcie_fpga_dma_read = (self.fpga.dll.sys_dma_read)
        pcie_fpga_dma_read.argtypes = [ctypes.c_int,ctypes.c_longlong, ctypes.c_longlong]
        return ctypes.c_uint64(pcie_fpga_dma_read(bus_id,addr,size))
    def readReg(self,addr,slot):
         for i in range(self.board_number):
                if slot== self.BoardInfo[str(i)][1]:
                    self.fpga.dll.sys_read32(0,addr*4,ctypes.byref(self.temp),i)
                    return self.temp.value
#        if  self.closefalg:
#            print('错误,已经关闭板卡')
#        else:
            
    
    def writeReg(self,addr,data,slot=''):
        for i in range(self.board_number):
            if slot== self.BoardInfo[str(i)][1]:
                return self.fpga.dll.sys_write32(0,addr*4,data,i)
#        if  self.closefalg:
#            print('错误,已经关闭板卡')
#        else:
            
    def settrigT(self,T_us=500,times=1000,continueflag=True,trigger_source=False,slot=''):
        for i in range(self.board_number):
                if slot== self.BoardInfo[str(i)][1]:
        #T_us 周期时间
        #如果continueflag 为False 一共回放 times次 之后信号消失
                    times_i = times-1
#                    self.opencard('Clock','slot6')
                    if trigger_source:
                        self.writeReg(0x12,2,slot)
                    else:
                        self.writeReg(0x12,4,slot) # funtionc reset
                        if continueflag:
#                            val=int(T_us*1000/12.8)+0x80000000
                            val = int(np.ceil(int(T_us*1000/12.8)/4).astype(int) * 4)+0x80000000
                        else:
#                            val=int(T_us*1000/12.8)
                            val = int(np.ceil(int(T_us*1000/12.8)/4).astype(int) * 4)
                        self.writeReg(0x14,val,slot)
                        self.writeReg(0x12, times_i*8+0,slot)
                        time.sleep(0.0005)#等待fft 结束
                        self.writeReg(0x12, times_i*8+1,slot)##?? 次数最多12次
                    return 'ok'
                
        
    def settrig_delay(self,T_us,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='CLOCK':
                    
                    val=int(T_us*1000/12.8)
                    self.writeReg(val,slot)  #1

                    return 'ok'
        
    def data16_32(self,data_l,data_g):
        dd = (data_l & 0xffff) | data_g<<16
        return dd
    
    def data32_16(self,data):
        dd=[]
        for x in data:
            dd.append(np.int16(x%65536))
            dd.append(np.int16(x/65536))
        return dd
    
    def cal_addr(self,aa=[]):
        dd=0
        for x in aa:
            dd=x[0]*2**x[1]+dd
        return dd
    
#    def setGain(self,moduleIQ=[0,0],DB=0,slot=''):
#        for i in range(self.board_number):
#            if slot== self.BoardInfo[str(i)][1]:
#                Modulestr='module'+str(moduleIQ[0])
#                if moduleIQ[1]==1:
#                    settingadr=addr(self.boardtypeflag,Modulestr,'Gain_I')
#                    self.writeReg(settingadr,DB,slot)
#                else:
#                    settingadr=addr(self.boardtypeflag,Modulestr,'Gain_Q')
#                    self.writeReg(settingadr,DB,slot)
#                return 'ok'
#
#        
#    
#    def  setoffset(self,moduleIQ=[0,0],offset=0,slot=''):
#        for i in range(self.board_number):
#            if slot== self.BoardInfo[str(i)][1]:
#                 Modulestr='module'+str(moduleIQ[0])
#                 settingadr=addr(self.boardtypeflag,Modulestr,'offset')
#                 temp=self.readReg(settingadr,slot)
#                 if moduleIQ[1]==1:
#                    val=temp%65536+offset*65536
#                    self.writeReg(settingadr,val,slot)
#                 else:
#                    val=temp//65536*65536+offset #I
#                    self.writeReg(settingadr,val,slot)
#                 return 'ok'
                 


                    

                
    
    def demodulation_allsetting(self,reset,demodulation_en,delay,compare_times,slot):
        #reset demodulation解调模块 总控制 所有通道的比较和计算 工作状态回到原始状态
        #demodulation_en 解调模块总使能，如果使能为否 解调模块所有通道不工作
        
        #compare_times 解调之后比较的次数，也就是一共解调多少次，比较多少次
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    param1=demodulation_en*2**31 + delay*2 + reset
                    self.writeReg(0xc00,param1,slot)
                    self.writeReg(0xc01,compare_times,slot)
                    
                else:
                    print('sel board err')
        
                

#    def demodulation_channelsetting(self,channelnum,channel_en,compare_continue,compare_len,real_sin,imag_cos,compare_value,channel_11addsetting=[],slot):
    def demodulation_channelsetting(self,channelnum,channel_en,compare_continue,compare_len,real_sin,imag_cos,compare_value,slot):
        #channelnum  解调单通道设置 通道数
        #channelen 通道是否使能
        #compare_len  所有通道的解调的长度 最大为2048个点 
        #real_sin 与解调出来的数的实部相乘的数
        #imag_cos 与解调出来的数的虚部相乘的数(a+bj)*(real_sin+imag_cos*j)=real(a*real_sin-b*imag_cos)
        #compare_value 与解调出来的数的实部a*real_sin-b*imag_cos 相比较的数
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.allchanel_compare_value[channelnum-1]=compare_value
                    self.allchanel_compare_len[channelnum-1]=compare_len-1
                    if channelnum>21:
                        print('没有这个通道，最多解调通道为21 21位解调反馈通道 1-20为正常解调通道')
                    elif channelnum==21:
#                        if len(channel_11addsetting)==4:
                        param0=self.cal_addr([[compare_len-1,1],[channel_en,0]])
                        self.writeReg(0x1400,param0,slot)
                        param0=self.data16_32(int(real_sin),int(imag_cos))
                        self.writeReg(0x1401,int(param0),slot)
                        
                        
                        self.writeReg(0x1402,int(compare_value & 0xffff),slot)
                        self.writeReg(0x1403,int(compare_value>>16 & 0xffffffff),slot)
                            
                            
                            
#                            param1=self.cal_addr([[channel_en,11]])
#                            param0=self.data16_32([compare_value,param1])[0]
#                            self.writeReg(0x10182,param0,slot)
#                            self.writeReg(0x10183,int(np.int32(compare_value/2**16)),i)
#                            addr=(channel_11addsetting[0]-1)
#                            param1=self.cal_addr([[channel_11addsetting[2],1],[channel_11addsetting[1],0]])
#                            param0=self.data16_32([param1,channel_11addsetting[3]])[0]
#                            self.writeReg(0x10a00+addr,param0,slot)
#                        else:
#                            print('参数不够，应该为4个;1判断波形出之前回放波形号，如果不想判断之前有波形，则这个波形号位宽写0'
#                               +'2下一个波形是否反馈，反馈使能；3：判断为0时回放波形号；4判断为1时回放波形号')
                    else:
                        dma_addr=(channelnum-1)
#                        if channel_en == 1:
#                            param1=self.cal_addr([[compare_continue,12],[0,11],[compare_len-1,0]])
#                            param0=self.data16_32([int(np.int16(compare_value%2**16)),param1])[0]
#                            self.writeReg(0xc03+addr*3,param0,slot)
                        
                        param0=self.data16_32(int(real_sin),int(imag_cos))
                        self.writeReg(0xc02+dma_addr*3,param0,slot)
                        self.writeReg(0xc04+dma_addr*3,int(compare_value>>16 & 0xffffffff),slot)#这地方的值有问题能为浮点型数据么？？？？？
                        param1=self.cal_addr([[compare_continue,13],[channel_en,12],[compare_len-1,0]])
                        param0=self.data16_32(int(np.int16(compare_value & 0xffff)),param1)
                        
                        self.writeReg(0xc03+dma_addr*3,param0,slot)
                else:
                    print('sel board err')
       

        
    def set_demodulation_data(self,channelnum,data_i,data_q,slot):# 只有2AD2DA，有次功能
        #channelnum为通道数从1-10 最多可以有10个通道 每一个通道copy一下原始采集的数据 当为11 时为反馈的模式通道
        #sindata,cosdata 为16位的 通道借条数据 一般为2048个点，写进去用的时候是按读取的点数来计算的
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    data_buf=np.zeros(8192)
                    sindata_cnt = 0
                    cosdata_cnt = 0
                    data_len = int(len(data_i)*2)
                    for i in range(data_len):
                        if i%8<4:
                            data_buf[i] = data_i[sindata_cnt]
                            sindata_cnt = sindata_cnt+1
                        else:
                            data_buf[i] = data_q[cosdata_cnt]
                            cosdata_cnt = cosdata_cnt+1
                    
                    if channelnum>21:
                        print('没有这个通道，最多解调通道为11 11位解调反馈通道 1-10为正常解调通道')
#                    elif channelnum==11:
#                        data_addr = 0xd8000000
#                        data_buf = np.int16(data_buf)
#                        if not data_buf.flags['C_CONTIGUOUS']:
#                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
#                        databuf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
#                        self.fpga_dma_write(board_id,data_addr,databuf)
                    elif channelnum==21:
                        data_addr = 0xc4000000 + (32-1)*0x4000
                        data_buf_wr = np.int16(data_buf[:2048])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                        
                        data_addr = data_addr + 0x1000
                        data_buf_wr = np.int16(data_buf[2048:4096])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                        
                        data_addr = data_addr + 0x1000
                        data_buf_wr = np.int16(data_buf[4096:6144])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                        
                        data_addr = data_addr + 0x1000
                        data_buf_wr = np.int16(data_buf[6144:8192])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                    else:
                        data_addr = 0xc4000000 + (channelnum-1)*0x4000
                        data_buf_wr = np.int16(data_buf[:2048])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                        
                        data_addr = data_addr + 0x1000
                        data_buf_wr = np.int16(data_buf[2048:4096])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                        
                        data_addr = data_addr + 0x1000
                        data_buf_wr = np.int16(data_buf[4096:6144])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                        
                        data_addr = data_addr + 0x1000
                        data_buf_wr = np.int16(data_buf[6144:8192])
                        if not data_buf_wr.flags['C_CONTIGUOUS']:
                            data_buf_wr = np.ascontiguous(data_buf_wr, dtype=data_buf_wr.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf_wr = ctypes.cast(data_buf_wr.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,data_addr,data_buf_wr)
                    

                else:
                    print('sel board err')


    def demodulation_result_update(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0xc3f,0,slot)
                    self.writeReg(0xc3f,1,slot) 
                else:
                    print('sel board err')
   
            
    def get_demodulation_result(self,channelnum,slot):
      ## 把通道使能放在里边 为了直接能得到更新的数据
#        compare_value=self.allchanel_compare_value[channelnum-1]
#        compare_len=self.allchanel_compare_len[channelnum-1]
#        addr=(channelnum-1)
#        param1=self.cal_addr([[0,11],[compare_len-1,0]])
#        param0=self.data16_32([int(np.int16(compare_value%2**16)),param1])[0]
#        self.writeReg(0x103+addr*2,param0)
#        # 先是0 再为1 上升沿使能
#        param1=self.cal_addr([[1,11],[compare_len-1,0]])
#        param0=self.data16_32([int(np.int16(compare_value%2**16)),param1])[0]
#        self.writeReg(0x103+addr*2,param0)
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if channelnum>21:
                        print('没有这个通道，最多解调通道为21 21位解调反馈通道 1-20为正常解调通道')
                    elif channelnum==21:
                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x1405,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1404,slot),32)),64))/2**16)
                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x1407,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1406,slot),32)),64))/2**16)
                        self.demodulation_result['demo_now_data']=real + imag*1j
                        self.demodulation_result['demo_now_compare_times']=0
                        self.demodulation_result['Cnt_0']=0
                        self.demodulation_result['Cnt_1']=0
                        self.demodulation_result['demo_sum_data']=0
#                        self.writeReg(0x116,0,a)
                        return  self.demodulation_result.copy()
                    elif channelnum > 10:
                        dma_addr=channelnum-11
#                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x1801+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1800+dma_addr*4,slot),32)),64))/2**16/2**12)
#                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x1803+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1802+dma_addr*4,slot),32)),64))/2**16/2**12)
                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x1865+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1864+dma_addr*4,slot),32)),64))/2**16)
                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x1867+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1866+dma_addr*4,slot),32)),64))/2**16)
                        self.demodulation_result['demo_now_data']=real + imag*1j
                        self.demodulation_result['demo_now_compare_times']=self.readReg(0xc02,slot)
                        self.demodulation_result['Cnt_0']=self.readReg(0x188c+dma_addr*2,slot)
                        self.demodulation_result['Cnt_1']=self.readReg(0x188d+dma_addr*2,slot)
#                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x183d+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x183c+dma_addr*4,slot),32)),64))/2**16)
#                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x183f+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x183e+dma_addr*4,slot),32)),64))/2**16)
                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x18a1+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x18a0+dma_addr*4,slot),32)),64)))
                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x18a3+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x18a2+dma_addr*4,slot),32)),64)))
                        self.demodulation_result['demo_sum_data']=real + imag*1j
                        return  self.demodulation_result.copy()
                    else:
                        dma_addr=channelnum-1
#                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x1801+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1800+dma_addr*4,slot),32)),64))/2**16/2**12)
#                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x1803+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1802+dma_addr*4,slot),32)),64))/2**16/2**12)
                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x1801+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1800+dma_addr*4,slot),32)),64))/2**16)
                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x1803+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x1802+dma_addr*4,slot),32)),64))/2**16)
                        self.demodulation_result['demo_now_data']=real + imag*1j
                        self.demodulation_result['demo_now_compare_times']=self.readReg(0xc02,slot)
                        self.demodulation_result['Cnt_0']=self.readReg(0x1828+dma_addr*2,slot)
                        self.demodulation_result['Cnt_1']=self.readReg(0x1829+dma_addr*2,slot)
#                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x183d+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x183c+dma_addr*4,slot),32)),64))/2**16)
#                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x183f+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x183e+dma_addr*4,slot),32)),64))/2**16)
                        real = int((self.orig2comp(self.comp2orig(self.readReg(0x183d+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x183c+dma_addr*4,slot),32)),64)))
                        imag = int((self.orig2comp(self.comp2orig(self.readReg(0x183f+dma_addr*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x183e+dma_addr*4,slot),32)),64)))
                        self.demodulation_result['demo_sum_data']=real + imag*1j
                        return  self.demodulation_result.copy()
            
                else:
                    print('sel board err')


    def get_demodulation_result_save(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    data_buf=[]
                    for i in range(4096):
                        addr = 0x2000 + i
                        data_buf.append(self.readReg(addr,slot))
                    return data_buf
                else:
                    print('sel board err')
        
    def get_demodulation_result_savecnt(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    data_buf=[]
                    for i in range(1024):
                        addr = 0x1c00 + i
                        data_buf.append(self.readReg(addr,slot))
                    return data_buf
                else:
                    print('sel board err')
    
    def get_demo_save_data(self,channelnum,data_len,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                        
                    data_addr = 0x2fe000000 + (channelnum-1)*0x100000
                    
                    data_buf=[]
                    data_adci_real = []
                    data_adci_imag = []
                    data_adcq_real = []
                    data_adcq_imag = []
                    
                    if data_len%256 == 0:
                        read_data_cnt = int(data_len/256)
                    else:
                        read_data_cnt = int(data_len/256 + 1)

                    
                    data_buf,state = self.return_data_by_size(data_addr,read_data_cnt,slot)
                    
                    data_buf_i = ctypes.POINTER(ctypes.c_longlong)(data_buf)
                    
                    data_buf_0 = np.int64(data_buf_i[:1024*read_data_cnt:4])
                    print('buf',data_buf_0)
                    data_buf_1 = np.int64(data_buf_i[1:1024*read_data_cnt:4])
                    data_buf_2 = np.int64(data_buf_i[2:1024*read_data_cnt:4])
                    data_buf_3 = np.int64(data_buf_i[3:1024*read_data_cnt:4])
                    
                    
                    data_adci_real.extend(np.int64(data_buf_0>>16))
                    data_adci_imag.extend(np.int64(data_buf_1>>16))
                    data_adcq_real.extend(np.int64(data_buf_2>>16))
                    data_adcq_imag.extend(np.int64(data_buf_3>>16))
                        
                        
                    adci_real_out = np.array(data_adci_real[:data_len])
                    adci_imag_out = np.array(data_adci_imag[:data_len])
                    adcq_real_out = np.array(data_adcq_real[:data_len])
                    adcq_imag_out = np.array(data_adcq_imag[:data_len])

#                    for i in range(data_len):
#                        data_out.extend(np.complex(data_i_out[i],data_q_out[i]))
                    data_i_out = adci_real_out + adci_imag_out*1j
                    data_q_out = adcq_real_out + adcq_imag_out*1j
                        

                    
                    return adci_real_out+adcq_real_out,adci_imag_out+adcq_imag_out
                    # return data_i_out,data_q_out
                else:
                    print('not adc board')
                    return {}

              

        
#    def writeWaveform(self,moduleIQ=[0,0],setting={},data=[],slot=''):
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
#                self.boardtypeflag = self.BoardInfo[str(a)][0]
#        #moduleIQ 第一个为第几个模块 第二个为IQ 通道 I为0 Q 为1
#        #wave_id波形好设置 lenth播放波形长度 一个寄存器为2048点 此为播放从0到lenth点的波形后边的不回放
#        #dac_begin_point dac_end_point 此为之前没用关断功能 参数默认为0和2048 功能没用
#        #next_begin_addr 设置下次回放的地址 
#        #next_wave_en 下次波形是否开始 如果为0 接下来的都不回放
#        #dac_palyback_cnt 本次波形回放次数
#        #data_delay  如果dac_palyback_cnt比1大 本波形号两次回放之间的延时 也是0.4ns 一个点
#                Modulestr='module'+str(moduleIQ[0])
#                param1=self.data16_32([setting['lenth'],int(setting['delayt']*2500)])[0]
##                param2=self.data16_32([setting['dac_begin_point'],setting['dac_end_point']])[0]
#                param2=self.data16_32([0,2047])[0]
#                param3_0=self.cal_addr([[setting['next_begin_addr'],0],[setting['next_wave_en'],6]])
#                param3=self.data16_32([param3_0,int(setting['data_delay']*2500)])[0]
#                param4=setting['dac_palyback_cnt']
#                wave_id=setting['wave_id']
#                print(wave_id)
#                settingadr=addr(self.boardtypeflag,Modulestr,'setting')
#                
#                self.writeReg(settingadr+4*wave_id,param1,slot)
#                self.writeReg(settingadr+4*wave_id+1,param2,slot)
#                self.writeReg(settingadr+4*wave_id+2,param3,slot)
#                self.writeReg(settingadr+4*wave_id+3,param4,slot)
#                
#                if len(data)==0:
#                    print('no wave write')
#                else:
#                    data_in=[np.int16(x) for x in data]
#                    data_in=self.data16_32(data_in)
#                    if moduleIQ[1]==1:
#                        dataaddr=addr(self.boardtypeflag,Modulestr,'Qdata')
#                    else:
#                        dataaddr=addr(self.boardtypeflag,Modulestr,'Idata')
#                    for i in range(setting['lenth']//2+setting['lenth']%2):
#                         self.writeReg(dataaddr+i+0x400*wave_id,data_in[i],slot)
#                return 'ok'
#            
#     
#                
#    def writeWavelong(self,moduleIQ=[0,0],Data=[],delay=[0],slot=''):
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
#                points=len(Data)
#                print(len(Data))
#                if points==0:
#                    points=1
#                    Data=[0]
#                if points>64*2048:
#                    print('data too long ,please check it')
#                    sys.exit()
#                Data=Data*(2**14-1)
#                if points%2048>=1:
#                    regNum=int(points//2048)+1
#                else:
#                     regNum=int(points//2048)
#                allset=[]
#                alldelay=[0]*regNum
#                alldelay[:len(delay)]=delay
#                for i in range(regNum):
#                    temp={'wave_id':i,'lenth':2048,'delayt':alldelay[i],'dac_begin_point':0,'dac_end_point':2048,'next_begin_addr':i+1,
#                             'next_wave_en':1,'data_delay':0,'dac_palyback_cnt':1}
#                    if i==regNum-1:
#                        if points%2048==0:
#                            lens=2048
#                        else:
#                            lens=points%2048
#                        temp={'wave_id':i,'lenth':lens,'delayt':alldelay[i],'dac_begin_point':0,'dac_end_point':2048,'next_begin_addr':i+1,
#                             'next_wave_en':0,'data_delay':0,'dac_palyback_cnt':1}
#                    allset.append(temp)
#                for oneset in allset:
#                    start=oneset['wave_id']*2048
#                    stop=oneset['wave_id']*2048+2048
#                    if stop>points:
#                        stop=points
#                    self.writeWaveform(moduleIQ,oneset,Data[start:stop],slot)
#                self.CtrolReg_setting(moduleIQ[0],1,0,0,slot) # 先复位
#                self.CtrolReg_setting(moduleIQ[0],0,1,0,slot)#再使能}
#                return points
#
#      
#
#    def CtrolReg_setting(self,module=0,reset=0,start_en=1,nomal_wavenum=0,testen=0,testwavenum0=0,testwavenum1=0,slot=''):# 2DA2AD 没有testmodle功能 只有6DA 有
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
#        #module  第几个模块 模块0 AB  模块1 DE 模块2 C  模块3 F
#        #reset 高电平复位
#        #start_en 参数写完毕，开始回放
#        #nomal_wavenum  正常模式开始回放的波形号
#        #testen     test模式使能，不使能的时候位正常模式
#        #testwavenum0 test模式波形号第一个，test模式从设置好的两个波形号中交替周期回放波形
#        #testwavenum1 test模式波形号第二个，test模式从设置好的两个波形号中交替周期回放波形
#                Modulestr='module'+str(module)                                 #bit 6 test model en   nomal modle disen
#                param0_0=self.cal_addr([[reset,0],[start_en,5],[testen,6],[testwavenum0,7]])         
#                param0_1=self.cal_addr([[nomal_wavenum,0],[testwavenum1,8]])        
#                param0=self.data16_32([param0_0,param0_1])[0]
#                settingadr=addr(self.boardtypeflag,Modulestr,'daCtrolReg')
#                self.writeReg(settingadr,param0,slot)
#                time.sleep(0.01)
#                return 'ok'

     
    
#    def setdata_delay(self,delay=660,slot=''):
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
##                if self.boardtypeflag=='2DA2AD':
#                self.writeReg(0x23,delay,slot) 
##                else:
##                    print('请打开AD板')
#        #            sys.exit()
#                return self.boardtypeflag

    
#    def getdata(self,num,read_data_len,slot=''):
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
#        
##        self.writeReg(0x22,0x01)# 读取复位
##        time.sleep(0.01)
##        self.writeReg(0x24,Times2048*2048) #读取长度
##        self.writeReg(0x25,num-1)# 读取次数
##        self.writeReg(0x22,0x00)
##        time.sleep(0.01)
##        self.writeReg(0x22,0x02)# 上升沿开始工作
##        state=0
##        self.writeReg(0x27,0x00)
###        startT=time.clock()
##        while state == 0:
##            time.sleep(0.01)
##            print('duqu zhuangtai：',self.readReg(0x27))
##            state=self.readReg(0x27)%2# 数采完完全写到寄存器中
#    #        stopT=time.clock()
#    #        print('总采数时间：',stopT-startT)
#                
#                
#    #        totaltimes=Times2048*(num)
#    #        adc_data_i=[]
#    #        adc_data_q=[]
#    #        state=ctypes.c_int32(0)
#    #        for cnt_j in range(totaltimes):
#    #            self.writeReg(0x26,0x200*cnt_j)
#    #            self.writeReg(0x22,0x00)
#    #            self.writeReg(0x22,0x04)
#    #            
#    #            for cnt_i in range(1024):
#    #                aa=self.readReg(0x50000+cnt_i)
#    #                adc_data_i.append(np.int16(aa%65536)/16)
#    #                adc_data_i.append(np.int16(aa/65536)/16)
#    #                aa=self.readReg(0x60000+cnt_i)
#    #                adc_data_q.append(np.int16(aa%65536)/16)
#    #                adc_data_q.append(np.int16(aa/65536)/16)
#        
#                Times2048 = math.ceil(read_data_len/2048)
#                adc_data_i=[]
#                adc_data_q=[]
#                
#                self.writeReg(0x22,0x01,slot)# 读取复位
#                time.sleep(0.01)
#                self.writeReg(0x24,Times2048*2048,slot) #读取长度
#                self.writeReg(0x25,num-1,slot)# 读取次数
#                self.writeReg(0x22,0x00,slot)
#                time.sleep(0.01)
#                self.writeReg(0x22,0x02,slot)# 上升沿开始工作
#                state=0
#                self.writeReg(0x27,0x00,slot)
#        #        startT=time.clock()
#                while state == 0:
#                    time.sleep(0.01)
#                    print('duqu zhuangtai：',self.readReg(0x27,slot))
#                    state=self.readReg(0x27,slot)%2# 数采完完全写到寄存器中
#        
#                totaltimes = num
#                singletimes = read_data_len // 2048
#                read_data_mod = read_data_len % 2048
#                cnt_data = 0
#                state=ctypes.c_int32(0)
#                while totaltimes:
#                    if singletimes != 0:
#                        for cnt_j in range(singletimes):
#                            self.writeReg(0x26,0x200*(cnt_j+cnt_data),slot)
#                            self.writeReg(0x22,0x00,slot)
#                            self.writeReg(0x22,0x04,slot)
#                            
#                            for cnt_i in range(1024):
#                                aa=self.readReg(0x50000+cnt_i,slot)
#                                adc_data_i.append(np.int16(aa%65536)/16)
#                                adc_data_i.append(np.int16(aa/65536)/16)
#                                aa=self.readReg(0x60000+cnt_i,slot)
#                                adc_data_q.append(np.int16(aa%65536)/16)
#                                adc_data_q.append(np.int16(aa/65536)/16)
#                    
#                    cnt_data = cnt_data + singletimes
#                    
#                    if read_data_mod != 0:
#                        
#                        self.writeReg(0x26,0x200*cnt_data,slot)
#                        self.writeReg(0x22,0x00,slot)
#                        self.writeReg(0x22,0x04,slot)
#                        
#                        for cnt_i in range(read_data_mod//2):
#                            aa=self.readReg(0x50000+cnt_i,slot)
#                            adc_data_i.append(np.int16(aa%65536)/16)
#                            adc_data_i.append(np.int16(aa/65536)/16)
#                            aa=self.readReg(0x60000+cnt_i,slot)
#                            adc_data_q.append(np.int16(aa%65536)/16)
#                            adc_data_q.append(np.int16(aa/65536)/16)
#                        if read_data_mod % 2 ==1:
#                            aa=self.readReg(0x50000+read_data_mod//2+1,slot)
#                            adc_data_i.append(np.int16(aa%65536)/16)
#                            aa=self.readReg(0x60000+read_data_mod//2+1,slot)
#                            adc_data_q.append(np.int16(aa%65536)/16)
#                    cnt_data = cnt_data - singletimes
#                    cnt_data = cnt_data + Times2048
#                    totaltimes = totaltimes-1
#                        
#                    
#                    
#        #        lastT=time.clock()
#        #        print('总读取传输时间：',lastT-stopT)
#                return adc_data_i,adc_data_q
#
#   
#                
#                
#    
#
#        
#    def get_adc_sumdata(self,times,read_data_len,slot):
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
#                adc_data_i=[]
#                adc_data_q=[]
#                
#                self.writeReg(0x44,0x01,slot)# 读取复位
#                self.writeReg(0x45,times*2+1,slot)
#                self.writeReg(0x44,0x00,slot)# 读取复位
#                state=0
#                while state == 0:
#                    time.sleep(0.01)
#                    print('duqu zhuangtai：',self.readReg(0x46,slot))
#                    state=self.readReg(0x46,slot)%2# 数采完完全写到寄存器中
#        
#                state=ctypes.c_int32(0)
#                    
#                if read_data_len <= 2048:
#                    for cnt_i in range(read_data_len):
#                        aa=self.readReg(0x51000+cnt_i,slot)
#                        adc_data_i.append(aa)
#                        aa=self.readReg(0x61000+cnt_i,slot)
#                        adc_data_q.append(aa)
#                else:
#                    print('Point Overload')
#                        
#                return adc_data_i,adc_data_q

       
        
    
    def orig2comp(self,val, bits): #补码变原码
        if (val & (1 << (bits - 1))) != 0: 
            val = val - (1 << bits)       
        return val                       
    def comp2orig(self,val,bits): #原码变补码
        return int((bin(((1 << bits) - 1) & val)[2:]).zfill(bits),2)  


    
    def set_compare_parameter(self,compare_num,compare_sin,compare_cos,compare_real,fft_cnt,compare_en,slot):
        for a in range(self.board_number):
            if slot == self.BoardInfo[str(a)][1]:
                self.writeReg(0x102 + 2*compare_num,compare_sin+compare_cos*2**16,slot)
                self.writeReg(0x103 + 2*compare_num,compare_real%2**16+fft_cnt*2**16+compare_en*2**27,slot)# 80f f表示16
                self.writeReg(0x12c + compare_num,compare_real//(2**16),slot)

        
        
#    def getfftcntdata(self,Times2048,num,compare_num,slot):
#        for a in range(self.board_number):
#            if slot == self.BoardInfo[str(a)][1]:
#                self.writeReg(0x100,0x00b01,slot) #复位1 不能和复位0放到一起，太快监测不出来
#                self.writeReg(0x22,0x01,slot)# 读取复位
#                self.writeReg(0x27,0x00,slot)
#                self.writeReg(0x24,Times2048*2048,slot) #读取长度
#                self.writeReg(0x25,num-1,slot)# 读取次数
#                self.writeReg(0x100,0x10b00,slot)#复位0
#                self.writeReg(0x22,0x02,slot)# 上升沿开始工作
#                state=0
#                
#                
#                while state == 0:
#                    state=self.readReg(0x27,slot)# 数采完完全写到寄存器中
#                time.sleep(0.0005)#等待fft 结束
#                rd_fft_i = int((self.orig2comp(self.comp2orig(self.readReg(0x3001+compare_num*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x3000+compare_num*4,slot),32)),64))/2**16)
#                rd_fft_q = int((self.orig2comp(self.comp2orig(self.readReg(0x3003+compare_num*4,slot)*2**32,64)+(self.comp2orig(self.readReg(0x3002+compare_num*4,slot),32)),64))/2**16)
#                return rd_fft_i,rd_fft_q
#        
#    
#    
    def getfft(self,slot=''):
        for a in range(self.board_number):
            if slot == self.BoardInfo[str(a)][1]:
                adc_data_i=[]
                adc_data_q=[]
                for i in range(2048):
                    aa=self.readReg(0x1000+i,slot)
                    adc_data_i.append(np.int32(aa/256))#%% int16 会截位 史符号位和高位变少读出来的变错 65536  原本数据是24位的。
                for i in range(2048):
                    aa=self.readReg(0x1800+i,slot)
                    adc_data_q.append(np.int32(aa/256))
                return adc_data_i,adc_data_q
            
            
            
            
            
    def write_dac_data(self,dac_chennel=0,offset=0,data=[],slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
#                    print(self.boardtypeflag)
                    dac_data_addr = np.int64(dac_chennel*0x2000000+offset*4096)
                    lenth = len(data)
                    if lenth==0:
                        return 'ok'
#                        print('no wave write')
                    elif lenth>2048:
                        return 'ok'
#                        print('wave too largh')
                    else:
                        data_i16=np.zeros(2048)
                        data_i16[:lenth] = np.int16(data)
                        data_short = np.int16(data_i16)
                        if not data_short.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_short = np.ascontiguous(data_short, dtype=data_short.dtype)  # 如果不是C连续的内存，必须强制转换
#                        else:
#                            print('addr lianxu')
                        databuf = ctypes.cast(data_short.ctypes.data, ctypes.POINTER(ctypes.c_short))
                            
                        self.fpga_dma_write(board_id,dac_data_addr,databuf)
                        return 'ok'
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
#                    print(self.boardtypeflag)
                    dac_data_addr = np.int64(0x100000000 + dac_chennel*0x2000000+offset*4096)
                    lenth = len(data)
                    if lenth==0:
                        return 'ok'
#                        print('no wave write')
                    elif lenth>2048:
                        return 'ok'
#                        print('wave too largh')
                    else:
                        data_i16=np.zeros(2048)
                        data_i16[:lenth] = np.int16(data)
                        data_short = np.int16(data_i16)
                        if not data_short.flags['C_CONTIGUOUS']:
                            data_short = np.ascontiguous(data_short, dtype=data_short.dtype)  # 如果不是C连续的内存，必须强制转换
                        databuf = ctypes.cast(data_short.ctypes.data, ctypes.POINTER(ctypes.c_short))
                            
                        self.fpga_dma_write(board_id,dac_data_addr,databuf)
                        return 'ok'
    
    def writeWaveform_setting(self,dac_chennel=0,setting={},slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    if dac_chennel > 5 & dac_chennel < 0:
                        print('no dac_chennel')
                    else:
                        dac_data_addr = 0x100000000 + dac_chennel*0x10000000
                        if len(setting)%256 == 0:
                            dma_n = int(len(setting)/256)
                        else:
                            dma_n = int(len(setting)/256)+1
                        
                        for j in range(dma_n):
                            cmd_buf = np.uint16(np.zeros(2048))
                            
                            
                            if j == (dma_n-1):
                                
                                for i in range(len(setting)-j*256):
                                    
                                    param = np.uint16(setting[j*256+i][1])
                                    cmd_buf[i*8] = param
                                    param = np.uint16(setting[j*256+i][2] + setting[j*256+i][3]*2**15)
                                    cmd_buf[i*8+1] = param
                                    param = np.uint16(setting[j*256+i][4]%2**16)
                                    cmd_buf[i*8+2] = param
                                    param = np.uint16(setting[j*256+i][4]/2**16)
                                    cmd_buf[i*8+3] = param
                                    param = np.uint16(setting[j*256+i][5]%2**16)
                                    cmd_buf[i*8+4] = param
                                    param = np.uint16(setting[j*256+i][5]/2**16)
                                    cmd_buf[i*8+5] = param
                                    param = np.uint16(setting[j*256+i][6]%2**16)
                                    cmd_buf[i*8+6] = param
                                    param = np.uint16(setting[j*256+i][6]/2**16)
                                    cmd_buf[i*8+7] = param
                                    
    #                                param1=int(dev.data16_32(np.int32(setting[j*256+i]['replay_len']),np.int32(setting[j*256+i]['signal_num'] + setting[j*256+i]['next_wave_en']*2**15)))
    #                                param2=int(setting[j*256+i]['first_delay'])
    #                                param3=int(setting[j*256+i]['data_delay'])
    #                                param4=int(setting[j*256+i]['dac_palyback_cnt'])
    #                                cmd_buf[i*4] = param1
    #                                cmd_buf[i*4+1] = param2
    #                                cmd_buf[i*4+2] = param3
    #                                cmd_buf[i*4+3] = param4
                            else:
                                for i in range(256):
                                    
                                    param = np.uint16(setting[j*256+i][1])
                                    cmd_buf[i*8] = param
                                    param = np.uint16(setting[j*256+i][2] + setting[j*256+i][3]*2**15)
                                    cmd_buf[i*8+1] = param
                                    param = np.uint16(setting[j*256+i][4]%2**16)
                                    cmd_buf[i*8+2] = param
                                    param = np.uint16(setting[j*256+i][4]/2**16)
                                    cmd_buf[i*8+3] = param
                                    param = np.uint16(setting[j*256+i][5]%2**16)
                                    cmd_buf[i*8+4] = param
                                    param = np.uint16(setting[j*256+i][5]/2**16)
                                    cmd_buf[i*8+5] = param
                                    param = np.uint16(setting[j*256+i][6]%2**16)
                                    cmd_buf[i*8+6] = param
                                    param = np.uint16(setting[j*256+i][6]/2**16)
                                    cmd_buf[i*8+7] = param
                                    
    #                                param1=int(dev.data16_32(np.int32(setting[j*256+i]['replay_len']),np.int32(setting[j*256+i]['signal_num'] + setting[j*256+i]['next_wave_en']*2**15)))
    #                                param2=int(setting[j*256+i]['first_delay'])
    #                                param3=int(setting[j*256+i]['data_delay'])
    #                                param4=int(setting[j*256+i]['dac_palyback_cnt'])
    #                                cmd_buf[i*4] = param1
    #                                cmd_buf[i*4+1] = param2
    #                                cmd_buf[i*4+2] = param3
    #                                cmd_buf[i*4+3] = param4
                            
                            
                            if not cmd_buf.flags['C_CONTIGUOUS']:
                                print('addr not lianxu')
                                cmd_buf = np.ascontiguous(cmd_buf, dtype=cmd_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                            cmd_buf = ctypes.cast(cmd_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                            
                            self.fpga_dma_write(board_id,dac_data_addr,cmd_buf)
                            dac_data_addr = dac_data_addr + 4096
                        
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if dac_chennel > 1 & dac_chennel < 0:
                        print('no dac_chennel')
                    else:
                        dac_data_addr = 0x100000000 + dac_chennel*0x10000000
                        if len(setting)%256 == 0:
                            dma_n = int(len(setting)/256)
                        else:
                            dma_n = int(len(setting)/256)+1
                        
                        for j in range(dma_n):
                            cmd_buf = np.uint16(np.zeros(2048))
                            
                            
                            if j == (dma_n-1):
                                
                                for i in range(len(setting)-j*256):
                                    
                                    param = np.uint16(setting[j*256+i][1])
                                    cmd_buf[i*8] = param
                                    param = np.uint16(setting[j*256+i][2] + setting[j*256+i][3]*2**15)
                                    cmd_buf[i*8+1] = param
                                    param = np.uint16(setting[j*256+i][4]%2**16)
                                    cmd_buf[i*8+2] = param
                                    param = np.uint16(setting[j*256+i][4]/2**16)
                                    cmd_buf[i*8+3] = param
                                    param = np.uint16(setting[j*256+i][5]%2**16)
                                    cmd_buf[i*8+4] = param
                                    param = np.uint16(setting[j*256+i][5]/2**16)
                                    cmd_buf[i*8+5] = param
                                    param = np.uint16(setting[j*256+i][6]%2**16)
                                    cmd_buf[i*8+6] = param
                                    param = np.uint16(setting[j*256+i][6]/2**16)
                                    cmd_buf[i*8+7] = param
                                    
    #                                param1=int(dev.data16_32(np.int32(setting[j*256+i]['replay_len']),np.int32(setting[j*256+i]['signal_num'] + setting[j*256+i]['next_wave_en']*2**15)))
    #                                param2=int(setting[j*256+i]['first_delay'])
    #                                param3=int(setting[j*256+i]['data_delay'])
    #                                param4=int(setting[j*256+i]['dac_palyback_cnt'])
    #                                cmd_buf[i*4] = param1
    #                                cmd_buf[i*4+1] = param2
    #                                cmd_buf[i*4+2] = param3
    #                                cmd_buf[i*4+3] = param4
                            else:
                                for i in range(256):
                                    
                                    param = np.uint16(setting[j*256+i][1])
                                    cmd_buf[i*8] = param
                                    param = np.uint16(setting[j*256+i][2] + setting[j*256+i][3]*2**15)
                                    cmd_buf[i*8+1] = param
                                    param = np.uint16(setting[j*256+i][4]%2**16)
                                    cmd_buf[i*8+2] = param
                                    param = np.uint16(setting[j*256+i][4]/2**16)
                                    cmd_buf[i*8+3] = param
                                    param = np.uint16(setting[j*256+i][5]%2**16)
                                    cmd_buf[i*8+4] = param
                                    param = np.uint16(setting[j*256+i][5]/2**16)
                                    cmd_buf[i*8+5] = param
                                    param = np.uint16(setting[j*256+i][6]%2**16)
                                    cmd_buf[i*8+6] = param
                                    param = np.uint16(setting[j*256+i][6]/2**16)
                                    cmd_buf[i*8+7] = param
                                    
    #                                param1=int(dev.data16_32(np.int32(setting[j*256+i]['replay_len']),np.int32(setting[j*256+i]['signal_num'] + setting[j*256+i]['next_wave_en']*2**15)))
    #                                param2=int(setting[j*256+i]['first_delay'])
    #                                param3=int(setting[j*256+i]['data_delay'])
    #                                param4=int(setting[j*256+i]['dac_palyback_cnt'])
    #                                cmd_buf[i*4] = param1
    #                                cmd_buf[i*4+1] = param2
    #                                cmd_buf[i*4+2] = param3
    #                                cmd_buf[i*4+3] = param4
                            
                            
                            if not cmd_buf.flags['C_CONTIGUOUS']:
                                print('addr not lianxu')
                                cmd_buf = np.ascontiguous(cmd_buf, dtype=cmd_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                            cmd_buf = ctypes.cast(cmd_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                            
                            self.fpga_dma_write(board_id,dac_data_addr,cmd_buf)
                            dac_data_addr = dac_data_addr + 4096
        return 'ok'

    def dac_data_point_len(self,dac_chennel=0,data_point_len=0,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    if dac_chennel > 5 & dac_chennel < 0:
                        return 'no dac_chennel'
    
                    if data_point_len > 4096:
                        return 'too lang!'
                    else:
                        dac_data_addr = dac_chennel + 0x4009
                        param1 = data_point_len
                        self.writeReg(dac_data_addr,param1,slot)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if dac_chennel > 1 & dac_chennel < 0:
                        return 'no dac_chennel'
                    
                    if data_point_len > 4096:
                        return 'too lang!'
                    else:
                        dac_data_addr = dac_chennel + 0x4009
                        param1 = data_point_len
                        self.writeReg(dac_data_addr,param1,slot)
        return 'ok'
    def wr_dac_data_point(self,dac_chennel=0,data_point={},slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    if dac_chennel > 5 & dac_chennel < 0:
                        return 'no dac_chennel'
                    
                    if len(data_point) > 4096:
                        return 'too lang!'
                    else:
                        dac_data_addr = 0xc0000000 + dac_chennel*0x2000000
                        if len(data_point)%512 == 0:
                            dma_n = int(len(data_point)/512)
                        else:
                            dma_n = int(len(data_point)/512)+1
                        
                        for j in range(dma_n):
                            point_buf = np.uint16(np.zeros(2048))
                            
                            if j == (dma_n-1):
                                
                                for i in range(len(data_point)-j*512):
                                    
                                    data_amp = np.uint32(data_point[j*512+i]['amp']*2**16)
    #                                print(data_amp)
                                    param = np.uint32(data_point[j*512+i]['wave_id'] + data_amp*2**12)
                                    point_buf[i*4] = np.uint16(param & 0xffff)
                                    point_buf[i*4+1] = np.uint16(param>>16)
                                    param = np.uint32(data_point[j*512+i]['repeat_num'])
                                    point_buf[i*4+2] = np.uint16(param & 0xffff)
                                    point_buf[i*4+3] = np.uint16(param>>16)
                            else:
                                for i in range(512):
                                    
                                    data_amp = np.uint32(data_point[j*512+i]['amp']*2**16)
                                    param = np.uint32(data_point[j*512+i]['wave_id'] + data_amp*2**12)
                                    point_buf[i*4] = np.uint16(param & 0xffff)
                                    point_buf[i*4+1] = np.uint16(param>>16)
                                    param = np.uint32(data_point[j*512+i]['repeat_num'])
                                    point_buf[i*4+2] = np.uint16(param & 0xffff)
                                    point_buf[i*4+3] = np.uint16(param>>16)
    
                            if not point_buf.flags['C_CONTIGUOUS']:
                                print('addr not lianxu')
                                point_buf = np.ascontiguous(point_buf, dtype=point_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                            point_buf = ctypes.cast(point_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                            
                            self.fpga_dma_write(board_id,dac_data_addr,point_buf)
                            dac_data_addr = dac_data_addr + 4096
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if dac_chennel > 1 & dac_chennel < 0:
                        return 'no dac_chennel'
                    
                    if len(data_point) > 4096:
                        return 'too lang!'
                    else:
                        dac_data_addr = 0xc0000000 + dac_chennel*0x2000000
                        if len(data_point)%512 == 0:
                            dma_n = int(len(data_point)/512)
                        else:
                            dma_n = int(len(data_point)/512)+1
                        
                        for j in range(dma_n):
                            point_buf = np.uint16(np.zeros(2048))
                            
                            if j == (dma_n-1):
                                
                                for i in range(len(data_point)-j*512):
                                    
                                    data_amp = np.uint32(data_point[j*512+i]['amp']*2**16)
    #                                print(data_amp)
                                    param = np.uint32(data_point[j*512+i]['wave_id'] + data_amp*2**12)
                                    point_buf[i*4] = np.uint16(param & 0xffff)
                                    point_buf[i*4+1] = np.uint16(param>>16)
                                    param = np.uint32(data_point[j*512+i]['repeat_num'])
                                    point_buf[i*4+2] = np.uint16(param & 0xffff)
                                    point_buf[i*4+3] = np.uint16(param>>16)
                            else:
                                for i in range(512):
                                    
                                    data_amp = np.uint32(data_point[j*512+i]['amp']*2**16)
                                    param = np.uint32(data_point[j*512+i]['wave_id'] + data_amp*2**12)
                                    point_buf[i*4] = np.uint16(param & 0xffff)
                                    point_buf[i*4+1] = np.uint16(param>>16)
                                    param = np.uint32(data_point[j*512+i]['repeat_num'])
                                    point_buf[i*4+2] = np.uint16(param & 0xffff)
                                    point_buf[i*4+3] = np.uint16(param>>16)
    
                            if not point_buf.flags['C_CONTIGUOUS']:
                                print('addr not lianxu')
                                point_buf = np.ascontiguous(point_buf, dtype=point_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                            point_buf = ctypes.cast(point_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                            
                            self.fpga_dma_write(board_id,dac_data_addr,point_buf)
                            dac_data_addr = dac_data_addr + 4096
        return 'ok'

    def dma_wr_dac_data(self,dac_chennel=0,dac_data=[],slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                for wave_id in range(len(dac_data)):
    #                for dac_chennel in range(6):
                    dac_data_addr = 0x180000000 + dac_chennel*0x40000000 + wave_id*0x40000
    #                for i in range(len(dac_data)):
                    for j in range(len(dac_data[wave_id])):
                        data_len = len(dac_data[wave_id][j])
                        data_buf = np.uint16(np.zeros(2048))
                        data_buf[:data_len] = np.uint16(dac_data[wave_id][j])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        
                        while 1:
                            dma_write_state = self.fpga_dma_write(board_id,dac_data_addr,data_buf)
                            if dma_write_state == 1:
                                break
                            elif dma_write_state == -1:
                                print('dac write err')
                                break
#                            elif dma_write_state == -2:
#                                print('dac data reload')
                                
                        dac_data_addr = dac_data_addr + 4096
        return 'ok'


    def data_reshape(self,data,data_len_reshape):
        data_len = len(data)
    
        data_len_i = np.ceil(data_len/data_len_reshape).astype(int) * data_len_reshape
    
        data_buf = np.zeros(data_len_i)
        data_buf[:data_len] = data
        data_buf = np.reshape(data_buf,(-1,data_len_reshape))
        return data_buf
    #    data_buf_i = []
    #    if data_len%data_len_reshape == 0:
    #        data_buf_i = list(data_buf[:data_len//data_len_reshape])
    #    else:
    #        data_buf_i = list(data_buf[:data_len//data_len_reshape])
    #        data_buf_i.append(data_buf[data_len//data_len_reshape][:data_len%data_len_reshape])
    #    
    #    return data_buf_i
    
    def analyze_dac_data(self,dac_data,continuous=False):
    
        dac_data_len = len(dac_data)
        
    #    setting_new={'replay_id':0,'replay_len':1,'signal_num':2,'next_wave_en':3,'first_delay':4,'data_delay':5,'dac_palyback_cnt':6}
        setting_block = [0,0,0,1,0,0,1]
        setting_generate = setting_block
        wr_dac_data_buf = []
        wr_dac_data_buf_ii = []
        wr_dac_data_buf_iii = []
        
        setting=[]
        #if dac_data_len == 0:
        #    return setting,wr_dac_data_buf
        #else:
        for i in range(dac_data_len):
            wr_dac_data_buf_iii = []
            if len(dac_data[i]) > 2048*64:
                
                signal_num = 0
                wr_dac_data_buf_i = self.data_reshape(dac_data[i],16)
            #    wr_dac_data_buf.append(wr_dac_data_buf_i)
                marker_data_i = np.any(wr_dac_data_buf_i,axis=1)*1
                setting_generate = copy.deepcopy(setting_block)
                setting_generate[0] = i
                setting_buf=[]
                for j in range(len(marker_data_i)):
                    
                    if marker_data_i[j] == 1:
                        wr_dac_data_buf_ii.append(wr_dac_data_buf_i[j])
                        setting_generate[1] += 16
                        
                        if setting_generate[1] == 2048:
                            setting_buf.append(setting_generate)
                            wr_dac_data_buf_iii.append(np.reshape(wr_dac_data_buf_ii,-1))
                            wr_dac_data_buf_ii = []
                            setting_generate = copy.deepcopy(setting_block)
                            signal_num += 1
                            setting_generate[2] = signal_num
                            setting_generate[0] = i
                        elif j == (len(marker_data_i)-1):
                            setting_buf.append(setting_generate)
                            wr_dac_data_buf_iii.append(np.reshape(wr_dac_data_buf_ii,-1))
                            wr_dac_data_buf_ii = []
                    else:
                        if j == (len(marker_data_i)-1):
                            setting_buf.append(setting_generate)
                            wr_dac_data_buf_iii.append(np.reshape(wr_dac_data_buf_ii,-1))
                            wr_dac_data_buf_ii = []
                        elif setting_generate[1] == 0:
                            setting_generate[4] += 16
                        else:
                            setting_buf.append(setting_generate)
                            wr_dac_data_buf_iii.append(np.reshape(wr_dac_data_buf_ii,-1))
        #                    print(len(wr_dac_data_buf_iii),len(wr_dac_data_buf_ii)*16,setting_generate[1],len(wr_dac_data_buf_iii[len(wr_dac_data_buf_iii)-1]))
                            wr_dac_data_buf_ii = []
                            setting_generate = copy.deepcopy(setting_block)
                            signal_num += 1
                            setting_generate[2] = signal_num
                            setting_generate[0] = i
                            
                    if signal_num >= 64:
                        print('write data too lang!')
                        return setting,wr_dac_data_buf
        
        
                if signal_num >= len(setting_buf):
                    signal_num -= 1
                elif  setting_buf[signal_num][1] == 0:
                    signal_num -= 1
        #            setting_buf[signal_num-1][3] = continuous
        #            setting.append(setting_buf[:signal_num])
        #            
        ##            print(setting_buf,signal_num)
        #        else:
        #            setting_buf[signal_num][3] = continuous
        #            setting.append(setting_buf[:signal_num])
    
                setting_buf[signal_num][3] = 0
                setting.append(setting_buf[:signal_num+1])
                
                wr_dac_data_buf.append(wr_dac_data_buf_iii[:signal_num+1])
        #        wr_dac_data_buf.append(np.reshape(wr_dac_data_buf_ii,(-1)))
            else:
                data_package_cnt = np.ceil(len(dac_data[i])/2048).astype(int)
                data_buf = np.zeros(data_package_cnt*2048)
                data_buf[:len(dac_data[i])] = dac_data[i]
                wr_dac_data_buf_iii = list(np.reshape(data_buf,(data_package_cnt,-1)))
                
                setting_buf=[]
                for j in range(data_package_cnt):
                    setting_generate = copy.deepcopy(setting_block)
                    setting_generate[0] = i
                    if j == data_package_cnt-1:
                        setting_generate[1] = len(dac_data[i])%2048
                        setting_generate[3] = 0
                    else:
                        setting_generate[1] = 2048
                        setting_generate[3] = 1
                    setting_generate[2] = j
                    setting_buf.append(setting_generate)
                
                setting.append(setting_buf)
                
                wr_dac_data_buf.append(wr_dac_data_buf_iii)
                
            
        
        return setting,wr_dac_data_buf

    def ad2da_writeWaveform_setting(self,dac_chennel=0,setting={},resule=0,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if dac_chennel > 1 & dac_chennel < 0:
                        print('no dac_chennel')
                    elif resule > 1 & resule < 0:
                        print('no this resule')
                    else:
                        dac_data_addr = 0x8000 + dac_chennel*0x2000 + resule*0x1000
                        param1=int(self.data16_32(np.int32(setting['replay_len']),np.int32(setting['signal_num'] + setting['next_wave_en']*2**15)))
                        param2=int(setting['first_delay'])
                        param3=int(setting['data_delay'])
                        param4=int(setting['dac_palyback_cnt'])
                        replay_id=setting['replay_id']
                        self.writeReg(dac_data_addr+4*replay_id,param1,slot)
                        self.writeReg(dac_data_addr+4*replay_id+1,param2,slot)
                        self.writeReg(dac_data_addr+4*replay_id+2,param3,slot)
                        self.writeReg(dac_data_addr+4*replay_id+3,param4,slot)
        return 'ok'

    

    def dac_all_set(self,dac_enable=0,cmd_reload=0,dac_cmd_update_done=0,dac_ctl={},slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                
                dac_ctl_cmd = cmd_reload%2
                dac_ctl_cmd = dac_ctl_cmd + dac_ctl['dac_a_rst']*2**1 + dac_ctl['dac_a_replay']*2**2
                dac_ctl_cmd = dac_ctl_cmd + dac_ctl['dac_b_rst']*2**3 + dac_ctl['dac_b_replay']*2**4
                dac_ctl_cmd = dac_ctl_cmd + dac_ctl['dac_c_rst']*2**5 + dac_ctl['dac_c_replay']*2**6
                dac_ctl_cmd = dac_ctl_cmd + dac_ctl['dac_d_rst']*2**7 + dac_ctl['dac_d_replay']*2**8
                dac_ctl_cmd = dac_ctl_cmd + dac_ctl['dac_e_rst']*2**9 + dac_ctl['dac_e_replay']*2**10
                dac_ctl_cmd = dac_ctl_cmd + dac_ctl['dac_f_rst']*2**11 + dac_ctl['dac_f_replay']*2**12
                
                
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    self.writeReg(0x4000,int(dac_enable%2),slot)
                    self.writeReg(0x4001,int(dac_ctl_cmd),slot)
                    self.writeReg(0x4008,int(dac_cmd_update_done%2),slot)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0x4000,int(dac_enable%2),slot)
                    self.writeReg(0x4001,int(dac_ctl_cmd),slot)
                    self.writeReg(0x4008,int(dac_cmd_update_done%2),slot)
        return 'ok'
    

    
    def dac_contrle(self,dac_chennel=0,dac_replay_signal_num=0,chennel_open=1,slot=''):
#        for board_id in range(self.board_number):
#            if slot == self.BoardInfo[str(board_id)][1]:
#                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
##                print(dac_chennel,hex(dac_replay_signal_num))
#                if self.BoardInfo[str(board_id)][0]=='6DA':
#                    dac_data_addr = dac_chennel + 0x4002
#                    param1 = int(dac_replay_signal_num*2)
#                    self.writeReg(dac_data_addr,param1,slot)
#                    time.sleep(0.001)
#                    param1 = int(1 + dac_replay_signal_num*2 + 2**31)
#                    self.writeReg(dac_data_addr,param1,slot)
#                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
#    #                    print(self.boardtypeflag)
        dac_data_addr = dac_chennel + 0x4002
        param1 = int(dac_replay_signal_num*2)
        self.writeReg(dac_data_addr,param1,slot)
        time.sleep(0.001)
        param1 = int(chennel_open + dac_replay_signal_num*2 + chennel_open*2**31)
        self.writeReg(dac_data_addr,param1,slot)
        return 'ok'
    
    def get_adc_data(self,delay,read_data_len,num,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0x400,1,slot)
                    time.sleep(0.001)
                    self.writeReg(0x400,0,slot)
                    
                    self.writeReg(0x402,int(delay),slot)
                    self.writeReg(0x403,int(read_data_len),slot)
                    self.writeReg(0x404,int(num-1),slot)
                    self.writeReg(0x401,0,slot)
                    time.sleep(0.001)
                    self.writeReg(0x401,1,slot)
                    
                    state = self.readReg(0x404,slot)
                    while state == 0:
                        time.sleep(0.001)
                        state = self.readReg(0x404,slot)
                        print('.')
                    
                    adc_data_rd=[]
                    
#                    adc_data_rd = self.fpga_dma_read(board_id,0x200000000,num*read_data_len*4)
                    
                
                
                
                Times2048 = math.ceil(read_data_len/2048)
                adc_data_i=[]
                adc_data_q=[]
                
                self.writeReg(0x22,0x01,slot)# 读取复位
                time.sleep(0.01)
                self.writeReg(0x24,Times2048*2048,slot) #读取长度
                self.writeReg(0x25,num-1,slot)# 读取次数
                self.writeReg(0x22,0x00,slot)
                time.sleep(0.01)
                self.writeReg(0x22,0x02,slot)# 上升沿开始工作
                state=0
                self.writeReg(0x27,0x00,slot)
        #        startT=time.clock()
                while state == 0:
                    time.sleep(0.01)
                    print('duqu zhuangtai：',self.readReg(0x27,slot))
                    state=self.readReg(0x27,slot)%2# 数采完完全写到寄存器中
        
                totaltimes = num
                singletimes = read_data_len // 2048
                read_data_mod = read_data_len % 2048
                cnt_data = 0
                state=ctypes.c_int32(0)
                while totaltimes:
                    if singletimes != 0:
                        for cnt_j in range(singletimes):
                            self.writeReg(0x26,0x200*(cnt_j+cnt_data),slot)
                            self.writeReg(0x22,0x00,slot)
                            self.writeReg(0x22,0x04,slot)
                            
                            for cnt_i in range(1024):
                                aa=self.readReg(0x50000+cnt_i,slot)
                                adc_data_i.append(np.int16(aa%65536)/16)
                                adc_data_i.append(np.int16(aa/65536)/16)
                                aa=self.readReg(0x60000+cnt_i,slot)
                                adc_data_q.append(np.int16(aa%65536)/16)
                                adc_data_q.append(np.int16(aa/65536)/16)
                    
                    cnt_data = cnt_data + singletimes
                    
                    if read_data_mod != 0:
                        
                        self.writeReg(0x26,0x200*cnt_data,slot)
                        self.writeReg(0x22,0x00,slot)
                        self.writeReg(0x22,0x04,slot)
                        
                        for cnt_i in range(read_data_mod//2):
                            aa=self.readReg(0x50000+cnt_i,slot)
                            adc_data_i.append(np.int16(aa%65536)/16)
                            adc_data_i.append(np.int16(aa/65536)/16)
                            aa=self.readReg(0x60000+cnt_i,slot)
                            adc_data_q.append(np.int16(aa%65536)/16)
                            adc_data_q.append(np.int16(aa/65536)/16)
                        if read_data_mod % 2 ==1:
                            aa=self.readReg(0x50000+read_data_mod//2+1,slot)
                            adc_data_i.append(np.int16(aa%65536)/16)
                            aa=self.readReg(0x60000+read_data_mod//2+1,slot)
                            adc_data_q.append(np.int16(aa%65536)/16)
                    cnt_data = cnt_data - singletimes
                    cnt_data = cnt_data + Times2048
                    totaltimes = totaltimes-1
                        
                    
                    
        #        lastT=time.clock()
        #        print('总读取传输时间：',lastT-stopT)
                return adc_data_i,adc_data_q

    def wr_dac_data(self,dac_data=[],slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    dac_chennel_all = 6
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    dac_chennel_all = 2
                else:
                    return 'on dac channel is this board'
                
                setting_wr_save = []
    
                for dac_chennel in range(dac_chennel_all):
                    dac_data_len = len(dac_data[dac_chennel])
                    if dac_data_len == 0:
                        setting_wr_save.append([[]])
                    elif len(dac_data[dac_chennel][0]) == 0:
                        setting_wr_save.append([[]])
                    else:
                        setting_save,data_buf = self.analyze_dac_data(dac_data[dac_chennel],False)
                        if data_buf == []:
                            break
                        else:
                            self.dma_wr_dac_data(dac_chennel,data_buf,slot)
                        
                        setting_wr_save.append(setting_save)
                
                return setting_wr_save

    def wr_dac_data_single_ch(self,dac_data=[],dac_chennel=0,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    dac_chennel_all = 6
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    dac_chennel_all = 2
                else:
                    return 'on dac channel is this board'
                
                if dac_chennel > dac_chennel_all:
                    return 'on dac channel is this board'
                
                dac_data_len = len(dac_data)
                if dac_data_len == 0:
                    setting_wr_save=[[]]
                elif len(dac_data[0]) == 0:
                    setting_wr_save=[[]]
                else:
                    setting_save,data_buf = self.analyze_dac_data(dac_data,False)
                    if data_buf == []:
                        break
                    else:
                        self.dma_wr_dac_data(dac_chennel-1,data_buf,slot)
                    
                    setting_wr_save = setting_save
                
                return setting_wr_save

    def get_dac_all_set(self,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                
#                dac_ctl = {'dac_a_rst':0,'dac_a_replay':1,'dac_b_rst':0,'dac_b_replay':1,'dac_c_rst':0,'dac_c_replay':1,
#                   'dac_d_rst':0,'dac_d_replay':1,'dac_e_rst':0,'dac_e_replay':1,'dac_f_rst':0,'dac_f_replay':1}
                dac_ctl = []
                dac_ctl_cmd = self.readReg(0x4001,slot)
                dac_ctl.append(dac_ctl_cmd>>1 & 1)
                dac_ctl.append(dac_ctl_cmd>>2 & 1)
                dac_ctl.append(dac_ctl_cmd>>3 & 1)
                dac_ctl.append(dac_ctl_cmd>>4 & 1)
                dac_ctl.append(dac_ctl_cmd>>5 & 1)
                dac_ctl.append(dac_ctl_cmd>>6 & 1)
                dac_ctl.append(dac_ctl_cmd>>7 & 1)
                dac_ctl.append(dac_ctl_cmd>>8 & 1)
                dac_ctl.append(dac_ctl_cmd>>9 & 1)
                dac_ctl.append(dac_ctl_cmd>>10 & 1)
                dac_ctl.append(dac_ctl_cmd>>11 & 1)
                dac_ctl.append(dac_ctl_cmd>>12 & 1)
                
        return dac_ctl
    
    def dac_all_set_single_ch(self,dac_enable=0,cmd_reload=0,dac_cmd_update_done=0,dac_ctl=[],slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                
                dac_ctl_cmd = cmd_reload%2
                dac_ctl_cmd = dac_ctl_cmd + (dac_ctl[0] & 1)*2**1 + (dac_ctl[1] & 1)*2**2
                dac_ctl_cmd = dac_ctl_cmd + (dac_ctl[2] & 1)*2**3 + (dac_ctl[3] & 1)*2**4
                dac_ctl_cmd = dac_ctl_cmd + (dac_ctl[4] & 1)*2**5 + (dac_ctl[5] & 1)*2**6
                dac_ctl_cmd = dac_ctl_cmd + (dac_ctl[6] & 1)*2**7 + (dac_ctl[7] & 1)*2**8
                dac_ctl_cmd = dac_ctl_cmd + (dac_ctl[8] & 1)*2**9 + (dac_ctl[9] & 1)*2**10
                dac_ctl_cmd = dac_ctl_cmd + (dac_ctl[10] & 1)*2**11 + (dac_ctl[11] & 1)*2**12
                
                
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    self.writeReg(0x4000,int(dac_enable%2),slot)
                    self.writeReg(0x4001,int(dac_ctl_cmd),slot)
                    self.writeReg(0x4008,int(dac_cmd_update_done%2),slot)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0x4000,int(dac_enable%2),slot)
                    self.writeReg(0x4001,int(dac_ctl_cmd),slot)
                    self.writeReg(0x4008,int(dac_cmd_update_done%2),slot)
        return 'ok'
    
    def dac_contrle_rst(self,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.writeReg(0x4000,0,slot)
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    self.writeReg(0x4001,0,slot)
                    for i in range(6):
                        self.dac_contrle(i,0,0,slot)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0x4001,0,slot)
                    for i in range(6):
                        self.dac_contrle(i,0,0,slot)
        return 'ok'
    

    def wr_dac_setting_single_ch(self,data_point,dac_setting,dac_chennel,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                
                dac_ctl = self.get_dac_all_set(slot)

                dac_update_state = 0
                
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    dac_chennel_all = 6
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    dac_chennel_all = 2
                else:
                    return 'on dac channel is this board'
                    
                if dac_chennel > dac_chennel_all:
                    return 'on dac channel is this board'
                
                
                if data_point == []:
                    dac_ctl[dac_chennel*2-1] = 0
                elif dac_setting[0] == []:
                    dac_ctl[dac_chennel*2-1] = 0
                else:
                    dac_ctl[dac_chennel*2-1] = 1
                
                for i in range(dac_chennel_all):
                    if dac_chennel_all == 6:
                        if dac_ctl[i*2+1] == 1:
                            dac_update_state = dac_update_state + 2**i + (2**i<<6)
                    if dac_chennel_all == 2:
                        if dac_ctl[i*2+1] == 1:
                            dac_update_state = dac_update_state + 2**i + (2**i<<2)
                    
                
                self.dac_all_set_single_ch(1,1,0,dac_ctl,slot)
                time.sleep(0.001)
                self.dac_all_set_single_ch(1,0,0,dac_ctl,slot)
    
                
                setting_bufe_cnt1 = 0
                setting_bufe_i = {}
                
                if (data_point == []) | (dac_setting[0] == []):
                    self.dac_data_point_len(dac_chennel-1,len(data_point),slot)
                    self.wr_dac_data_point(dac_chennel-1,data_point,slot)
                    setting_bufe_i = []
                    setting_bufe = {}
#                        continue
                else:
                    
                    setting_bufe = {}
                    for j in range(len(data_point)):
                        for setting_bufe_cnt in range(len(dac_setting[data_point[j]['wave_id']])):
                            setting_bufe[setting_bufe_cnt1+setting_bufe_cnt] = dac_setting[data_point[j]['wave_id']][setting_bufe_cnt]
                        
                        if data_point[j]['continuous'] == 1:
                            setting_bufe[setting_bufe_cnt1+setting_bufe_cnt][3] = 1
                        else:
                            setting_bufe[setting_bufe_cnt1+setting_bufe_cnt][3] = 0
                        
                        setting_bufe_cnt1 = setting_bufe_cnt1 + len(dac_setting[data_point[j]['wave_id']])
                        
                    self.dac_data_point_len(dac_chennel-1,len(data_point),slot)
                    self.wr_dac_data_point(dac_chennel-1,data_point,slot)
                    self.writeWaveform_setting(dac_chennel-1,setting_bufe,slot)
                    setting_bufe_cnt1 = 0
                    setting_bufe_i = setting_bufe

                if len(setting_bufe_i) == 0:
                    self.dac_contrle(dac_chennel-1,len(setting_bufe_i),0,slot)
                else:
                    self.dac_contrle(dac_chennel-1,len(setting_bufe_i),1,slot)

                
                self.dac_all_set_single_ch(1,0,1,dac_ctl,slot)
                time.sleep(0.001)

                
                self.dac_all_set_single_ch(0,0,1,dac_ctl,slot)
                time.sleep(0.001)
                
                
                if dac_update_state == 0:
                    time.sleep(0.001)
                elif self.BoardInfo[str(board_id)][0]=='6DA':
                    while ((self.readReg(0x4001,slot)>>16) & 0xfff) != dac_update_state:
#                        print(hex((self.readReg(0x4001,slot)>>16) & 0xfff),hex(dac_update_state))
                        time.sleep(0.001)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    while ((self.readReg(0x4001,slot)>>16) & 0xf) != dac_update_state:
#                        print(hex(self.readReg(0x4001,slot)))
                        time.sleep(0.001)
    
                
                return setting_bufe


    def wr_dac_data_fb(self,dac_data={},slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    data_buf = np.uint16(np.zeros(2048))
                    data_len = len(dac_data[0])
                    for wave_id in range(data_len):
                        dac_data_addr = 0x180000000 + wave_id*0x40000 + 62*0x1000
                        data_buf = np.uint16(dac_data[0][wave_id][:2048])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,dac_data_addr,data_buf)
                    
                    data_len = len(dac_data[1])
                    for wave_id in range(data_len):
                        dac_data_addr = 0x180000000 + wave_id*0x40000 + 63*0x1000
                        data_buf = np.uint16(dac_data[1][wave_id][:2048])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,dac_data_addr,data_buf)
                    
                    data_len = len(dac_data[2])
                    for wave_id in range(data_len):
                        dac_data_addr = 0x180000000 + 0x40000000 + wave_id*0x40000 + 62*0x1000
                        data_buf = np.uint16(dac_data[2][wave_id][:2048])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,dac_data_addr,data_buf)
                    
                    data_len = len(dac_data[3])
                    for wave_id in range(data_len):
                        dac_data_addr = 0x180000000 + 0x40000000 + wave_id*0x40000 + 63*0x1000
                        data_buf = np.uint16(dac_data[3][wave_id][:2048])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        self.fpga_dma_write(board_id,dac_data_addr,data_buf)

        return 'ok'


#    def wr_dac_setting(self,data_point,dac_setting,slot=''):
#         for board_id in range(self.board_number):
#             if slot == self.BoardInfo[str(board_id)][1]:
#                 self.boardtypeflag = self.BoardInfo[str(board_id)][0]
#                 if self.BoardInfo[str(board_id)][0]=='6DA':
#                     dac_chennel_all = 6
#                 elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
#                     dac_chennel_all = 2
#                 else:
#                     return 'on dac channel is this board'
#                
#                 dac_ctl = {'dac_a_rst':0,'dac_a_replay':1,'dac_b_rst':0,'dac_b_replay':1,'dac_c_rst':0,'dac_c_replay':1,
#                    'dac_d_rst':0,'dac_d_replay':1,'dac_e_rst':0,'dac_e_replay':1,'dac_f_rst':0,'dac_f_replay':1}
#                
#     #            dac_ctl['dac_a_replay'] = len(data_point[0])
#     #            dac_ctl['dac_b_replay'] = len(data_point[1])
#     #            dac_ctl['dac_c_replay'] = len(data_point[2])
#     #            dac_ctl['dac_d_replay'] = len(data_point[3])
#     #            dac_ctl['dac_e_replay'] = len(data_point[4])
#     #            dac_ctl['dac_f_replay'] = len(data_point[5])
#                
#                 self.dac_all_set(1,1,0,dac_ctl,slot)
# #                time.sleep(0.001)
# #                self.dac_all_set(1,0,0,dac_ctl,slot)
#    
#                
#                 setting_bufe_cnt1 = 0
#                 setting_bufe_i = {}
#                 for dac_chennel in range(dac_chennel_all):
#                     setting_bufe = {}
#                     for j in range(len(data_point[dac_chennel])):
#                         for setting_bufe_cnt in range(len(dac_setting[dac_chennel][data_point[dac_chennel][j]['wave_id']])):
#                             setting_bufe[setting_bufe_cnt1+setting_bufe_cnt] = dac_setting[dac_chennel][data_point[dac_chennel][j]['wave_id']][setting_bufe_cnt]
#                        
#                         if data_point[dac_chennel][j]['continuous'] == 1:
#                             setting_bufe[setting_bufe_cnt1+setting_bufe_cnt][3] = 1
#                        
#                         setting_bufe_cnt1 = setting_bufe_cnt1 + len(dac_setting[dac_chennel][data_point[dac_chennel][j]['wave_id']])
#                     self.dac_data_point_len(dac_chennel,len(data_point[dac_chennel]),slot)
#                     self.wr_dac_data_point(dac_chennel,data_point[dac_chennel],slot)
#                     self.writeWaveform_setting(dac_chennel,setting_bufe,slot)
#                     setting_bufe_cnt1 = 0
#                     setting_bufe_i[dac_chennel] = setting_bufe
#                 for dac_chennel in range(dac_chennel_all):
#                     self.dac_contrle(dac_chennel,len(setting_bufe_i[dac_chennel]),slot)
#                
#                
#                 self.dac_all_set(0,1,0,dac_ctl,slot)
#                
#                 time.sleep(0.001)
# #                self.dac_all_set(1,0,1,dac_ctl,slot)
#                 self.dac_all_set(0,0,0,dac_ctl,slot)
#                
#                
#                 time.sleep(0.001)
#                 self.dac_all_set(0,0,1,dac_ctl,slot)
#                 time.sleep(0.001)
#                
#                 if self.BoardInfo[str(board_id)][0]=='6DA':
#                     while ((self.readReg(0x4001,slot)>>16) & 0xfff) != 0xfff:
#     #                    print(hex((self.readReg(0x4001,slot)>>16) & 0xfff))
#                         time.sleep(0.001)
#                 elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
#                     while ((self.readReg(0x4001,slot)>>16) & 0xf) != 0xf:
# #                        print(hex(self.readReg(0x4001,slot)))
#                         time.sleep(0.001)
#    
#                
#                 return setting_bufe
    def wr_dac_setting(self,data_point,dac_setting,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                
                dac_ctl = {'dac_a_rst':0,'dac_a_replay':1,'dac_b_rst':0,'dac_b_replay':1,'dac_c_rst':0,'dac_c_replay':1,
                   'dac_d_rst':0,'dac_d_replay':1,'dac_e_rst':0,'dac_e_replay':1,'dac_f_rst':0,'dac_f_replay':1}
                
                dac_update_state = 0
                
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    dac_chennel_all = 6
                    if data_point[0] == []:
                        dac_ctl['dac_a_replay'] = 0
                    else:
                        if dac_setting[0][0] == []:
                            dac_ctl['dac_a_replay'] = 0
                        else:
                            dac_ctl['dac_a_replay'] = 1
                            dac_update_state = 1 + (1<<6)
                    if data_point[1] == []:
                        dac_ctl['dac_b_replay'] = 0
                    else:
                        if dac_setting[1][0] == []:
                            dac_ctl['dac_b_replay'] = 0
                        else:
                            dac_ctl['dac_b_replay'] = 1
                            dac_update_state = dac_update_state + 2 + (2<<6)
                    if data_point[2] == []:
                        dac_ctl['dac_c_replay'] = 0
                    else:
                        if dac_setting[2][0] == []:
                            dac_ctl['dac_c_replay'] = 0
                        else:
                            dac_ctl['dac_c_replay'] = 1
                            dac_update_state = dac_update_state + 4 + (4<<6)
                    if data_point[3] == []:
                        dac_ctl['dac_d_replay'] = 0
                    else:
                        if dac_setting[3][0] == []:
                            dac_ctl['dac_d_replay'] = 0
                        else:
                            dac_ctl['dac_d_replay'] = 1
                            dac_update_state = dac_update_state + 8 + (8<<6)
                    if data_point[4] == []:
                        dac_ctl['dac_e_replay'] = 0
                    else:
                        if dac_setting[4][0] == []:
                            dac_ctl['dac_e_replay'] = 0
                        else:
                            dac_ctl['dac_e_replay'] = 1
                            dac_update_state = dac_update_state + 0x10 + (0x10<<6)
                    if data_point[5] == []:
                        dac_ctl['dac_f_replay'] = 0
                    else:
                        if dac_setting[5][0] == []:
                            dac_ctl['dac_f_replay'] = 0
                        else:
                            dac_ctl['dac_f_replay'] = 1
                            dac_update_state = dac_update_state + 0x20 + (0x20<<6)
                    
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    dac_chennel_all = 2
                    if data_point[0] == []:
                        dac_ctl['dac_a_replay'] = 0
                    else:
                        if dac_setting[0][0] == []:
                            dac_ctl['dac_a_replay'] = 0
                        else:
                            dac_ctl['dac_a_replay'] = 1
                            dac_update_state = dac_update_state + 1 + (1<<2)
                    if data_point[1] == []:
                        dac_ctl['dac_b_replay'] = 0
                    else:
                        if dac_setting[1][0] == []:
                            dac_ctl['dac_b_replay'] = 0
                        else:
                            dac_ctl['dac_b_replay'] = 1
                            dac_update_state = dac_update_state + 2 + (2<<2)
                    dac_ctl['dac_c_replay'] = 0
                    dac_ctl['dac_d_replay'] = 0
                    dac_ctl['dac_e_replay'] = 0
                    dac_ctl['dac_f_replay'] = 0
                    
                else:
                    return 'on dac channel is this board'
                

                

                
                
    #            dac_ctl['dac_a_replay'] = len(data_point[0])
    #            dac_ctl['dac_b_replay'] = len(data_point[1])
    #            dac_ctl['dac_c_replay'] = len(data_point[2])
    #            dac_ctl['dac_d_replay'] = len(data_point[3])
    #            dac_ctl['dac_e_replay'] = len(data_point[4])
    #            dac_ctl['dac_f_replay'] = len(data_point[5])
                
                self.dac_all_set(1,1,0,dac_ctl,slot)
                time.sleep(0.001)
                self.dac_all_set(1,0,0,dac_ctl,slot)
    
                
                setting_bufe_cnt1 = 0
                setting_bufe_i = {}
                for dac_chennel in range(dac_chennel_all):
                    if (data_point[dac_chennel] == []) | (dac_setting[dac_chennel][0] == []):
                        self.dac_data_point_len(dac_chennel,len(data_point[dac_chennel]),slot)
                        self.wr_dac_data_point(dac_chennel,data_point[dac_chennel],slot)
                        setting_bufe_i[dac_chennel] = []
                        setting_bufe = {}
#                        continue
                    else:
                        
                        setting_bufe = {}
                        for j in range(len(data_point[dac_chennel])):
                            for setting_bufe_cnt in range(len(dac_setting[dac_chennel][data_point[dac_chennel][j]['wave_id']])):
                                setting_bufe[setting_bufe_cnt1+setting_bufe_cnt] = dac_setting[dac_chennel][data_point[dac_chennel][j]['wave_id']][setting_bufe_cnt]
                            
                            if data_point[dac_chennel][j]['continuous'] == 1:
                                setting_bufe[setting_bufe_cnt1+setting_bufe_cnt][3] = 1
                            else:
                                setting_bufe[setting_bufe_cnt1+setting_bufe_cnt][3] = 0
                            
                            setting_bufe_cnt1 = setting_bufe_cnt1 + len(dac_setting[dac_chennel][data_point[dac_chennel][j]['wave_id']])
                            
                        self.dac_data_point_len(dac_chennel,len(data_point[dac_chennel]),slot)
                        self.wr_dac_data_point(dac_chennel,data_point[dac_chennel],slot)
                        self.writeWaveform_setting(dac_chennel,setting_bufe,slot)
                        setting_bufe_cnt1 = 0
                        setting_bufe_i[dac_chennel] = setting_bufe

                for dac_chennel in range(dac_chennel_all):
                    if len(setting_bufe_i[dac_chennel]) == 0:
                        self.dac_contrle(dac_chennel,len(setting_bufe_i[dac_chennel]),0,slot)
                    else:
                        self.dac_contrle(dac_chennel,len(setting_bufe_i[dac_chennel]),1,slot)

                
                self.dac_all_set(1,0,1,dac_ctl,slot)
                
#                time.sleep(0.001)
#                self.dac_all_set(1,0,1,dac_ctl,slot)
#                self.dac_all_set(0,0,0,dac_ctl,slot)
                time.sleep(0.001)

                
                self.dac_all_set(0,0,1,dac_ctl,slot)
                time.sleep(0.001)
                
                
                if dac_update_state == 0:
                    time.sleep(0.001)
                elif self.BoardInfo[str(board_id)][0]=='6DA':
                    while ((self.readReg(0x4001,slot)>>16) & 0xfff) != dac_update_state:
    #                    print(hex((self.readReg(0x4001,slot)>>16) & 0xfff))
                        time.sleep(0.001)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    while ((self.readReg(0x4001,slot)>>16) & 0xf) != dac_update_state:
#                        print(hex(self.readReg(0x4001,slot)))
                        time.sleep(0.001)
    
                
                return setting_bufe

    def close_dac_board(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='6DA':
                    dac_ctl = {'dac_a_rst':0,'dac_a_replay':1,'dac_b_rst':0,'dac_b_replay':1,'dac_c_rst':0,'dac_c_replay':1,
                               'dac_d_rst':0,'dac_d_replay':1,'dac_e_rst':0,'dac_e_replay':1,'dac_f_rst':0,'dac_f_replay':1}
                    self.dac_all_set(1,1,0,dac_ctl,slot)
                elif self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    dac_ctl = {'dac_a_rst':0,'dac_a_replay':1,'dac_b_rst':0,'dac_b_replay':1,'dac_c_rst':0,'dac_c_replay':1,
                               'dac_d_rst':0,'dac_d_replay':1,'dac_e_rst':0,'dac_e_replay':1,'dac_f_rst':0,'dac_f_replay':1}
                    self.dac_all_set(1,1,0,dac_ctl,slot)
                else:
                    return 'on dac channel is this board'
                
    def open_dac_board(self,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.dac_all_set(0,0,slot)
                    return 'ok'
                elif self.BoardInfo[str(board_id)][0]=='6DA':
                    self.dac_all_set(0,0,slot)
                    return 'ok'
                
                
                
    def rd_adc_data(self,delay,read_data_len,num,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if (read_data_len*num > 1024*1024*1024) | (read_data_len>=2**20):
                        print('读取数据超出地址范围')
                    else:
                        
                        self.writeReg(0x401,0,slot)
                        self.writeReg(0x400,1,slot)
                        time.sleep(0.001)
                        self.writeReg(0x400,0,slot)
                        
                        self.writeReg(0x402,int(delay),slot)
                        self.writeReg(0x403,int(num),slot)
                        if read_data_len%2048 == 0:
                            read_data_len_reg = read_data_len
                        else:
                            read_data_len_reg = int(read_data_len/2048 + 1)*2048
                        self.writeReg(0x404,int(read_data_len_reg),slot)
                        
                        time.sleep(0.001)
                        
                        self.writeReg(0x401,1,slot)
                        
                        state = self.readReg(0x405,slot)
                        while state == 0:
                            time.sleep(0.001)
                            state = self.readReg(0x405,slot)
                        
                        data_buf=[]
                        adc_i_data_out = []
                        adc_q_data_out = []
                        data_buf_0 = []
                        data_buf_1 = []
                        
                        if read_data_len%2048 == 0:
                            read_data_cnt = int(read_data_len/2048)
                        else:
                            read_data_cnt = int(read_data_len/2048 + 1)
                        
                        
                        read_data_cnt = read_data_cnt*num
#                        time0 = time.time()
                       
                        for i in range(read_data_cnt):
                            data_buf,state = self.return_data_by_size(0x200000000+i*8192,1,slot)
                            data_buf_i = ctypes.POINTER(ctypes.c_short)(data_buf)
                            data_buf_0.append(np.array(np.int16(data_buf_i[:4096:2])>>4))
                            data_buf_1.append(np.array(np.int16(data_buf_i[1:4096:2])>>4))
#           
#                        
#                        data_buf,state = self.return_data_by_size(0x200000000,read_data_cnt,slot)
#                        time1 = time.time()
#                        data_buf_i = ctypes.POINTER(ctypes.c_short)(data_buf)
#                        data_buf_0 = np.int16(data_buf_i[:read_data_cnt*4096:2])>>4
#                        data_buf_1 = np.int16(data_buf_i[1:read_data_cnt*4096:2])>>4
#                        time2 = time.time()
#                        
                        data_buf_0 = np.array(data_buf_0)
                        data_buf_1 = np.array(data_buf_1)

                        data_buf_0 = data_buf_0.reshape(num,-1)
                        data_buf_1 = data_buf_1.reshape(num,-1)
                        adc_i_data_out[:] = copy.deepcopy(data_buf_0[:][:read_data_len])
                        adc_q_data_out[:] = copy.deepcopy(data_buf_1[:][:read_data_len])
                        

                        
                        data_buf=[]
                        data_buf_0 = []
                        data_buf_1 = []

                    return adc_i_data_out,adc_q_data_out
                else:
                    print('not adc board')
                    return [],[]
                    
                    
    def rd_adc_sum_data(self,delay,times,adc_data_len,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if times > 2**20-1:
                        print('数据求和次数超出范围')
                    else:
                        
                        self.writeReg(0x801,0,slot)
                        self.writeReg(0x800,1,slot)
                        time.sleep(0.001)
                        self.writeReg(0x800,0,slot)
                        
                        self.writeReg(0x803,int(delay),slot)
                        self.writeReg(0x801,int(times*2+0),slot)
                        time.sleep(0.001)
                        self.writeReg(0x801,int(times*2+1),slot)
                        
                        state = self.readReg(0x802,slot)
                        while state == 0:
                            time.sleep(0.001)
                            state = self.readReg(0x802,slot)
#                            print('.')
                        
                        
                        data_buf=[]
                        adc_i_sum_data=[]
                        adc_q_sum_data=[]
                        
                        data_buf = self.return_sum_data(0x80000000,slot)
                        databuf = ctypes.cast(data_buf, ctypes.POINTER(ctypes.c_int))
                        adc_i_sum_data = np.int32(databuf[:adc_data_len])
#                        for i in range(2048):
#                            adc_i_sum_data.append(np.int32(databuf[i]))
                            
                        data_buf=self.return_sum_data(0x82000000,slot)
                        databuf = ctypes.cast(data_buf, ctypes.POINTER(ctypes.c_int))
                        adc_q_sum_data = np.int32(databuf[:adc_data_len])
#                        for i in range(2048):
#                            adc_q_sum_data.append(np.int32(databuf[i]))
#                        plt.plot(adc_i_sum_data)
#                        plt.plot(adc_q_sum_data)
                        
                    return adc_i_sum_data,adc_q_sum_data
                else:
                    print('not adc board')
                    return {},{}

    def feedback_setting(self,fb_set,slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0x8000,fb_set['dac_fb_en'],slot)
                    self.writeReg(0x8001,fb_set['dac_a_fb_delay0'],slot)
                    self.writeReg(0x8002,fb_set['dac_a_fb_delay1'],slot)
                    self.writeReg(0x8003,fb_set['dac_a_fb_len0'],slot)
                    self.writeReg(0x8004,fb_set['dac_a_fb_len1'],slot)
                    self.writeReg(0x8001,fb_set['dac_b_fb_delay0'],slot)
                    self.writeReg(0x8002,fb_set['dac_b_fb_delay1'],slot)
                    self.writeReg(0x8003,fb_set['dac_b_fb_len0'],slot)
                    self.writeReg(0x8004,fb_set['dac_b_fb_len1'],slot)
                    return 'ok'
                else:
                    print('not adc board')
                    return 'ok'

    def dac_set_offset(self,dac_chennel,offset,slot):
#        step=0.17562499999999998
        step = 32768/6
        offset_i = int(offset*step) + 0x8000
#        offset_i = offset
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if dac_chennel < 2:
                        self.writeReg(0x1a,0x12345678,slot)
                        time.sleep(1)
                        self.writeReg(0x14+dac_chennel,offset_i,slot)
                        time.sleep(1)
                        self.writeReg(0x1a,0x00000000,slot)
                    else:
                        print('dac_chennel err')
                elif self.BoardInfo[str(board_id)][0]=='6DA':
                    if dac_chennel < 6:
                        self.writeReg(0x1a,0x12345678,slot)
                        time.sleep(1)
                        self.writeReg(0x14+dac_chennel,offset_i,slot)
                        time.sleep(1)
                        self.writeReg(0x1a,0x00000000,slot)
                    else:
                        print('dac_chennel err')
                else:
                    print('this board have no dac')

          

    
    def initial_channel(self,channel_num, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    self.trig_disen(slot)
                    self.writeReg(0x6, 0x200012, slot)                ##控制寄存器值：200012为无符号数，200002为有符号数
                    if all_channel == 1:                        ##是否全通道设置
                        self.writeReg(0x5, 0xffffffff, slot)          ##程序支持共32通道，但此版本硬件只支持16通道，对应位操作实际为0x5555aaaa;
                    else:
                        self.writeReg(0x5, 1<<channel_num, slot)      ##写寄存器使能控制，为位操作，上升沿有效
                    self.writeReg(0x5, 0x00000000, slot)          ##写使能清零
        
    ####硬件复位，channel_num，单通道时为对应实际通道号;all_channel为是否硬件复位全部通道
    def reset_channel(self,channel_num, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    if all_channel == 1:
                        self.writeReg(0x3, 0xffffffff, slot)
                    else:
                        self.writeReg(0x3, 1<<channel_num, slot)
                    self.writeReg(0x3, 0x00000000, slot)
        
    ####LDAC值设定，channel_num，单通道时为对应实际通道号，ldac_val_volt：ldac寄存器输入值 直接输入目标电压值 输入范围-10~+10,
    def set_ldac_value(self,channel_num, ldac_val_volt, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    hex_val = int((ldac_val_volt + 10)/20 * 0xfffff)
                    print(hex(hex_val))
                    self.writeReg(0x6,0x100000 + (0x000fffff & hex_val), slot)
                    
                    if all_channel == 1:
                        self.writeReg(0x5,0xffffffff, slot)
                    else:
                        self.writeReg(0x5,1<<channel_num, slot)
                        
                    self.writeReg(0x5,0x00000000, slot)
    
    ####LDAC值输出使能，channel_num，单通道时为对应实际通道号
    def LDAC_load(self,channel_num, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
        
                    if all_channel == 1:
                        self.writeReg(0x2,0xffffffff, slot)
                    else:
                        self.writeReg(0x2,1<<channel_num, slot)
                        
                    self.writeReg(0x2,0x00000000, slot)
    
    ####CLR值设定，channel_num，单通道时为对应实际通道号，clr_val_volt：clr寄存器输入值 直接输入目标电压值 输入范围-10~+10
    def set_clr_value(self,channel_num, clr_val_volt, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    hex_val = int((clr_val_volt + 10)/20 * 0xfffff)
                    print(hex(hex_val))
                    self.writeReg(0x6,0x300000 + (0x000fffff & hex_val), slot)
                    
                    if all_channel == 1:
                        self.writeReg(0x5,0xffffffff, slot)
                    else:
                        self.writeReg(0x5,1<<channel_num, slot)
                        
                    self.writeReg(0x5,0x00000000, slot)
        
    ####CLR寄存器输出触发 channel_num:0-31位对应0-31通道
    def CLR_load(self,channel_num, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    if all_channel == 1:
                        self.writeReg(0x4,0xffffffff, slot)
                    else:
                        self.writeReg(0x4,1<<channel_num, slot)
                    self.writeReg(0x4,0x00000000, slot)    
    
    
    ####
    ####    CHANNEL 输出持续时间与间隔时间计时值寄存器，计数时钟为系统TRIGGER时钟,计数器为32位
    ####    trig_en函数使能时本函数设定延迟时间，输出电平跳变如下
    ####        trigger信号输入，此时为CLR寄存器输出的电平值，持续时间为delay_us
    ####        delay_us结束后，输出LDAC寄存器的电平值，持续时间为last_us
    ####        last_us结束后，输出CLR寄存器的电平值，持续时间直至下次TRIGGER信号输入
    def DC_delay_last(self,delay_us,last_us,channelnum, all_channel, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    self.trig_disen(slot)
                    
                    if delay_us <= 10:
                        delay_us = 10;print('delay_t should be more than 10 us')
                    if last_us <= 10:
                        last_us = 10;print('last_us should be more than 10 us')
                    delay_val = int(delay_us*1000/12.8)
                    last_val=int(last_us*1000/12.8)
                    if all_channel == 1:
                        for i in range(32):
                            self.writeReg(0x14 + i*2,delay_val, slot)
                            self.writeReg(0x14 + i*2 + 1,last_val, slot)
                    else:
                        self.writeReg(0x14 + 2*channelnum, delay_val, slot)
                        self.writeReg(0x14 + 2*channelnum + 1, last_val, slot)
        
    ####系统TRIGGER使能，disen时可用手动触发通道电平输出，en时只可依照TRIGGER信号进行电平切换
    def trig_en(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    self.writeReg(0x9,0x1, slot)
    
    def trig_disen(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    self.writeReg(0x9,0x0, slot)
        
        
    ####读寄存器值
    def get_channel_value(self,channel_num, i, slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='DC':
                    self.trig_disen(slot)
                    self.LDAC_load(channel_num, 0, slot)
                    num_str = str(channel_num)
                    self.writeReg(0x6, 0x900000, slot)
                    self.writeReg(0x5, 1<<channel_num, slot)
                    self.writeReg(0x5, 0x00000000, slot)
                    
                    self.writeReg(0x6, 0xb00000, slot)
                    self.writeReg(0x5, 1<<channel_num, slot)
                    self.writeReg(0x5, 0x00000000, slot)
                    
                    decimal = '{:.'+ str(i) + 'f}'
                    ldac_hex_val = self.readReg(84 + channel_num, slot) & 0x000fffff
                    ldac_reg_volt = decimal.format(ldac_hex_val/0xfffff *20 - 10)    
                    
                    print('CHANNEL ' + num_str +' LDAC output register was set to ' + ldac_reg_volt + ' volt')
                    
                
                    
                    self.writeReg(0x6, 0x800000, slot)
                    self.writeReg(0x5, 2**channel_num, slot)
                    self.writeReg(0x5, 0x00000000, slot)
                    
                    clr_hex_val = self.readReg(84 + channel_num, slot) & 0x000fffff
                    clr_reg_volt = decimal.format(clr_hex_val/0xfffff *20 - 10)    
                    print('CHANNEL ' + num_str +' CLR output register was set to ' + clr_reg_volt + ' volt')
        
    def wr_feed_back_data(self,data={},slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    dac_data_addr = 0xC6000000
                    
                    for j in range(len(data[0])):
                        data_buf = np.uint16(np.zeros(2048))
                        if len(data[0][j]) > 2048:
                            data_buf[:2048] = np.uint16(data[0][j][:2048])
                        else:
                            data_buf[:len(data[0][j])] = np.uint16(data[0][j][:len(data[0][j])])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        
                        self.fpga_dma_write(board_id,dac_data_addr,data_buf)
                        dac_data_addr = dac_data_addr + 4096
                    
                    dac_data_addr = 0xC8000000
                    data_buf = np.uint16(np.zeros(2048))
                    for j in range(len(data[1])):
                        data_buf = np.uint16(np.zeros(2048))
                        if len(data[1][j]) > 2048:
                            data_buf[:2048] = np.uint16(data[1][j][:2048])
                        else:
                            data_buf[:len(data[1][j])] = np.uint16(data[1][j][:len(data[1][j])])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        
                        self.fpga_dma_write(board_id,dac_data_addr,data_buf)
                        dac_data_addr = dac_data_addr + 4096
                        
                    return 'ok'
                else:
                    return 'on dac channel is this board'



            
    

    def feed_back_set(self,feed_back_en,setting={},slot=''):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    baseaddr = 0x8000
                    if feed_back_en == 0:
                        self.writeReg(baseaddr,0,slot)
                    else:
                        
                        self.writeReg(baseaddr,0,slot)
                        for i in range(len(setting[0])):
                            data_buf = np.uint32(np.uint32(setting[0][i]['dac_fb_num0']&0x3f) + (np.uint32(setting[0][i]['dac_fb_len0']&0xfff)<<6) + (np.uint32(setting[0][i]['dac_fb_delay0']&0x3fff)<<18))
                            self.writeReg(0x6000+i*2,int(data_buf),slot)
                            data_buf = np.uint32(np.uint32(setting[0][i]['dac_fb_num1']&0x3f) + (np.uint32(setting[0][i]['dac_fb_len1']&0xfff)<<6) + (np.uint32(setting[0][i]['dac_fb_delay1']&0x3fff)<<18))
                            self.writeReg(0x6000+i*2+1,int(data_buf),slot)
                        for i in range(len(setting[1])):
                            data_buf = np.uint32(np.uint32(setting[1][i]['dac_fb_num0']&0x3f) + (np.uint32(setting[1][i]['dac_fb_len0']&0xfff)<<6) + (np.uint32(setting[1][i]['dac_fb_delay0']&0x3fff)<<18))
                            self.writeReg(0x6400+i*2,int(data_buf),slot)
                            data_buf = np.uint32(np.uint32(setting[1][i]['dac_fb_num1']&0x3f) + (np.uint32(setting[1][i]['dac_fb_len1']&0xfff)<<6) + (np.uint32(setting[1][i]['dac_fb_delay1']&0x3fff)<<18))
                            self.writeReg(0x6400+i*2+1,int(data_buf),slot)
                        
                        dac_setlen = len(setting[0])
                        self.writeReg(baseaddr+1,dac_setlen,slot)
                        dac_setlen = len(setting[1])
                        self.writeReg(baseaddr+2,dac_setlen,slot)
                        self.writeReg(baseaddr,1,slot)
                    return 'ok'
                else:
                    return 'on dac channel is this board' 


    def dac_offset(self,dac_chennel=0,amp_v_in=0,slot=''):
        
        #dac_chennel dac通道a~f分别对应0~5
        #amp_v_in 为设置的offset单位为V
        
        time.sleep(0.002)
        amp_n_mv = 0.000092
        amp_in = amp_v_in/amp_n_mv
        amp = amp_in
        
        self.writeReg(0x32 + dac_chennel,int(amp),slot)
        return 'ok'

    def rd_adc_data_set(self,delay,read_data_len,num,slot=''):
        
        #delay trigger后的采样延时时间
        #read_data_len 每次采样的长度
        #num 采样次数
        
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if (read_data_len*num > 1024*1024*1024) | (read_data_len>=2**20):
                        print('读取数据超出地址范围')
                    else:
                        
                        self.writeReg(0x401,0,slot)
                        self.writeReg(0x400,1,slot)
                        time.sleep(0.001)
                        self.writeReg(0x400,0,slot)
                        
                        self.writeReg(0x402,int(delay),slot)
                        self.writeReg(0x403,int(num),slot)
                        if read_data_len%2048 == 0:
                            read_data_len_reg = read_data_len
                        else:
                            read_data_len_reg = int(read_data_len/2048 + 1)*2048
                        self.writeReg(0x404,int(read_data_len_reg),slot)
                        
                        time.sleep(0.001)
                        
                        self.writeReg(0x401,1,slot)
                        
#                        self.readReg(0x405,slot)
                        
                    return 'ok'

    def rd_adc_data_return(self,read_data_len,num,slot=''):
        
        #read_data_len 每次采样的长度
        #num 采样次数
        #返回值 i路数据，q路数据，状态。其中1路、q路数据为num*read_data_len的数组
        
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    if (read_data_len*num > 1024*1024*1024) | (read_data_len>=2**20):
                        print('读取数据超出地址范围')
                    else:
                        state = self.readReg(0x405,slot)
                        if state == 0:
                            return [],[],False
                            
                        data_buf=[]
                        data_buf_0 = []
                        data_buf_1 = []
                        
                        if read_data_len%2048 == 0:
                            read_data_cnt = int(read_data_len/2048)
                        else:
                            read_data_cnt = int(read_data_len/2048 + 1)
                        
                        
                        read_data_cnt = read_data_cnt*num
#                        time0 = time.time()
                       
                        for i in range(read_data_cnt):
                            data_buf,state = self.return_data_by_size(0x200000000+i*8192,1,slot)
                            data_buf_i = ctypes.POINTER(ctypes.c_short)(data_buf)
                            data_buf_0.append(np.array(np.int16(data_buf_i[:4096:2])>>4))
                            data_buf_1.append(np.array(np.int16(data_buf_i[1:4096:2])>>4))
#           
#                        
#                        data_buf,state = self.return_data_by_size(0x200000000,read_data_cnt,slot)
#                        time1 = time.time()
#                        data_buf_i = ctypes.POINTER(ctypes.c_short)(data_buf)
#                        data_buf_0 = np.int16(data_buf_i[:read_data_cnt*4096:2])>>4
#                        data_buf_1 = np.int16(data_buf_i[1:read_data_cnt*4096:2])>>4
#                        time2 = time.time()
#                        
                        data_buf_0 = np.array(data_buf_0)
                        data_buf_1 = np.array(data_buf_1)

                        data_buf_0 = data_buf_0.reshape(num,-1)
                        data_buf_1 = data_buf_1.reshape(num,-1)
                        
                        data_buf=[]
#                        data_buf_0 = []
#                        data_buf_1 = []

                    return data_buf_0[:,:read_data_len],data_buf_1[:,:read_data_len],True
                else:
                    print('not adc board')
                    return [],[],False
                    

################################marker ctrl##############################
    
    def wr_marker_bufe(self,addr,marker_bufe_write,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    data_len = len(marker_bufe_write)*4
                    addr_i = addr
                    data_buf = np.uint32(np.zeros(1024))
                    for i in range(int(data_len/4096)):
                        data_buf = np.uint32(marker_bufe_write[i*1024:i*1024+1024])
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        
                        self.fpga_dma_write_bysize(board_id,addr_i,data_buf,4096)
                        addr_i += 4096
                
                    data_buf = np.uint32(np.zeros(1024))
                    
                    if data_len%4096 != 0:
                        data_buf = marker_bufe_write[int(data_len/4096)*1024:data_len]
                        if not data_buf.flags['C_CONTIGUOUS']:
                            print('addr not lianxu')
                            data_buf = np.ascontiguous(data_buf, dtype=data_buf.dtype)  # 如果不是C连续的内存，必须强制转换
                        data_buf = ctypes.cast(data_buf.ctypes.data, ctypes.POINTER(ctypes.c_short))
                        
                        self.fpga_dma_write_bysize(board_id,addr_i,data_buf,4096)
    
    
                    return 'ok'
    
    def wr_marker(self,marker_data_in,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    data_mul = []
                    for i in range(32):
                        data_mul.append(2**i)
                    
                    data_mul = np.array(data_mul)
                    
                    marker_setting = {}
                    
                    for i in range(16):
                        data_len = []
                        data_len_div32 = []
                        data_generate = []
                        
                        data_num = len(marker_data_in)
                        
                        for i in range(data_num):
                            data_len.append(np.ceil(len(marker_data_in[i])/128).astype(int))
                            data_len_div32.append(np.ceil(data_len[i]/32).astype(int))
                            
                        
                        marker_data_in_len = np.ceil(max(data_len)/32).astype(int)
                        
                        data_generate = np.zeros((data_num,marker_data_in_len*32))
                        
                        for i in range(data_num):
                            data_generate[i][:data_len[i]] = marker_data_in[i][:-1:128]
                        
                
                        data_generate_i = np.reshape(data_generate,(data_num,marker_data_in_len,32))
                        
                        marker_data = np.zeros((data_num,marker_data_in_len))
                        for i in range(data_num):
                            for j in range(data_len_div32[i]):
                                marker_data[i][j] = np.convolve(data_generate_i[i][j],data_mul,'valid')
                        
                        
                        marker_setting.append(self.wr_marker_single(i,marker_data_in,marker_data,slot))
                    return marker_setting
                else:
                    return 'not Clock'
                
                
    def wr_marker_single(self,marker_chennel,data_len,marker_data,slot):
        marker_setting = {}
        data_bufe_save = []
        marker_setting_parameter = {'marker_save_start_addr':0,'marker_len':0}
        if np.size(data_len) == 0:
            marker_setting = []
        elif np.size(data_len) == 1:
            marker_setting_parameter['marker_len'] = data_len[0]
            marker_setting[0] = marker_setting_parameter
            data_bufe_save.extend(np.uint32(marker_data[0]))
        else:
            for j in range(len(data_len)):
                if j != 0:
                    marker_setting_parameter['marker_save_start_addr'] += len(marker_data[j-1])*4

                marker_setting_parameter['marker_len'] = data_len[j]
                marker_setting[j] = copy.deepcopy(marker_setting_parameter)
                data_bufe_save.extend(np.uint32(marker_data[j]))
        
        if np.size(data_len) != 0:
            self.wr_marker_bufe(0x80000000+marker_chennel*0x8000000,np.array(data_bufe_save),slot)
#            time.sleep(0.0005)
        else:
            print('波形为空')
        
        return marker_setting
    
    
    def wr_marker_singlechennel(self,marker_chennel,marker_data_in,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':

                    data_mul = []
                    for i in range(32):
                        data_mul.append(2**(31-i))
                    
                    data_mul = np.array(data_mul)
                    
                    data_len = []
                    data_len_div32 = []
                    data_generate = []
                    
                    data_num = len(marker_data_in)
                    
                    for i in range(data_num):
                        data_len.append(np.ceil(len(marker_data_in[i])/128).astype(int))
                        data_len_div32.append(np.ceil(data_len[i]/32).astype(int))
                        
                    
                    marker_data_in_len = np.ceil(max(data_len)/32).astype(int)
                    
                    data_generate = np.zeros((data_num,marker_data_in_len*32))
                    
                    for i in range(data_num):
                        data_generate[i][:data_len[i]] = marker_data_in[i][:-1:128]
                    
            
                    data_generate_i = np.reshape(data_generate,(data_num,marker_data_in_len,32))
                    
                    marker_data = np.zeros((data_num,marker_data_in_len))
                    for i in range(data_num):
                        for j in range(data_len_div32[i]):
                            marker_data[i][j] = np.convolve(data_generate_i[i][j],data_mul,'valid')

                    return self.wr_marker_single(marker_chennel,data_len,marker_data,slot)
                else:
                    return 'not Clock'


    
    def wr_marker_single_setting(self,marker_chennel,marker_point,marker_setting,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':

                    marker_ctl = {}
                    marker_block_setting = {'marker_block_en':0,'marker_point_len':1}
#                    reload = 0
                    
                    if np.size(marker_point) == 0:
                        marker_block_setting['marker_block_en'] = 0
                        marker_block_setting['marker_point_len'] = 0
                    else:
                        marker_block_setting['marker_block_en'] = 1
                        marker_block_setting['marker_point_len'] = len(marker_point)
                        
                    marker_ctl = copy.deepcopy(marker_block_setting)
                    
#                    print(len(marker_point))
#                    self.writeReg(0x44000,1,slot)   #marker总使能
#                    time.sleep(0.001)
#                    self.writeReg(0x44000,0,slot)   #marker总使能
#                    time.sleep(0.001)
                    
                    wr_reg = marker_ctl['marker_block_en'] + marker_ctl['marker_point_len']*2
                    self.writeReg(0x44001+marker_chennel,wr_reg,slot)
    
                    for i in range(len(marker_point)):
                        self.writeReg(0x4000*(marker_chennel + 1)+i*4,int(marker_point[i]['marker_trigger_delay']*1e9/51.2),slot)
                        self.writeReg(0x4000*(marker_chennel + 1)+i*4+1,marker_setting[marker_point[i]['marker_num']]['marker_save_start_addr'],slot)
                        self.writeReg(0x4000*(marker_chennel + 1)+i*4+2,int(marker_setting[marker_point[i]['marker_num']]['marker_len']),slot)
                        self.writeReg(0x4000*(marker_chennel + 1)+i*4+3,marker_point[i]['marker_repeat_num'],slot)
                    
                    
                    

#                    while 1 :
#                        self.writeReg(0x44000,2,slot)   #marker总使能
#                        for i in range(10):
#                            if (np.uint32(self.readReg(0x44001 + marker_chennel,slot)) >>31 != 1):
#                                time.sleep(0.01)
#                                reload = 1
#                            else:
#                                reload = 0
#                                break
#                            
#                        if reload == 0:
##                            print('marker',marker_chennel,'load done!')
#                            break
##                        else:
##                            print(marker_chennel,hex(np.uint32(self.readReg(0x44001 + marker_chennel,slot))))
#                        self.writeReg(0x44000,1,slot)   #marker总使能
#                        self.writeReg(0x44000,0,slot)   #marker总使能
#                        time.sleep(0.001)
#                    
                    return 'ok'
    
    def wr_marker_setting(self,marker_point,marker_setting,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    marker_ctl = {}
                    marker_block_setting = {'marker_block_en':0,'marker_point_len':1}
                    
                    dac_update_state = np.zeros(16)
                    
                    for i in range(16):
                        if np.size(marker_point[i]) == 0:
                            marker_block_setting['marker_block_en'] = 0
                            marker_block_setting['marker_point_len'] = 0
                        else:
                            marker_block_setting['marker_block_en'] = 1
                            marker_block_setting['marker_point_len'] = len(marker_point[i])
                            dac_update_state[i] = 1
                            
                        marker_ctl[i] = copy.deepcopy(marker_block_setting)
                    
    
                    self.writeReg(0x44000,1,slot)   #marker总使能
                    time.sleep(0.0001)
                    self.writeReg(0x44000,0,slot)   #marker总使能
                    time.sleep(0.0001)
                    
                    for i in range(16):
                        wr_reg = marker_ctl[i]['marker_block_en'] + marker_ctl[i]['marker_point_len']*2
                        self.writeReg(0x44001+i,wr_reg,slot)
    
                    
                    for j in range(16):
                        for i in range(len(marker_point[j])):
                            self.writeReg(0x4000*(j + 1)+i*4,marker_point[j][i]['marker_trigger_delay'],slot)
                            self.writeReg(0x4000*(j + 1)+i*4+1,marker_setting[j][marker_point[j][i]['marker_num']]['marker_save_start_addr'],slot)
                            self.writeReg(0x4000*(j + 1)+i*4+2,marker_setting[j][marker_point[j][i]['marker_num']]['marker_len'],slot)
                            self.writeReg(0x4000*(j + 1)+i*4+3,marker_point[j][i]['marker_repeat_num'],slot)
                    
                    
                    self.writeReg(0x44000,2,slot)   #marker总使能
    
                    for i in range(16):
                        while (np.uint32(self.readReg(0x44001 + i,slot)) >>31 != dac_update_state[i]):
                            time.sleep(1)
                            print(i,np.uint32(self.readReg(0x44001 + i,slot)))
                    
                    return 'ok'
    
    
    def close_marker_block(self,marker_num,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    reg_value = self.readReg(0x44001 + marker_num,slot)
                    reg_value = reg_value & 0x1ffe
                    self.writeReg(0x44001+marker_num,reg_value,slot)
                    return 'ok'
    
    def close_all_marker(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    self.writeReg(0x44000,1,slot)
                    self.writeReg(0x44000,0,slot)
                    while 1:
                        if self.readReg(0x44011,slot) == 0:
                            break
        return 'ok'
    def open_marker(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    marker_block_en = []
#                    self.writeReg(0x44000,0,slot)
#                    time.sleep(0.001)
                    for i in range(16):
                        marker_block_en.append(self.readReg(0x44001+i,slot)&0x01)
                        # print(marker_block_en)
                    for marker_chennel in range(16):
                        if marker_block_en[marker_chennel] == 1:
                            # print(marker_chennel,marker_block_en[marker_chennel])
                            while 1 :
#                                self.writeReg(0x44000,1,slot)   #marker总使能
#                                time.sleep(0.001)
                                self.writeReg(0x44000,2,slot)   #marker总使能
                                for i in range(1000):
                                    if (np.uint32(self.readReg(0x44001 + marker_chennel,slot)) >>31 != 1):
                                        reload = 1
                                    else:
                                        reload = 0
                                        # print(i)
                                        break
                                        
                                    
                                if reload == 0:
#                                    print('marker',marker_chennel,'load done!')
                                    break
#                                else:
#                                    print(marker_chennel,hex(np.uint32(self.readReg(0x44001 + marker_chennel,slot))))
                                self.writeReg(0x44000,1,slot)   #marker总使能
                                self.writeReg(0x44000,0,slot)   #marker总使能
                                time.sleep(0.001)
                    return 'ok'

    def resync_clk_baord(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    self.writeReg(0x48000,0,slot)
                    
                    self.writeReg(0x48000,1,slot)
                    time.sleep(1)
                    self.writeReg(0x48000,0,slot)
                    while(self.readReg(0x48000+2,slot)==0):
                        time.sleep(0.01)
                    print(self.readReg(0x48000+2,slot))

    def set_clk_baord_trigger_out(self,trigger_out_sel,slot):
        #trigger_out_sel:0trigger;1sysref
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='Clock':
                    self.writeReg(0x48001,trigger_out_sel,slot)
                    
                    
    def resync_adcdac_baord(self,slot):
        for board_id in range(self.board_number):
            if slot == self.BoardInfo[str(board_id)][1]:
                self.boardtypeflag = self.BoardInfo[str(board_id)][0]
                if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                    self.writeReg(0xc000,0,slot)
                    self.writeReg(0xc000+2,0,slot)
                    
                    self.writeReg(0xc000,1,slot)
                    self.writeReg(0xc000+2,1,slot)
                    time.sleep(0.1)
                    self.writeReg(0xc000,0,slot)
                    self.writeReg(0xc000+2,0,slot)
                    
                    
                    
                    while(self.readReg(0xc000+1,slot)==0):
                        time.sleep(0.01)
                    while(self.readReg(0xc000+3,slot)==0):
                        time.sleep(0.01)
                    print(self.readReg(0xc000+1,slot))
                    print(self.readReg(0xc000+3,slot))
                elif self.BoardInfo[str(board_id)][0]=='6DA':
                    self.writeReg(0x8000,0,slot)
                    
                    self.writeReg(0x8000,1,slot)
                    time.sleep(0.1)
                    self.writeReg(0x8000,0,slot)
                    
                    
                    
                    while(self.readReg(0x8000+1,slot)==0):
                        time.sleep(0.01)
                    print(self.readReg(0x8000+1,slot))

    def resync_awg(self):
        self.resync_clk_baord('slot6')
        for board_id in range(self.board_number):
            slot = self.BoardInfo[str(board_id)][1]
            if self.BoardInfo[str(board_id)][0]=='2DA2AD':
                self.writeReg(0xc000,0,slot)
                self.writeReg(0xc000+2,0,slot)
                
                self.writeReg(0xc000,1,slot)
                self.writeReg(0xc000+2,1,slot)
                time.sleep(0.1)
                self.writeReg(0xc000,0,slot)
                self.writeReg(0xc000+2,0,slot)
                
                
                
                while(self.readReg(0xc000+1,slot)==0):
                    time.sleep(0.01)
                while(self.readReg(0xc000+3,slot)==0):
                    time.sleep(0.01)
                print('resync',slot)
            elif self.BoardInfo[str(board_id)][0]=='6DA':
                self.writeReg(0x8000,0,slot)
                
                self.writeReg(0x8000,1,slot)
                time.sleep(0.1)
                self.writeReg(0x8000,0,slot)
                while(self.readReg(0x8000+1,slot)==0):
                    time.sleep(0.01)
                print('resync',slot)
        
        print('resync done!')



#%%:
if __name__=='__main__':
    dev=fpgadev()    
    #%%
