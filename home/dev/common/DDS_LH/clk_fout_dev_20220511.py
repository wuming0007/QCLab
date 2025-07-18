# -*- coding: utf-8 -*-
"""
Created on Wed Apr 20 17:26:14 2022

@author: YH
"""
import ctypes
#import os
import numpy as np
import time
import copy
import socket


def my_tcp_send(ip,port,data):
    clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_Addr = (ip,port)
    clk_tcp_client_socket.connect(server_Addr)
    
    tcp_buffer = bytes(data)
    clk_tcp_client_socket.send(tcp_buffer)
    clk_tcp_client_socket.close()

def my_udp_send(ip,port,data):
    clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_Addr = (ip,port)
    tcp_buffer = bytes(data)
    clk_tcp_client_socket.sendto(tcp_buffer,server_Addr)
    clk_tcp_client_socket.close()


class clk_fout_dev(object):
    
    _instance=None
    _initflag=False
    sampling_g = 2
    dev_id = []
    
    
    
    def __init__(self,dev_ip):
        self.dev_id.append([dev_ip,5001])
    
    def trigger_open(self):
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        clk_board = self.dev_id[0]
        
        server_Addr = (clk_board[0],clk_board[1])
        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(3))
        fband_data_buf.append(np.uint8(0))
        fband_data_buf.append(np.uint8(0))
        fband_data_buf.append(np.uint8(1))
        fband_data_buf.append(np.uint8(1))
        for i in range(26):
            fband_data_buf.append(np.uint8(0x00))
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'
    
    def trigger_close(self):
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        clk_board = self.dev_id[0]
        
        server_Addr = (clk_board[0],clk_board[1])
        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(3))
        fband_data_buf.append(np.uint8(0))
        fband_data_buf.append(np.uint8(0))
        fband_data_buf.append(np.uint8(1))
        for i in range(27):
            fband_data_buf.append(np.uint8(0x00))
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'
    
    def trigger_ctrl(self,trigger_ch,trigger_parameter):
        #trigger_parameter = {'trigger_source':0,'trigger_continue':0,'trigger_times':0,'trigger_us':0,'trigger_delay':0}
        #trigger_source 0 为内部触发，1为外部触发
        #trigger_us 触发周期单位us
        #trigger_num 触发次数，当trigger_continue为1时无效
        #trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        #trigger_delay 触发相对延时单位us
    
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        clk_board = self.dev_id[0]
        
        server_Addr = (clk_board[0],clk_board[1])
        clk_tcp_client_socket.connect(server_Addr)
        
        
        trigger_times = np.uint32(trigger_parameter['trigger_times'])
        if self.sampling_g == 0:
            trigger_f = 0.0064
        elif self.sampling_g == 1:
            trigger_f = 0.008
        elif self.sampling_g == 2:
            trigger_f = 0.8
        
        trigger_us_cnt = np.uint32(round(trigger_parameter['trigger_us']/trigger_f)-1)
        trigger_delay  = np.uint32(round(trigger_parameter['trigger_delay']/trigger_f))
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(3))
        fband_data_buf.append(np.uint8(1))
        fband_data_buf.append(np.uint8(trigger_ch-1))
        fband_data_buf.append(np.uint8(trigger_parameter['trigger_source']))
        fband_data_buf.append(np.uint8(trigger_parameter['trigger_continue']))
        fband_data_buf.append(np.uint8(trigger_parameter['trigger_block_en']))
        fband_data_buf.append(np.uint8(trigger_parameter['trigger_ref']))
        fband_data_buf.append(np.uint8(trigger_times>>24 & 0xff))
        fband_data_buf.append(np.uint8(trigger_times>>16 & 0xff))
        fband_data_buf.append(np.uint8(trigger_times>>8 & 0xff))
        fband_data_buf.append(np.uint8(trigger_times & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt>>24 & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt>>16 & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt>>8 & 0xff))
        fband_data_buf.append(np.uint8(trigger_us_cnt & 0xff))
        fband_data_buf.append(np.uint8(trigger_delay>>24 & 0xff))
        fband_data_buf.append(np.uint8(trigger_delay>>16 & 0xff))
        fband_data_buf.append(np.uint8(trigger_delay>>8 & 0xff))
        fband_data_buf.append(np.uint8(trigger_delay & 0xff))
        for i in range(12):
            fband_data_buf.append(np.uint8(0x00))
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'
    
    def trigger_ch_open(self,trigger_ch):
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        clk_board = self.dev_id[0]
        
        server_Addr = (clk_board[0],clk_board[1])
        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(3))
        fband_data_buf.append(np.uint8(2))
        fband_data_buf.append(np.uint8(trigger_ch-1))
        fband_data_buf.append(np.uint8(1))
        for i in range(27):
            fband_data_buf.append(np.uint8(0x00))
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'

    def trigger_ch_close(self,trigger_ch):
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        clk_board = self.dev_id[0]
        
        server_Addr = (clk_board[0],clk_board[1])
        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(3))
        fband_data_buf.append(np.uint8(2))
        fband_data_buf.append(np.uint8(trigger_ch-1))
        for i in range(28):
            fband_data_buf.append(np.uint8(0x00))
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.send(tcp_buffer)
        
        return 'ok'




    def system_sampling_cmd_send(self,board_id,cmd,sampling):
        #
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
        #切换采样率 0 为5Gsps；1 为4Gsps ; 2 为f_out

        self.sampling_g = sampling
        
        self.system_sampling_cmd_send(self.dev_id[0],0x06,sampling)
        time.sleep(2)
        
        self.system_sampling_cmd_send(self.dev_id[0],0x07,sampling)
        
        time.sleep(0.5)
        
        self.system_sampling_cmd_send(self.dev_id[0],0x04,sampling)
        
        time.sleep(0.5)
        


    def conv_ip(self,ip):
        ip_i = []
        data_buf = 0
        for i in range(len(ip)):
            
            if (ip[i] == '.' ):
                ip_i.append(data_buf)
                data_buf = 0
            elif i+1 == len(ip):
                data_buf = data_buf*10 + int(ip[i])
                ip_i.append(data_buf)
                data_buf = 0
            else:
                data_buf = data_buf*10 + int(ip[i])
        
#        print(ip_i)
        
        return ip_i

    def read_system_ip(self,ip):
        #读取系统板卡类型，ip地址，mac地址等详细信息
        ip_bufe = self.conv_ip(ip)
        ip_i = str(ip_bufe[0])+'.'+str(ip_bufe[1])+'.'+str(ip_bufe[2])+'.'+str(255)
        
        
        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        server_Addr = (ip_i,5001)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xbb))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x01))
        for i in range(29):
            fband_data_buf.append(np.uint8(0x00))
        
        tcp_buffer = bytes(fband_data_buf)
        clk_tcp_client_socket.sendto(tcp_buffer,server_Addr)
        
        data_recv = []
        
        clk_tcp_client_socket.settimeout(1)
        
#        time.sleep(0.1)
        
        while True:
            try:
                data = clk_tcp_client_socket.recv(1024)
            except:
                break
            else:
                data_bufe = []
                for i in range(len(data)):
                    data_bufe.append(np.uint8(data[i]))
                data_recv.append(data_bufe)
        
        clk_tcp_client_socket.close()
        
        
        system_ip = []
        for i in range(len(data_recv)):
            data_recv_i = []
            if data_recv[i][0] == 0x11:
                data_recv_i.append('da')
                data_recv_i.append(str(data_recv[i][1])+'.'+str(data_recv[i][2])+'.'+str(data_recv[i][3])+'.'+str(data_recv[i][4]))
                data_recv_i.append(str(data_recv[i][9])+':'+str(data_recv[i][10])+':'+str(data_recv[i][11])+':'+str(data_recv[i][12])+':'+str(data_recv[i][13])+':'+str(data_recv[i][14]))
                data_recv_i.append(str(data_recv[i][5])+'.'+str(data_recv[i][6])+'.'+str(data_recv[i][7])+'.'+str(data_recv[i][8]))
                data_recv_i.append(str(data_recv[i][15])+':'+str(data_recv[i][16])+':'+str(data_recv[i][17])+':'+str(data_recv[i][18])+':'+str(data_recv[i][19])+':'+str(data_recv[i][20]))
            elif data_recv[i][0] == 0x22:
                data_recv_i.append('ad')
                data_recv_i.append(str(data_recv[i][1])+'.'+str(data_recv[i][2])+'.'+str(data_recv[i][3])+'.'+str(data_recv[i][4]))
                data_recv_i.append(str(data_recv[i][9])+':'+str(data_recv[i][10])+':'+str(data_recv[i][11])+':'+str(data_recv[i][12])+':'+str(data_recv[i][13])+':'+str(data_recv[i][14]))
                data_recv_i.append(str(data_recv[i][5])+'.'+str(data_recv[i][6])+'.'+str(data_recv[i][7])+'.'+str(data_recv[i][8]))
                data_recv_i.append(str(data_recv[i][15])+':'+str(data_recv[i][16])+':'+str(data_recv[i][17])+':'+str(data_recv[i][18])+':'+str(data_recv[i][19])+':'+str(data_recv[i][20]))
            elif data_recv[i][0] == 0x33:
                data_recv_i.append('adda')
                data_recv_i.append(str(data_recv[i][1])+'.'+str(data_recv[i][2])+'.'+str(data_recv[i][3])+'.'+str(data_recv[i][4]))
                data_recv_i.append(str(data_recv[i][9])+':'+str(data_recv[i][10])+':'+str(data_recv[i][11])+':'+str(data_recv[i][12])+':'+str(data_recv[i][13])+':'+str(data_recv[i][14]))
                data_recv_i.append(str(data_recv[i][5])+'.'+str(data_recv[i][6])+'.'+str(data_recv[i][7])+'.'+str(data_recv[i][8]))
                data_recv_i.append(str(data_recv[i][15])+':'+str(data_recv[i][16])+':'+str(data_recv[i][17])+':'+str(data_recv[i][18])+':'+str(data_recv[i][19])+':'+str(data_recv[i][20]))
            elif data_recv[i][0] == 0x00:
                data_recv_i.append('clock')
                data_recv_i.append(str(data_recv[i][1])+'.'+str(data_recv[i][2])+'.'+str(data_recv[i][3])+'.'+str(data_recv[i][4]))
                data_recv_i.append(str(data_recv[i][5])+':'+str(data_recv[i][6])+':'+str(data_recv[i][7])+':'+str(data_recv[i][8])+':'+str(data_recv[i][9])+':'+str(data_recv[i][10]))
            elif data_recv[i][0] == 0x44:
                data_recv_i.append('clk_fout')
                data_recv_i.append(str(data_recv[i][1])+'.'+str(data_recv[i][2])+'.'+str(data_recv[i][3])+'.'+str(data_recv[i][4]))
                data_recv_i.append(str(data_recv[i][5])+':'+str(data_recv[i][6])+':'+str(data_recv[i][7])+':'+str(data_recv[i][8])+':'+str(data_recv[i][9])+':'+str(data_recv[i][10]))
                
            system_ip.append(data_recv_i)
        
        print(system_ip)
        
        return system_ip

    def set_dev_ip(self,old_ip,new_ip):
        new_ip_i = self.conv_ip(new_ip)

#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#        server_Addr = (old_ip,5001)
#        clk_tcp_client_socket.connect(server_Addr)
        
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x01))
        for i in range(3):
            fband_data_buf.append(np.uint8(new_ip_i[i]))
        fband_data_buf.append(np.uint8(new_ip_i[3]))
        for i in range(25):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
#        tcp_buffer = bytes(fband_data_buf)
#        clk_tcp_client_socket.send(tcp_buffer)
        my_tcp_send(old_ip,5001,fband_data_buf)
        
        
#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#        server_Addr = (old_ip,5001)
#        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x03))
        for i in range(3):
            fband_data_buf.append(np.uint8(new_ip_i[i]))
        fband_data_buf.append(np.uint8(1))
        for i in range(25):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
#        tcp_buffer = bytes(fband_data_buf)
#        clk_tcp_client_socket.send(tcp_buffer)
        my_tcp_send(old_ip,5001,fband_data_buf)
        
#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#        server_Addr = (old_ip,5001)
#        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x09))
        for i in range(3):
            fband_data_buf.append(np.uint8(new_ip_i[i]))
        fband_data_buf.append(np.uint8(new_ip_i[3]-1))
        for i in range(25):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
#        tcp_buffer = bytes(fband_data_buf)
#        clk_tcp_client_socket.send(tcp_buffer)
        my_tcp_send(old_ip,5001,fband_data_buf)
            

    def set_dev_mac(self,clk_ip,new_mac):
        new_mac_i = self.conv_ip(new_mac)

#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#        server_Addr = (clk_ip,5001)
#        clk_tcp_client_socket.connect(server_Addr)
        
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x00))
        for i in range(6):
            fband_data_buf.append(np.uint8(new_mac_i[i]))
        for i in range(23):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
#        tcp_buffer = bytes(fband_data_buf)
#        clk_tcp_client_socket.send(tcp_buffer)
        my_tcp_send(clk_ip,5001,fband_data_buf)
        
    def set_init_ip(self,dev_id):
        #恢复ip出厂设置
        ip_bufe = self.conv_ip(dev_id[0])
        ip_i = str(ip_bufe[0])+'.'+str(ip_bufe[1])+'.'+str(ip_bufe[2])+'.'+str(255)
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xbb))
        for i in range(31):
            fband_data_buf.append(np.uint8(0x00))
        
        my_udp_send(ip_i,5001,fband_data_buf)


if __name__=='__main__':
    dev=clk_fout_dev()    
    
    
    
    
    