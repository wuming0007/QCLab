 # -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 10:28:36 2021

@author: cl
"""
import _thread

import ctypes
import os
import numpy as np
import time
import copy
import socket

basedir = os.path.abspath(os.path.dirname(__file__))
userDLL_path = basedir+'\\UdpDLL_20210822.dll'


package_len = 700
package_rd_num = 135
global sampling_g
sampling_g = 0

class fpgadev(object):
    _instance=None
    _initflag=False
#    clock_board = []
#    clock_board.append(['192.168.4.40',5001])
##    clock_board.append(['192.168.4.10',5001])
##    clock_board.append(['192.168.4.13',5001])
#    
#    dac_board = []
#    dac_board.append(['192.168.4.44',5001])
#    dac_board.append(['192.168.4.45',5001])
##    dac_board.append(['192.168.4.46',5001])
#    
#    adc_board = []
#    adc_board.append(['192.168.4.12',5001])
##    adc_board.append(['192.168.4.15',5001])
#    dac_chennel = []
#    dac_chennel.append(["192.168.4.41",6000,[]])
#    dac_chennel.append(["192.168.4.41",6100,[]])
#    dac_chennel.append(["192.168.4.41",6200,[]])
#    dac_chennel.append(["192.168.4.41",6300,[]])
#    dac_chennel.append(["192.168.4.42",6000,[]])
#    dac_chennel.append(["192.168.4.42",6100,[]])
#    dac_chennel.append(["192.168.4.42",6200,[]])
#    dac_chennel.append(["192.168.4.42",6300,[]])
##    dac_chennel.append(["192.168.4.43",6000,[]])
##    dac_chennel.append(["192.168.4.43",6100,[]])
##    dac_chennel.append(["192.168.4.43",6200,[]])
##    dac_chennel.append(["192.168.4.43",6300,[]])
#    adc_chennel = []
#    adc_chennel.append(["192.168.4.11",6000,[]])
#    adc_chennel.append(["192.168.4.11",6300,[]])
#    adc_chennel.append(["192.168.4.11",6100,[]])
#    adc_chennel.append(["192.168.4.11",6200,[]])
##    adc_chennel.append(["192.168.4.14",6000,[]])
##    adc_chennel.append(["192.168.4.14",6300,[]])
##    adc_chennel.append(["192.168.4.14",6100,[]])
##    adc_chennel.append(["192.168.4.14",6200,[]])
    clock_board = []
    clock_board.append(['192.168.4.48',5001])
#    clock_board.append(['192.168.4.10',5001])
#    clock_board.append(['192.168.4.13',5001])
    
    dac_board = []
    dac_board.append(['192.168.4.52',5001])
    dac_board.append(['192.168.4.53',5001])
#    dac_board.append(['192.168.4.46',5001])
    
    adc_board = []
#    adc_board.append(['192.168.4.14',5001])
#    adc_board.append(['192.168.4.15',5001])
    dac_chennel = []
    dac_chennel.append(["192.168.4.49",6000,[]])
    dac_chennel.append(["192.168.4.49",6100,[]])
    dac_chennel.append(["192.168.4.49",6200,[]])
    dac_chennel.append(["192.168.4.49",6300,[]])
    dac_chennel.append(["192.168.4.50",6000,[]])
    dac_chennel.append(["192.168.4.50",6100,[]])
    dac_chennel.append(["192.168.4.50",6200,[]])
    dac_chennel.append(["192.168.4.50",6300,[]])
#    dac_chennel.append(["192.168.4.43",6000,[]])
#    dac_chennel.append(["192.168.4.43",6100,[]])
#    dac_chennel.append(["192.168.4.43",6200,[]])
#    dac_chennel.append(["192.168.4.43",6300,[]])
    adc_chennel = []
#    adc_chennel.append(["192.168.4.13",6000,[]])
#    adc_chennel.append(["192.168.4.13",6300,[]])
#    adc_chennel.append(["192.168.4.13",6100,[]])
#    adc_chennel.append(["192.168.4.13",6200,[]])
#    adc_chennel.append(["192.168.4.14",6000,[]])
#    adc_chennel.append(["192.168.4.14",6300,[]])
#    adc_chennel.append(["192.168.4.14",6100,[]])
#    adc_chennel.append(["192.168.4.14",6200,[]])
    
    def __init__(self):   
        print("start\n")
#        self.fpga=fpgadevdll()
        self.dll=ctypes.WinDLL(userDLL_path)
#        bbbb=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,40,41,42,43]
#        
#        length=len(bbbb)
#        print("len： %s" %(length))
#        startAddr=0
#        lostPackAddr=0
#        readCommand=0xFFFF
       # data=np.zeros(sendLength,dtype=np.uint8)
#        data=[]
#        data[0]=np.uint8(readCommand>>8)
#        print("data[0] :%s" %(data[0]))
#        self.analysisSendData(bbbb,length,startAddr,lostPackAddr)      
#        print(d_array_data)          
     

    def udp_write(self,sendBuf,size,socket,ip,port):
        #size = 8192
#        print(size)
        udp_write_i = self.dll.clientSendFunc # 取得函数
        udp_write_i.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_char), ctypes.c_int, ctypes.POINTER(ctypes.c_char), ctypes.c_int]#id,address,data,size
        pstr = ctypes.create_string_buffer(bytes(ip, encoding='utf8'))
        return udp_write_i(socket,pstr,port,sendBuf,size)#返回实际传输字节数

    def udp_read(self,size,socket):#底层返回char*
        socket_read = self.dll.ClientRecvFunc 
        socket_read.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_ubyte),ctypes.c_int]
        recv_data = (ctypes.c_ubyte *size)()
        
        recv_len = socket_read(socket,recv_data,size)
        return recv_data,recv_len

    
#    def socket_connect(self,ip,port):
    def socket_connect(self):
        socket_connect_i = self.dll.clientConnect 
#        socket_connect_i.argtypes = [ctypes.POINTER(ctypes.c_char)]
#        pstr = ctypes.create_string_buffer(bytes( encoding='utf8'))
        return socket_connect_i()
    
    

    
    def udp_send_data(self,slot_dac,package_z,package_num,start_addr,send_data):
        
        sendBuf = []
        send_len = len(send_data)*2 + 8
        start_addr_320bit = np.uint32(start_addr//20)
        start_addr_sub = np.uint8(start_addr%20)
        
        sendBuf.append((package_num<<8) + package_z)
        sendBuf.append(start_addr_320bit & 0xffff)
        sendBuf.append(start_addr_320bit>>16 & 0xffff)
        sendBuf.append(start_addr_sub & 0xff)
        sendBuf.extend(send_data)
        sendBuf = np.array(np.int16(sendBuf))
        
        pbuf = ctypes.create_string_buffer(send_len)
        pbuf.raw = sendBuf
    #    print(sendBuf,send_len,type(sendBuf[0]))
        sendBuf_o = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_char))
    
        self.udp_write(sendBuf_o,send_len,int(slot_dac[2]),slot_dac[0],int(slot_dac[1]))
        return 'ok'
    
    def udp_wr_reg(self,slot_dac,package_num,reg_addr,reg_data):
        sendBuf = []
        send_len = 22
        sendBuf.append((package_num<<8) + 0xfe)
        sendBuf.append(reg_addr)
        sendBuf.append(reg_addr>>16)
        sendBuf.extend(reg_data)
        sendBuf = np.array(np.uint16(sendBuf))
        
        pbuf = ctypes.create_string_buffer(send_len)
        pbuf.raw = sendBuf
        sendBuf_o = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_char))
    
        self.udp_write(sendBuf_o,send_len,int(slot_dac[2]),slot_dac[0],int(slot_dac[1]))
        
        return 'ok'
    
    def udp_rd_reg(self,slot_dac,package_num,reg_addr):
        sendBuf = []
        send_len = 6
        sendBuf.append((package_num<<8) + 0xfd)
        sendBuf.append(reg_addr)
        sendBuf.append(reg_addr>>16)
        sendBuf = np.array(np.uint16(sendBuf))
        
        pbuf = ctypes.create_string_buffer(send_len)
        pbuf.raw = sendBuf
        sendBuf_o = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_char))
    
        self.udp_write(sendBuf_o,send_len,int(slot_dac[2]),slot_dac[0],int(slot_dac[1]))
        
        return 'ok'
    
    def udp_rd_data(self,slot_dac,package_num,start_addr,read_data_len):
        sendBuf = []
        send_len = 10
        start_addr_320bit = np.uint32(start_addr//20)
        start_addr_sub = np.uint8(start_addr%20)
    
        read_data_len_320bit = np.uint16((read_data_len+start_addr_sub)//20)
        read_data_len_sub = np.uint8((read_data_len+start_addr_sub)%20)
        
        
        sendBuf.append((package_num<<8) + 0xff)
        sendBuf.append(start_addr_320bit)
        sendBuf.append(start_addr_320bit>>16)
        sendBuf.append((read_data_len_320bit<<8) + start_addr_sub)
        sendBuf.append((read_data_len_sub<<8) + (read_data_len_320bit>>8))
        sendBuf = np.array(np.uint16(sendBuf))
        pbuf = ctypes.create_string_buffer(send_len)
        pbuf.raw = sendBuf
        sendBuf_o = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_char))
    
        self.udp_write(sendBuf_o,send_len,int(slot_dac[2]),slot_dac[0],int(slot_dac[1]))
        
        return 'ok'
    
    def udp_recv(self,slot_dac,size):
        return self.udp_read(size,int(slot_dac[2]))
    
    def data_reshape(self,data,data_len_reshape):
        data_len = len(data)
    
        data_len_i = np.ceil(data_len/data_len_reshape).astype(int) * data_len_reshape
    
        data_buf = np.zeros(data_len_i)
        data_buf[:data_len] = data
        data_buf = np.reshape(data_buf,(-1,data_len_reshape))
        return data_buf
    
    
    def send_data_to_udp(self,slot_dac,generate_data,start_addr):

        data_len = len(generate_data)
        data_len_sub = data_len%package_len
        data_bufe_g = self.data_reshape(np.int16(generate_data),package_len)
        data_len_zong = len(data_bufe_g)
        package_miss_num_g = np.array(range(0,len(data_bufe_g)))*package_len + start_addr
        
        udp_package_num = np.ceil(data_len_zong/253).astype(int)
        udp_package_num_sub = data_len_zong%253
        
        for send_num in range(udp_package_num):
            
            if send_num == udp_package_num-1:
                data_len_z = udp_package_num_sub
                data_bufe = np.int16(data_bufe_g[send_num*253:send_num*253+udp_package_num_sub])
                package_miss_num = package_miss_num_g[send_num*253:send_num*253+udp_package_num_sub]
            else:
                data_len_z = 253
                data_bufe = np.int16(data_bufe_g[send_num*253:send_num*253+253])
                package_miss_num = package_miss_num_g[send_num*253:send_num*253+253]
                
            
            
            
            while 1:
                wr_pack = len(data_bufe)
                
                if wr_pack == 0:
                    break
#                else:
#                    _thread.start_new_thread(self.udp_recv,(slot_dac,4096,))
                
                for i in range(wr_pack-1):
                    self.udp_send_data(slot_dac,wr_pack-1,i,package_miss_num[i],data_bufe[i])
    #                print('send :',i,package_miss_num[i])
                    
                
            

                while 1:
                    if (wr_pack == data_len_z) & (send_num == udp_package_num-1):
                        if data_len_sub == 0:
                            self.udp_send_data(slot_dac,wr_pack-1,wr_pack-1,package_miss_num[wr_pack-1],data_bufe[wr_pack-1])
                        else:
                            self.udp_send_data(slot_dac,wr_pack-1,wr_pack-1,package_miss_num[wr_pack-1],data_bufe[wr_pack-1][:data_len_sub])
#                        print(1)
                    else:
                        self.udp_send_data(slot_dac,wr_pack-1,wr_pack-1,package_miss_num[wr_pack-1],data_bufe[wr_pack-1])
        #                print(2)
                    
                    udp_data_rx,recv_len = self.udp_recv(slot_dac,4096)
                    if recv_len != -1:
                        data_buf_i = ctypes.POINTER(ctypes.c_uint8)(udp_data_rx)
                        data_rx_bufe = np.array(np.uint8(data_buf_i[:int(recv_len)]))

                        break
                
                if recv_len == 2:
    #                print('udp send done!')
                    break
                else:
                    data_rx_bufe = data_rx_bufe[2:]
                    print('udp package miss:',data_rx_bufe)
                    data_bufe_i = copy.deepcopy(data_bufe)
                    package_miss_num_i = copy.deepcopy(package_miss_num)
                    data_bufe = []
                    package_miss_num = []
                    for i in range(len(data_rx_bufe)):
                        data_bufe.append(data_bufe_i[data_rx_bufe[i]])
                        package_miss_num.append(package_miss_num_i[data_rx_bufe[i]])
        
        return 'ok'
    
    def write_dac_data(self,slot_dac,dac_data):
        
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
            
            self.send_data_to_udp(slot_dac,dac_data_bufe[i],start_addr)
            
        return dac_data_point
            
    
    def read_data_from_udp(self,slot_dac,start_addr,read_data_len):
        addr_list = list(np.array(range(0,np.ceil(read_data_len/package_len).astype(int)))*package_len + start_addr)
        
        read_data_len_list = list(np.uint32(np.ones(int(read_data_len/package_len))*package_len))
        if read_data_len % package_len != 0:
            read_data_len_list.append(read_data_len % package_len)
        rd_data_bufe = []
        package_num = 0
        

        for i in range(len(addr_list)):
            while 1:
                
                self.udp_rd_data(slot_dac,package_num,addr_list[i],read_data_len_list[i])
                udp_data_rx,recv_len = self.udp_recv(slot_dac,4096)
                if recv_len != -1:
                    break
            data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx)
            data_rx_bufe = np.array(np.uint16(data_buf_i[:int(recv_len/2)]))
    #        print('recv package :',hex(data_buf_i[0]>>8),len(addr_list),package_num,read_udp_recv_state)
            package_num += 1
            rd_data_bufe.extend(data_rx_bufe)
            
        return rd_data_bufe
    
    
    
    def read_reg(self,slot_dac,reg_addr):
        
        pack_num = 0

        while 1:
            
            self.udp_rd_reg(slot_dac,pack_num,reg_addr)
            udp_data_rx,recv_len = self.udp_recv(slot_dac,4096)
            if recv_len != -1:
                break
        data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx)
        data_rx_bufe = np.array(np.uint16(data_buf_i[1:int(recv_len/2)]))
        
        return data_rx_bufe
        
    def write_reg(self,slot_dac,reg_addr,reg_data):
        
        pack_num = 0
        
        while 1:
            
            self.udp_wr_reg(slot_dac,pack_num,reg_addr,reg_data)
            udp_data_rx,recv_len = self.udp_recv(slot_dac,4096)
            if recv_len != -1:
                break
    #    data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx)
    #    data_rx_bufe = np.array(np.uint16(data_buf_i[1:int(recv_len/2)]))
        
        return 'ok'
        
    def dac_ch_ctrl(self,slot_dac,dac_reset,dac_en):
        dac_ctrl_reg = []
        dac_ctrl_reg.append(np.uint16(dac_en*2 + dac_reset))
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        
        self.write_reg(slot_dac,0,dac_ctrl_reg)
        
        return 'ok'
        
    def dac_data_point(self,slot_dac,data_point):
        
        dac_data_point_bufe = data_point
        
        if np.size(dac_data_point_bufe[0]) == 1:
            dac_data_point_bufe = [dac_data_point_bufe]
    
        for i in range(len(dac_data_point_bufe)):
            reg_addr = 0x10000000+i
            reg_data = []
            reg_data.append(np.uint16(dac_data_point_bufe[i][0]))
            reg_data.append(np.uint16(dac_data_point_bufe[i][0]>>16))
            reg_data.append(np.uint16(dac_data_point_bufe[i][1]))
            reg_data.append(np.uint16(0))
            reg_data.append(np.uint16(dac_data_point_bufe[i][2]))
            reg_data.append(np.uint16(dac_data_point_bufe[i][2]>>16))
            reg_data.append(np.uint16(dac_data_point_bufe[i][3]))
            reg_data.append(np.uint16(0))
        
            self.write_reg(slot_dac,reg_addr,reg_data)
        
        return 'ok'
    
    def dac_replay_point(self,slot_dac,data_point):
        dac_point_bufe = data_point
        if np.size(dac_point_bufe[0]) == 1:
            dac_point_bufe = [dac_point_bufe]
        
        for i in range(len(dac_point_bufe)):
            reg_addr = 0x20000000+i
            reg_data = []
            reg_data.append(np.uint16(dac_point_bufe[i][0]))
            reg_data.append(np.uint16(dac_point_bufe[i][1]))
            reg_data.append(np.uint16(dac_point_bufe[i][2]))
            reg_data.append(np.uint16(dac_point_bufe[i][2]>>16))
            reg_data.append(np.uint16(dac_point_bufe[i][3]))
            reg_data.append(np.uint16(dac_point_bufe[i][3]>>16) + np.uint16(dac_point_bufe[i][4]<<15))
            reg_data.append(0)
            reg_data.append(0)
        
            self.write_reg(slot_dac,reg_addr,reg_data)
    
    
    def dac_trigger_ctrl(self,clk_board,trigger_source,trigger_us,trigger_num,trigger_continue):
        #trigger_source 0 为内部触发，1为外部触发
        #trigger_us 触发周期单位us
        #trigger_num 触发次数，当trigger_continue为1时无效
        #trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        global sampling_g
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_Addr = (clk_board[0],clk_board[1])
        clk_tcp_client_socket.connect(server_Addr)
        
        trigger_times = np.uint32(trigger_num)
        if sampling_g == 0:
            trigger_us_cnt = np.uint32(trigger_us/0.0064)
        else:
            trigger_us_cnt = np.uint32(trigger_us/0.008)
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
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'

    def dac_trigger_close(self):
        #关闭触发
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_Addr = (self.clock_board[0][0],self.clock_board[0][1])
        clk_tcp_client_socket.connect(server_Addr)
        
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x02))
        for i in range(29):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'

    def system_sampling_cmd_send(self,board_id,cmd,sampling):
        #关闭触发
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_Addr = (board_id[0],board_id[1])
        clk_tcp_client_socket.connect(server_Addr)
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(cmd))
        fband_data_buf.append(np.uint8(sampling))
        for i in range(28):
            fband_data_buf.append(np.uint8(0x00))
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'


    def system_sampling(self,sampling):
        #切换采样率 0 为5Gsps；1 为4Gsps
        global sampling_g
        sampling_g = sampling
#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        server_Addr = (self.clock_board[0][0],self.clock_board[0][1])
#        clk_tcp_client_socket.connect(server_Addr)
#        fband_data_buf=[]
#        fband_data_buf.append(np.uint8(0xaa))
#        fband_data_buf.append(np.uint8(0x02))
#        fband_data_buf.append(np.uint8(0x01))
#        fband_data_buf.append(np.uint8(sampling))
#        for i in range(28):
#            fband_data_buf.append(np.uint8(0x00))
#        tcp_buffer = bytes(fband_data_buf)
#        clk_tcp_client_socket.send(tcp_buffer)
        
        self.system_sampling_cmd_send(self.clock_board[0],0x06,sampling)
        time.sleep(2)
        
        self.dac_trigger_ctrl(self.clock_board[0],0,4,10,0)
        
        time.sleep(0.5)
        
        self.system_sampling_cmd_send(self.clock_board[0],0x07,sampling)
        time.sleep(0.5)
        
        self.dac_trigger_ctrl(self.clock_board[0],0,4,10,0)
        
        time.sleep(0.5)
        
        self.system_sampling_cmd_send(self.clock_board[0],0x04,sampling)
        
        for i in range(len(self.clock_board)-1):
        
            self.system_sampling_cmd_send(self.clock_board[i+1],0x03,sampling)
            time.sleep(5)
            
            self.dac_trigger_ctrl(self.clock_board[i],0,4,10,0)
            
            time.sleep(0.5)
           
            self.system_sampling_cmd_send(self.clock_board[i+1],0x07,sampling)
            self.dac_trigger_ctrl(self.clock_board[i+1],1,10,0,0)
            time.sleep(0.5)
            
            self.dac_trigger_ctrl(self.clock_board[i],0,4,10,0)
            
            time.sleep(0.5)
            
            self.system_sampling_cmd_send(self.clock_board[i+1],0x04,sampling)
            
        time.sleep(5)
        
        for i in range(len(self.clock_board)-1):
            self.dac_trigger_ctrl(self.clock_board[i+1],1,10,0,0)

        time.sleep(0.5)
        
        
        for i in range(len(self.dac_board)):
            self.system_sampling_cmd_send(self.dac_board[i],0x01,sampling)

        for i in range(len(self.adc_board)):
            self.system_sampling_cmd_send(self.adc_board[i],0x01,sampling)

      
        
        time.sleep(5)
        
        self.dac_trigger_ctrl(self.clock_board[0],0,4,10,0)
        
        time.sleep(0.5)
        
        for i in range(len(self.dac_board)):
            self.system_sampling_cmd_send(self.dac_board[i],0x02,sampling)

        for i in range(len(self.adc_board)):
            self.system_sampling_cmd_send(self.adc_board[i],0x02,sampling)
            
        time.sleep(0.5)
        
        self.dac_trigger_ctrl(self.clock_board[0],0,4,10,0)
        
#        time.sleep(0.5)
#        
#        for i in range(len(self.dac_board)):
#            self.system_sampling_cmd_send(self.dac_board[i],0x05,sampling)
#
#        for i in range(len(self.adc_board)):
#            self.system_sampling_cmd_send(self.adc_board[i],0x05,sampling)
#            
#        time.sleep(0.5)
#        
#        self.dac_trigger_ctrl(self.clock_board[0],0,1,10,0)
        
        time.sleep(0.5)
        
        for i in range(len(self.dac_board)):
            self.system_sampling_cmd_send(self.dac_board[i],0x03,sampling)
            
        for i in range(len(self.adc_board)):
            self.system_sampling_cmd_send(self.adc_board[i],0x03,sampling)
            
        time.sleep(10)
#        self.dac_trigger_ctrl(self.clock_board[0],0,4,10,0)
#        time.sleep(0.5)

      
        
    def dac_Nyquist_cfg(self,Chennal_num,Nyquist):
        #切换频域
        #Chennal_num 为DAC通道数0~11
        #Nyquist 为DAC工作模式，0 为正常模式；1 为mix模式，适合高频段
        if Chennal_num < 4:
            dac_board_id = self.dac_board[0]
        elif Chennal_num < 8:
            dac_board_id = self.dac_board[1]
        elif Chennal_num < 12:
            dac_board_id = self.dac_board[2]
        
        chennal_id = Chennal_num%4
        
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_Addr = (dac_board_id[0],dac_board_id[1])
        clk_tcp_client_socket.connect(server_Addr)
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x02))
        fband_data_buf.append(np.uint8(0x04))
        fband_data_buf.append(np.uint8(chennal_id))
        fband_data_buf.append(np.uint8(Nyquist))
        for i in range(27):
            fband_data_buf.append(np.uint8(0x00))
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
    
    
    def dac_updata(self,Chennal_num,dac_data):
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 1,dac_en = 0)
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 0,dac_en = 0)
        time.sleep(0.0005)
        dac_data_point_bufe = self.write_dac_data(self.dac_chennel[Chennal_num],dac_data)
        
        self.dac_data_point(self.dac_chennel[Chennal_num],dac_data_point_bufe)
    
    
    def dac_point_updata(self,Chennal_num,data_point):
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 1,dac_en = 0)
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 0,dac_en = 0)
        time.sleep(0.0005)
        self.dac_replay_point(self.dac_chennel[Chennal_num],data_point)
        
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 0,dac_en = 1)

    def dac_ch_close(self,Chennal_num):
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 1,dac_en = 0)
        self.dac_ch_ctrl(slot_dac = self.dac_chennel[Chennal_num],dac_reset = 0,dac_en = 0)
    
    
    
#    def udp_recv_times(self,slot_dac,size,recv_times):
#    
#        recv_len = 0
#        recv_times_cnt = 0
#        udp_rx_data = []
#        udp_rx_data_bufe = []
#        udp_rx_len = []
#        udp_rx_num = []
#        while(recv_times_cnt<recv_times):
#            udp_data_rx_i,recv_len = self.udp_read(size,int(slot_dac[2]))
#            if recv_len != -1:
#                data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx_i)
#                udp_rx_data_bufe.append(np.int16(data_buf_i[0:int(recv_len/2)]))
#    
#    #            print('recv data',recv_times,':',np.int16(data_buf_i[0]>>8))
#                
#                recv_len = -1
#                recv_times_cnt += 1
#            else:
#                break
#    
#        for i in range(len(udp_rx_data_bufe)):
#            udp_rx_len.append(len(udp_rx_data_bufe[i]) - 1)
#            udp_rx_num.append(np.uint16(udp_rx_data_bufe[i][0])>>8)
#            udp_rx_data.append(np.int16(udp_rx_data_bufe[i][1:len(udp_rx_data_bufe[i])]))
#    
#        return udp_rx_num,udp_rx_len,udp_rx_data
    
    def udp_recv_times_8bit(self,slot_dac,size,recv_times):
    
        recv_len = 0
        recv_times_cnt = 0
        udp_rx_data_bufe = []
        while(recv_times_cnt<recv_times):
            udp_data_rx_i,recv_len = self.udp_read(size,int(slot_dac[2]))
            if recv_len != -1:
                data_buf_i = ctypes.POINTER(ctypes.c_uint8)(udp_data_rx_i)
                udp_rx_data_bufe.append(np.uint8(data_buf_i[0:recv_len]))
                
                recv_times_cnt += 1
            else:
                udp_rx_data_bufe.append([])
                break
    
    
        return udp_rx_data_bufe[0]
    
#    def udp_recv_times_64bit(self,slot_dac,size,recv_times):
#    
#        recv_len = 0
#        recv_times_cnt = 0
#        data_longlong = []
#        udp_rx_len = []
#        udp_rx_data = []
#        udp_rx_num = []
#        while(recv_times_cnt<recv_times):
#            udp_data_rx_i,recv_len = self.udp_read(size,int(slot_dac[2]))
##            print(recv_times_cnt,recv_len)
#            if recv_len != -1:
#                data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx_i)
#                data_longlong.append(np.uint16(data_buf_i[:recv_len//2]))
##                udp_rx_num.append(np.uint16(data_buf_i[0])>>8)
##                data_buf_i += 1
##                data_buf_i = ctypes.cast(data_buf_i.ctypes.data, ctypes.POINTER(ctypes.c_longlong))
##                data_longlong.append(np.int64(data_buf_i[:recv_len//8]))
#                
#
#                recv_times_cnt += 1
#            else:
#                break
#        for i in range(len(data_longlong)):
#            udp_rx_len.append(int((len(data_longlong[i])-1)/4))
#            udp_rx_num.append(np.uint16(data_longlong[i][0])>>8)
#            data_buf_ii = np.array(data_longlong[i][1:len(data_longlong[i])])
#            data_buf_ii = ctypes.cast(data_buf_ii.ctypes.data, ctypes.POINTER(ctypes.c_longlong))
#            udp_rx_data.append(np.int64(data_buf_ii[:udp_rx_len[i]]))
#        return udp_rx_num,udp_rx_len,udp_rx_data


    def udp_recv_times(self,slot_dac,size,recv_times):
    
        recv_len = 0
        recv_times_cnt = 0
        udp_rx_data = []
        udp_rx_data_bufe = []
        udp_rx_len = []
        udp_rx_num = []
        while(recv_times_cnt<recv_times):
            udp_data_rx_i,recv_len = self.udp_read(size,int(slot_dac[2]))
            if recv_len != -1:
                data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx_i)
                udp_rx_data_bufe = np.int16(data_buf_i[0:int(recv_len/2)])
                
                udp_rx_len.append(len(udp_rx_data_bufe) - 1)
                udp_rx_num.append(np.uint16(udp_rx_data_bufe[0])>>8)
                udp_rx_data.append(np.int16(udp_rx_data_bufe[1:len(udp_rx_data_bufe)]))
                
                recv_len = -1
                recv_times_cnt += 1
            else:
                break
    
        return udp_rx_num,udp_rx_len,udp_rx_data


    def udp_recv_times_64bit(self,slot_dac,size,recv_times):
    
        recv_len = 0
        recv_times_cnt = 0
        data_longlong = []
        udp_rx_len = []
        udp_rx_data = []
        udp_rx_num = []
        while(recv_times_cnt<recv_times):
            udp_data_rx_i,recv_len = self.udp_read(size,int(slot_dac[2]))

            if recv_len != -1:
                data_buf_i = ctypes.POINTER(ctypes.c_uint16)(udp_data_rx_i)
                data_longlong = np.uint16(data_buf_i[:recv_len//2])
                udp_rx_len.append(int((len(data_longlong)-1)/4))
                udp_rx_num.append(np.uint16(data_longlong[0])>>8)
                data_buf_i = np.array(data_longlong[1:len(data_longlong)])
                data_buf_ii = ctypes.cast(data_buf_i.ctypes.data, ctypes.POINTER(ctypes.c_longlong))
                udp_rx_data.append(copy.deepcopy(np.int64(data_buf_ii[:int((len(data_longlong)-1)/4)])))

                

                recv_times_cnt += 1
            else:
                break

        return udp_rx_num,udp_rx_len,udp_rx_data
    
    
    #        else:
    #            time.sleep(0.0001)
    def udp_rd_data_send_cmd(self,slot_dac,start_addr,read_data_len):
        sendBuf = []
        
        package_num_i = np.ceil(read_data_len/package_len).astype(int)
        send_len = int(package_num_i*10+package_num_i//6*4)
        package_len_i = np.ones(package_num_i)
        package_len_i[0:package_num_i] = 700
    #    if read_data_len%package_len != 0:
    #        package_len_i[package_num_i-1] = read_data_len%package_len
            
        
        start_addr_i = start_addr
        start_addr_bufe = []
        cmd_bufe = []
        for i in range(package_num_i):
            start_addr_bufe.append(start_addr_i)
            
            start_addr_320bit = np.uint32(start_addr_i//20)
            start_addr_sub = np.uint8(start_addr_i%20)
            start_addr_i += package_len_i[i]
            read_data_len_320bit = np.uint16((package_len_i[i]+start_addr_sub)//20)
            read_data_len_sub = np.uint8((package_len_i[i]+start_addr_sub)%20)
            
    
            sendBuf.append((i<<8) + 0xff)
            sendBuf.append(start_addr_320bit)
            sendBuf.append(start_addr_320bit>>16)
            sendBuf.append((read_data_len_320bit<<8) + start_addr_sub)
            sendBuf.append((read_data_len_sub<<8) + (read_data_len_320bit>>8))
    
            if (i+1)%6 == 0:
                sendBuf.append(0)
                sendBuf.append(0)
    
    
        sendBuf = np.array(np.uint16(sendBuf))
        
        pbuf = ctypes.create_string_buffer(send_len)
        pbuf.raw = sendBuf
        sendBuf_o = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_char))
    
        cmd_bufe.append(start_addr_bufe)
        cmd_bufe.append(package_len_i)
    
        self.udp_write(sendBuf_o,send_len,int(slot_dac[2]),slot_dac[0],int(slot_dac[1]))
        return package_num_i,cmd_bufe
    
    
    def udp_rd_adc_data(self,slot_dac,start_addr,read_data_len):
    
        recv_data = np.zeros(read_data_len)
        recv_data_len = 0
        #dev.dac_ch_ctrl(slot_dac = slot_dac,dac_reset = 1,dac_en = 0)
        #dev.dac_ch_ctrl(slot_dac = slot_dac,dac_reset = 0,dac_en = 0)
        start_addr_list = list(np.array(range(0,np.ceil(read_data_len/package_len/package_rd_num).astype(int)))*package_len*package_rd_num + start_addr)
        
        read_data_len_list = list(np.ones(np.ceil(read_data_len/package_len/package_rd_num).astype(int))*package_len*package_rd_num)
        if read_data_len%(package_len*package_rd_num) != 0:
            read_data_len_list[len(read_data_len_list)-1] = read_data_len%(package_len*package_rd_num)
        else:
            read_data_len_list[len(read_data_len_list)-1] = package_len*package_rd_num
        
        recv_data_len = 0
        
        for i in range(len(read_data_len_list)):
    
            miss_cnt_i = 0
            miss_package = []
            cmd_buf_i = []
            
            package_num_i,cmd_buf = self.udp_rd_data_send_cmd(slot_dac,start_addr_list[i],read_data_len_list[i])
            udp_rx_num,udp_rx_len,udp_rx_data = self.udp_recv_times(slot_dac,4096,package_num_i)
        
            recv_data_bufe = [[0]*700]*package_num_i
        
            
            
        
            if package_num_i != len(udp_rx_num):
#                print('package_num_i',package_num_i,'udp_rx_num',len(udp_rx_num))
#                print('udp_rx_num',udp_rx_num)
#                print('cmd_buf',cmd_buf)
                for miss_cnt in range(package_num_i):
                    if miss_cnt_i == len(udp_rx_num):
                        miss_package.append(miss_cnt)
                        cmd_buf_i.append(cmd_buf[0][miss_cnt])
                    elif miss_cnt == udp_rx_num[miss_cnt_i]:
                        recv_data_bufe[miss_cnt] = udp_rx_data[miss_cnt_i]
                        miss_cnt_i += 1
                    else:
                        miss_package.append(miss_cnt)
                        cmd_buf_i.append(cmd_buf[0][miss_cnt])
                        
                
#                print('miss_package',miss_package)
#                print('cmd_buf_i',cmd_buf_i)
                
                miss_cnt = 0
                while 1:
                    package_num_i,cmd_buf = self.udp_rd_data_send_cmd(slot_dac,cmd_buf_i[miss_cnt],700)
                    udp_rx_num,udp_rx_len,udp_rx_data = self.udp_recv_times(slot_dac,4096,package_num_i)
#                    print('udp_rx_len',udp_rx_len,len(udp_rx_len))
                    if udp_rx_len[0] == 700:
#                        print('recv miss package',miss_package[miss_cnt],i)
                        recv_data_bufe[miss_package[miss_cnt]] = udp_rx_data[0]
                        miss_cnt += 1
                        
                    
#                    print('recv',miss_package[miss_cnt])
                    
                    if miss_cnt ==  len(miss_package):
#                        print('recv',i)
                        break
                    
                    
            else:
                recv_data_bufe = udp_rx_data
            
            recv_data_bufe = np.reshape(recv_data_bufe,(1,-1))
                        
            
            recv_data[int(recv_data_len):int(recv_data_len+read_data_len_list[i])] = recv_data_bufe[0][:int(read_data_len_list[i])]
            recv_data_len += read_data_len_list[i]
    
        return list(recv_data)
        
    
    def udp_rd_muldata(self,slot_dac,mul_modle,read_data_len):
        
        start_addr = (0xfec0000 + 0x10000*mul_modle)*20
        recv_data = []
        
        read_data_len = read_data_len*8
        
        recv_data_bufe_i = []
        max_len = 0
        #dev.dac_ch_ctrl(slot_dac = slot_dac,dac_reset = 1,dac_en = 0)
        #dev.dac_ch_ctrl(slot_dac = slot_dac,dac_reset = 0,dac_en = 0)
        start_addr_list = list(np.array(range(0,np.ceil(read_data_len/package_len/package_rd_num).astype(int)))*package_len*package_rd_num + start_addr)
        
        read_data_len_list = list(np.ones(np.ceil(read_data_len/package_len/package_rd_num).astype(int))*package_len*package_rd_num)
        if read_data_len%(package_len*package_rd_num) != 0:
            read_data_len_list[len(read_data_len_list)-1] = read_data_len%(package_len*package_rd_num)
        else:
            read_data_len_list[len(read_data_len_list)-1] = package_len*package_rd_num
        
        
        
        for i in range(len(read_data_len_list)):
    
            miss_cnt_i = 0
            miss_package = []
            cmd_buf_i = []
            
            package_num_i,cmd_buf = self.udp_rd_data_send_cmd(slot_dac,start_addr_list[i],read_data_len_list[i])
            udp_rx_num,udp_rx_len,udp_rx_data = self.udp_recv_times_64bit(slot_dac,4096,package_num_i)
        
            
            
            recv_data_bufe = [[0]*175]*package_num_i
        
            if package_num_i != len(udp_rx_num):
                for miss_cnt in range(package_num_i):
                    if miss_cnt_i == len(udp_rx_num):
                        miss_package.append(miss_cnt)
                        cmd_buf_i.append(cmd_buf[0][miss_cnt])
                    elif miss_cnt == udp_rx_num[miss_cnt_i]:
                        recv_data_bufe[miss_cnt] = udp_rx_data[miss_cnt_i]
                        miss_cnt_i += 1
                    else:
                        miss_package.append(miss_cnt)
                        cmd_buf_i.append(cmd_buf[0][miss_cnt])
                
                miss_cnt = 0
                while 1:
                    package_num_i,cmd_buf = self.udp_rd_data_send_cmd(slot_dac,cmd_buf_i[miss_cnt],700)
                    udp_rx_num,udp_rx_len,udp_rx_data = self.udp_recv_times_64bit(slot_dac,4096,package_num_i)

                    if udp_rx_len[0] == 175:
                        recv_data_bufe[miss_package[miss_cnt]] = udp_rx_data[0]
                        miss_cnt += 1
                        
                    if miss_cnt ==  len(miss_package):
                        break
                    
                    
            else:
                recv_data_bufe = udp_rx_data
            
            
            recv_data_bufe_i.append(np.reshape(recv_data_bufe,-1))
            if i == 0:
                max_len = len(recv_data_bufe_i[0])
    
        recv_data_bufe_ii = [[0]*max_len]*len(recv_data_bufe_i)
        recv_data_bufe_ii[:len(recv_data_bufe_i)-1] = recv_data_bufe_i[:len(recv_data_bufe_i)-1]
        recv_data_bufe_ii[len(recv_data_bufe_i)-1][:len(recv_data_bufe_i[len(recv_data_bufe_i)-1])] = recv_data_bufe_i[len(recv_data_bufe_i)-1]
    
        
        recv_data_bufe_ii = np.reshape(recv_data_bufe_ii,-1)
        recv_data_bufe_o = recv_data_bufe_ii[:read_data_len//4]
        
        recv_data_bufe_o = np.reshape(recv_data_bufe_o,(2,-1),order='F')
        
        recv_data = recv_data_bufe_o[0] + recv_data_bufe_o[1]*1j
        
        return recv_data
            
    
        
    def adc_modle_reset(self,slot_dac,modle_reset):
        #ADC模块总复位
        #slot_dac 为ADC通道数
        #modle_reset 为ADC模块总复位，0 为正常模式；1 为复位
        dac_ctrl_reg = []
        dac_ctrl_reg.append(modle_reset)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(0)
        
        adc_reg_addr = 0x10000000
        
        self.write_reg(slot_dac,adc_reg_addr,dac_ctrl_reg)
        
        return 'ok'
    
    
    def adc_save_ctrl(self,slot_dac,modle_reset,modle_en,trigger_delay,times,save_len):
        dac_ctrl_reg = []
        dac_ctrl_reg.append(np.uint16(modle_en*2 + modle_reset))
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(np.uint16(trigger_delay))
        dac_ctrl_reg.append(np.uint16(trigger_delay>>16))
        dac_ctrl_reg.append(np.uint16(times))
        dac_ctrl_reg.append(np.uint16(times>>16))
        dac_ctrl_reg.append(np.uint16(save_len))
        dac_ctrl_reg.append(np.uint16(save_len>>16))
    
        adc_reg_addr = 0x10000001
        
        self.write_reg(slot_dac,adc_reg_addr,dac_ctrl_reg)
        
        start_addr = 0
        start_addr_sub = 0
        data_len = save_len//20
        data_len_sub = save_len%20
        
        dac_ctrl_reg = []
        dac_ctrl_reg.append(np.uint16(start_addr))
        dac_ctrl_reg.append(np.uint16(start_addr>>16))
        dac_ctrl_reg.append(np.uint16(start_addr_sub))
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(np.uint16(data_len))
        dac_ctrl_reg.append(np.uint16(data_len>>16))
        dac_ctrl_reg.append(np.uint16(data_len_sub))
        dac_ctrl_reg.append(np.uint16(data_len_sub>>16))
        
        adc_reg_addr = 0x10000002
        
        self.write_reg(slot_dac,adc_reg_addr,dac_ctrl_reg)
        
        return 'ok'
    
    def rd_adc_data_ctrl(self,slot_dac,modle_en,trigger_delay,times,save_len):
        #ADC数据存储控制
        #slot_dac 为ADC通道数
        #modle_en 为模块使能，1为使能工作，0为不工作
        #trigger_delay 为解调通道对应数据延时精度为ADC的采样点
        #times 为存储次数，
        #save_len 为存储长度，最大存储深度为5342494720个样点，2.13s
        self.adc_modle_reset(slot_dac,1)
        self.adc_save_ctrl(slot_dac,0,modle_en,trigger_delay,times,save_len)
        self.adc_modle_reset(slot_dac,0)
        
        return 'ok'
    
    def rd_adc_data(self,slot_dac,times,save_len):
        #ADC存储数据读取
        #slot_dac 为ADC通道数
        #times 为读取的解调次数
        #save_len 为每次存储深度
        #返回值为存储数据和数据长度，其中存储未完成数据长度返回-1
        #存储数据格式为二维数据，其中第一维为times，第二维为save_len
        save_state_i = self.read_reg(slot_dac,0x10000001)
#        print(save_state_i)
        if (save_state_i[2]&1) == 0:
            read_data_len = -1
            return [],read_data_len
        else:
            read_data_len = save_len * times
            adc_data = self.udp_rd_adc_data(slot_dac,0,read_data_len)
            
            return np.reshape(adc_data,(-1,save_len)),read_data_len
    
    def adc_mul_ctrl(self,slot_dac,modle_reset,modle_en,modle_num,trigger_delay,times,data_len):
        
        dac_ctrl_reg = []
        dac_ctrl_reg.append(modle_en*2 + modle_reset)
        dac_ctrl_reg.append(0)
        dac_ctrl_reg.append(np.uint16(trigger_delay))
        dac_ctrl_reg.append(np.uint16(trigger_delay>>16))
        dac_ctrl_reg.append(np.uint16(times))
        dac_ctrl_reg.append(np.uint16(times>>16))
        dac_ctrl_reg.append(np.uint16(data_len))
        dac_ctrl_reg.append(np.uint16(data_len>>16))
        
        adc_reg_addr = 0x10000003+modle_num
        
        self.write_reg(slot_dac,adc_reg_addr,dac_ctrl_reg)
        
        return 'ok'
    
    def udp_send_uram_data(self,slot_dac,package_z,package_num,start_addr,send_data):
        
        sendBuf = []
        send_len = len(send_data)*2 + 8
        
        sendBuf.append((package_num<<8) + package_z)
        sendBuf.append(start_addr & 0xffff)
        sendBuf.append(start_addr>>16 & 0xffff)
        sendBuf.append(0)
        sendBuf.extend(send_data)
        sendBuf = np.array(np.int16(sendBuf))
    #    print(sendBuf,send_len,type(sendBuf[0]))
        pbuf = ctypes.create_string_buffer(send_len)
        pbuf.raw = sendBuf
        sendBuf_o = ctypes.cast(ctypes.addressof(pbuf), ctypes.POINTER(ctypes.c_char))
    
        self.udp_write(sendBuf_o,send_len,int(slot_dac[2]),slot_dac[0],int(slot_dac[1]))
        return 'ok'
    
    def adc_uram_wr(self,slot_dac,generate_data,start_addr):
        
        
        package_len_uram = package_len+4
        
        data_len = len(generate_data)
        data_len_sub = data_len%package_len_uram
        data_bufe_g = self.data_reshape(np.int16(generate_data),package_len_uram)
        data_len_zong = len(data_bufe_g)
        
        package_miss_num_g = np.int64(np.array(range(0,len(data_bufe_g)))*package_len_uram/16 + start_addr)
        
        udp_package_num = np.ceil(data_len_zong/253).astype(int)
        udp_package_num_sub = data_len_zong%253
        
        for send_num in range(udp_package_num):
            
            if send_num == udp_package_num-1:
                data_len_z = udp_package_num_sub
                data_bufe = np.int16(data_bufe_g[send_num*253:send_num*253+udp_package_num_sub])
                package_miss_num = package_miss_num_g[send_num*253:send_num*253+udp_package_num_sub]
            else:
                data_len_z = 253
                data_bufe = np.int16(data_bufe_g[send_num*253:send_num*253+253])
                package_miss_num = package_miss_num_g[send_num*253:send_num*253+253]
                
            
    #        print('send :',package_miss_num)
            while 1:
                wr_pack = len(data_bufe)
                
                if wr_pack == 0:
                    break
    #            else:
    #                _thread.start_new_thread(dev.udp_recv,(slot_dac,4096,))
                
                for i in range(wr_pack-1):
                    self.udp_send_uram_data(slot_dac,wr_pack-1,i,package_miss_num[i],data_bufe[i])
                    
                    
                
            
                send_last = 1
                while send_last == 1:
                    if (wr_pack == data_len_z) & (send_num == udp_package_num-1):
                        if data_len_sub == 0:
                            self.udp_send_uram_data(slot_dac,wr_pack-1,wr_pack-1,package_miss_num[wr_pack-1],data_bufe[wr_pack-1])
                        else:
                            self.udp_send_uram_data(slot_dac,wr_pack-1,wr_pack-1,package_miss_num[wr_pack-1],data_bufe[wr_pack-1][:data_len_sub])
    #                        print(1)
                    else:
                        self.udp_send_uram_data(slot_dac,wr_pack-1,wr_pack-1,package_miss_num[wr_pack-1],data_bufe[wr_pack-1])
    #                        print(2)
                    
                    udp_rx_data = self.udp_recv_times_8bit(slot_dac,4096,1)
    
                    if len(udp_rx_data) != 0:
                        send_last = 0
                
                
                if len(udp_rx_data) == 2:
    #                print('udp send done!')
                    break
                else:
                    data_rx_bufe = udp_rx_data[2:]
                    print('udp package miss:',data_rx_bufe)
                    data_bufe_i = copy.deepcopy(data_bufe)
                    package_miss_num_i = copy.deepcopy(package_miss_num)
                    data_bufe = []
                    package_miss_num = []
                    for i in range(len(data_rx_bufe)):
                        data_bufe.append(data_bufe_i[data_rx_bufe[i]])
                        package_miss_num.append(package_miss_num_i[data_rx_bufe[i]])
        
        return 'ok'
    
    def rd_adc_mul_data_ctrl(self,slot_dac,modle_en,modle_num,trigger_delay,times,save_len):
        #ADC解调模块控制
        #slot_dac 为ADC通道数
        #modle_en 为模块使能，1为使能工作，0为不工作
        #modle_num 为解调通道号 0~11总共12路
        #trigger_delay 为解调通道对应数据延时精度为ADC的采样点
        #times 为解调次数，最大为163840
        #save_len 为解调长度最大16384
#        self.adc_modle_reset(slot_dac,1)
        self.adc_mul_ctrl(slot_dac,0,modle_en,modle_num,trigger_delay,times,save_len)
#        self.adc_modle_reset(slot_dac,0)
        
        return 'ok'
       
    def rd_adc_mul_data(self,slot_dac,modle_num,times):
        #ADC解调结果读取
        #slot_dac 为ADC通道数
        #modle_num 为解调模块通道号，0~11
        #times 为读取的解调次数
        #返回值为解调结果数据和数据长度，其中解调未完成数据长度返回-1
        #解调结果数据格式为复数二维数据，其中第一维为times，第二维为复数结果
        save_state_i = self.read_reg(slot_dac,0x10000003+modle_num)
#        print(save_state_i)
        if (save_state_i[2]&1) == 0:
            read_data_len = -1
            return [],read_data_len
        else:
            adc_data = self.udp_rd_muldata(slot_dac,modle_num,times)
            read_data_len = times
            return adc_data,read_data_len
    
    def adc_mul_data_wr(self,slot_dac,modle_num,generate_data):
        #ADC解调模块数据写入，数据为复数，generate_data【0】为实部，generate_data【1】为虚部
        #slot_dac 为ADC通道数
        #modle_num 为解调通道号 0~11总共12路
        #generate_data 为解调通道对应数据
        generate_data = np.reshape(generate_data,(1,-1),order='F')

        start_addr = 0x800*modle_num
        self.adc_uram_wr(slot_dac,generate_data[0],start_addr)
        
        return 'ok'
        
    def setValue(self,dac_data,data_point,ch):
        self.dac_updata(ch,dac_data)
        self.dac_point_updata(ch,data_point)
#        return ch
    
    def get_adc_mul_data(self,adc_chennel,demo_ch_num,trigger_times):
        adc_muldata = []
        for modle_num in demo_ch_num:
            while 1:
                adc_data_bufe,data_len = self.rd_adc_mul_data(adc_chennel,modle_num,trigger_times)
        
                if data_len != -1:
                    break
            adc_muldata.append(adc_data_bufe)

        
        return adc_muldata,adc_chennel
        
    def get_adc_data(self,adc_chennel,trigger_times,save_len):
        
        while 1:
            adc_data_bufe,data_len = self.rd_adc_data(adc_chennel,trigger_times,save_len)
            if data_len != -1:
                break
        return adc_data_bufe,adc_chennel
        
        
    
if __name__=='__main__':
    dev=fpgadev()     