# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 13:56:18 2021

@author: YH
"""
import numpy as np
import socket
import time

def generate_ip(slot_ip):
    
    slot_id = [[],[],[],[],[]]
    clock_board = []
    slot_board = []
    ad_chennel = []
    da_chennel = []
    for s_num in range(len(slot_ip)):
        ip_i = slot_ip[s_num][0][0:10]
        ip_sub = int(slot_ip[s_num][0][10:12])
        
    
        
        clock_board.append([slot_ip[s_num][0],5001])
        

        board_num = slot_ip[s_num][2]//4
        for i in range(board_num):
            slot_board.append([ip_i+str(ip_sub+2+i*2),5001])
            if slot_ip[s_num][1] == 'ad':
                ad_chennel.append([ip_i+str(ip_sub+1+i*2),6300,0])
                ad_chennel.append([ip_i+str(ip_sub+1+i*2),6000,0])
                ad_chennel.append([ip_i+str(ip_sub+1+i*2),6200,0])
                ad_chennel.append([ip_i+str(ip_sub+1+i*2),6100,0])
            else:
                da_chennel.append([ip_i+str(ip_sub+1+i*2),6000,0])
                da_chennel.append([ip_i+str(ip_sub+1+i*2),6100,0])
                da_chennel.append([ip_i+str(ip_sub+1+i*2),6200,0])
                da_chennel.append([ip_i+str(ip_sub+1+i*2),6300,0])
        
    slot_id[0] = slot_ip
    slot_id[1] = clock_board
    slot_id[2] = slot_board
    slot_id[3] = da_chennel
    slot_id[4] = ad_chennel
    
    return slot_id

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

class devip(object):
    
    dev_id = []
    
    def __init__(self,dev_ip):
        
        self.dev_id = generate_ip(dev_ip)
        self.clock_board = self.dev_id[1]
        self.board = self.dev_id[2]
        self.da = self.dev_id[3]
        self.ad = self.dev_id[4]
    
#    def clock_board(self):
#        return self.dev_id[1]
#    
#    def board(self):
#        return self.dev_id[2]
#    
#    def chennel(self):
#        return self.dev_id[3]
    
    
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
        
        return ip_i
    
    def conv_mac(self,mac):
        mac_i = []
        data_buf = 0
        for i in range(len(mac)):
            
            if (mac[i] == '.' ):
                mac_i.append(data_buf)
                data_buf = 0
            elif i+1 == len(mac):
                data_buf = data_buf*10 + int(mac[i])
                mac_i.append(data_buf)
                data_buf = 0
            else:
                data_buf = data_buf*10 + int(mac[i])
        
        return mac_i
    
    def set_clk_ip(self,old_ip,new_ip):
        new_ip_i = self.conv_ip(new_ip)

#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#        server_Addr = (old_ip,5001)
#        clk_tcp_client_socket.connect(server_Addr)
        
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x01))
        for i in range(4):
            fband_data_buf.append(np.uint8(new_ip_i[i]))
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


    def set_dev_id(self,old_id,new_id):
        for i in range(len(new_id)):
            self.set_clk_ip(old_id[i][0],new_id[i][0])
            
            old_id_bufe = self.conv_ip(old_id[i][0])
            new_id_bufe = self.conv_ip(new_id[i][0])
            baord_num = new_id[0][2]//4
            
            for i in range(baord_num):
                old_id_i = str(old_id_bufe[0])+'.'+str(old_id_bufe[1])+'.'+str(old_id_bufe[2])+'.'+str(old_id_bufe[3]+i*2+2)
                new_id_i = str(new_id_bufe[0])+'.'+str(new_id_bufe[1])+'.'+str(new_id_bufe[2])+'.'+str(new_id_bufe[3]+i*2+2)
    #            print(old_id_i,new_id_i,baord_num)
                self.set_dev_ip(old_id_i,new_id_i)
            

    def set_clk_mac(self,clk_ip,new_mac):
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
        
        
#        clk_tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#        server_Addr = (clk_ip,5001)
#        clk_tcp_client_socket.connect(server_Addr)
        
        fband_data_buf=[]
        fband_data_buf.append(np.uint8(0xaa))
        fband_data_buf.append(np.uint8(0x00))
        fband_data_buf.append(np.uint8(0x0a))
        for i in range(5):
            fband_data_buf.append(np.uint8(new_mac_i[i]))
        fband_data_buf.append(np.uint8(new_mac_i[5]-1))
        for i in range(23):
            fband_data_buf.append(np.uint8(0x00))
        #fband_data_buf = {0x12,0x34,0x56,0x78,0x9a}
        
#        tcp_buffer = bytes(fband_data_buf)
#        clk_tcp_client_socket.send(tcp_buffer) 
        my_tcp_send(clk_ip,5001,fband_data_buf)
        

    def set_system_mac(self,ip,new_mac,ch_num):
        #设置系统mac地址
        self.set_clk_mac(ip,new_mac)
        
        ip_bufe = self.conv_ip(ip)
        new_mac_bufe = self.conv_mac(new_mac)
        baord_num = ch_num//4
        
        for i in range(baord_num):
            new_mac_i = str(new_mac_bufe[0])+'.'+str(new_mac_bufe[1])+'.'+str(new_mac_bufe[2])+'.'+str(new_mac_bufe[3])+'.'+str(new_mac_bufe[4])+'.'+str(new_mac_bufe[5]+i*2+2)
            ip_i = str(ip_bufe[0])+'.'+str(ip_bufe[1])+'.'+str(ip_bufe[2])+'.'+str(ip_bufe[3]+i*2+2)
            self.set_dev_mac(ip_i,new_mac_i)
#            print(ip_i,new_mac_i,baord_num)

    def ip_used(self,ip):
        #检测已使用的ip
        device = generate_ip(ip)
        dev_ip = []
        for i in range(len(device[1])):
            dev_ip.append(device[1][i][0])
        for i in range(len(device[2])):
            dev_ip.append(device[2][i][0])
        for i in range(len(device[3])//4):
            dev_ip.append(device[3][i*4][0]) 
        for i in range(len(device[4])//4):
            dev_ip.append(device[4][i*4][0])
        
        
        return dev_ip
    
    def ip_in_use(self,ip,new_ip):
        #检测ip是否已被使用
        
        ip_is_used = self.ip_used(ip)
        new_ip_i = self.conv_ip(new_ip[0][0])
        
        new_ip_ii = []
        new_ip_ii.append(str(new_ip_i[0])+'.'+str(new_ip_i[1])+'.'+str(new_ip_i[2])+'.'+str(new_ip_i[3]))
        for i in range(new_ip[0][2]//4):
            new_ip_ii.append(str(new_ip_i[0])+'.'+str(new_ip_i[1])+'.'+str(new_ip_i[2])+'.'+str(new_ip_i[3]+i*2+1))
            new_ip_ii.append(str(new_ip_i[0])+'.'+str(new_ip_i[1])+'.'+str(new_ip_i[2])+'.'+str(new_ip_i[3]+i*2+2))
        
        for i in range(len(new_ip_ii)):
            if new_ip_ii[i] in ip_is_used:
                return '设备id已被使用！'
        
        return '设备id未被使用！'
    
    def set_init_system_ip(self,dev_id):
        #恢复ip出厂设置
        for i in range(len(dev_id)):
            ip_bufe = self.conv_ip(dev_id[i][0])
            ip_i = str(ip_bufe[0])+'.'+str(ip_bufe[1])+'.'+str(ip_bufe[2])+'.'+str(255)
            fband_data_buf=[]
            fband_data_buf.append(np.uint8(0xbb))
            for i in range(31):
                fband_data_buf.append(np.uint8(0x00))
            
            my_udp_send(ip_i,5001,fband_data_buf)
    
    
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
            elif data_recv[i][0] == 0x00:
                data_recv_i.append('clock')
                data_recv_i.append(str(data_recv[i][1])+'.'+str(data_recv[i][2])+'.'+str(data_recv[i][3])+'.'+str(data_recv[i][4]))
                data_recv_i.append(str(data_recv[i][5])+':'+str(data_recv[i][6])+':'+str(data_recv[i][7])+':'+str(data_recv[i][8])+':'+str(data_recv[i][9])+':'+str(data_recv[i][10]))
            
            system_ip.append(data_recv_i)
        
        print(system_ip)
        
        return system_ip

    def read_system_id(self,system_id):
        #读取系统id
        system_ip = self.read_system_ip(system_id[0][0])
        
        system_id = []
        
        for i in range(len(system_ip)):
            if system_ip[i][0] == 'clock':
                board_type = ' '
                ch_num = 0
                ch_num_z = 0
                clk_ip = self.conv_ip(system_ip[i][1])
                dev_ip = str(clk_ip[0])+'.'+str(clk_ip[1])+'.'+str(clk_ip[2])+'.'+str(clk_ip[3]+1)
#                print(dev_ip)
                while 1:
                    for j in range(len(system_ip)):
                        if dev_ip in system_ip[j]:
                            board_type = system_ip[j][0]
#                            print(board_type)
                            ch_num += 1
                            break
                    
                    ch_num_z += 1
                    dev_ip = str(clk_ip[0])+'.'+str(clk_ip[1])+'.'+str(clk_ip[2])+'.'+str(clk_ip[3]+1+ch_num_z*2)
                    if ch_num_z == 3:
                        break
                    
                        
                system_id.append([system_ip[i][1],board_type,ch_num*4])
            
        
        
        
        
        return system_id

if __name__=='__main__':
    dev_ip=devip()

        
        