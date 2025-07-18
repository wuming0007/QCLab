# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 15:40:09 2022

@author: UNIVI-WYM
Ver = 20220722
"""

#%%   
import socket
import struct
import numpy as np
import time

AllChannel = 32;

####    通道初始化
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
def initial_channel(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 0xF;
        SelChannel  = channel_num;
        
        SendData = [CMD,AllChannel];
        AllInit_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        SendData1 = [CMD,SelChannel,0];
        SelInit_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        client.connect(('192.168.4.222', 7))  
        
        if all_channel == 1 :
            client.send(AllInit_buf[:]) 
        else:
            client.send(SelInit_buf[:])  
        
        rece_data = client.recv(2) 
        print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
        client.close()
    else:
        print('initial_channel函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
####    硬件复位
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
def reset_channel(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 0;
        SelChannel  = channel_num;
        
        SendData = [CMD,AllChannel,0];
        AllReseta_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        SendData1 = [CMD,SelChannel,0];
        SelReset_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        client.connect(('192.168.4.222', 7))
        
        if all_channel == 1 :
            client.send(AllReseta_buf[:]) 
        else:
            client.send(SelReset_buf[:])   
        
        rece_data = client.recv(2) 
        print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
        client.close()
    else:
        print('reset_channel函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
    
####    硬件释放复位
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
def NOTreset_channel(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 0;
        SelChannel  = channel_num;
        
        SendData = [CMD,AllChannel,1];
        AllNOTReseta_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        SendData1 = [CMD,SelChannel,1];
        SelNOTReset_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        client.connect(('192.168.4.222', 7))  
        
        if all_channel == 1 :
            client.send(AllNOTReseta_buf[:]) 
        else:
            client.send(SelNOTReset_buf[:]) 
        
        rece_data = client.recv(2) 
        print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
        client.close()
    else:
        print('NOTreset_channel函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 

####    硬件复位后释放复位
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
def ResetCtrl(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        reset_channel(channel_num, all_channel);
        NOTreset_channel(channel_num, all_channel);
    else:
        print('ResetCtrl函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
    
####    LDAC值设定
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
####    ldac_val_volt：ldac寄存器输入值 直接输入目标电压值 输入范围-10~+10。
def set_ldac_value(channel_num, ldac_val_volt, all_channel):
    if(ldac_val_volt <= 10 and ldac_val_volt >= -10) :
        channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
        channel_num = channel_index[channel_num - 1]
        if (channel_num < 32) :
            CMD = 1;
            SelChannel  = channel_num;
            
            data_corr = ldac_val_volt * 0.00054
            ldac_val_volt = ldac_val_volt - data_corr + 0.0001
            
            hex_val = np.uint32((ldac_val_volt + 10)/20 * 0xfffff);
         
            hex_val1 = hex_val >> 16 & 0xff;
            hex_val2 = hex_val >> 8 & 0xff;
            hex_val3 = hex_val >> 0 & 0xff;
            
            SendData = [CMD,AllChannel,hex_val1,hex_val2,hex_val3];
            AllLDAC_buf = struct.pack("%dB" % (len(SendData)), *SendData)
            
            SendData1 = [CMD,SelChannel,hex_val1,hex_val2,hex_val3];
            SelLDAC_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
            
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
            client.connect(('192.168.4.222', 7)) 
            
            if all_channel == 1 :
                client.send(AllLDAC_buf[:]) 
            else:
                client.send(SelLDAC_buf[:]) 
            
            rece_data = client.recv(2) 
 #           print(rece_data.decode(encoding='UTF-8',errors='strict'))  
                
            client.close() 
        else:
            print('set_ldac_value函数参数输入错误');
            print('channel_num 输入范围0~31;输入值：',channel_num);
            return 0; 
    else:
        print('set_ldac_value函数参数输入错误');
        print('ldac_val_volt输入范围-10~+10;输入值：',ldac_val_volt);
        return 0; 
    
####    LDAC值输出使能
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
def LDAC_load(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
       CMD = 2;
       SelChannel  = channel_num;
       
       SendData = [CMD,AllChannel];
       AllLDACload_buf = struct.pack("%dB" % (len(SendData)), *SendData)
       
       SendData1 = [CMD,SelChannel];
       SelLDACload_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
       
       client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
       client.connect(('192.168.4.222', 7)) 
        
       if all_channel == 1 :
           client.send(AllLDACload_buf[:]) 
       else:
           client.send(SelLDACload_buf[:]) 
        
       rece_data = client.recv(2) 
       print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
       client.close() 
    else:
        print('LDAC_load函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
    
####    CLR值设定
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
####    clr_val_volt：clr寄存器输入值 直接输入目标电压值 输入范围-10~+10。
def set_clr_value(channel_num, clr_val_volt, all_channel):   
    if(clr_val_volt <= 10 and clr_val_volt >= -10) :
        channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
        channel_num = channel_index[channel_num - 1]
        if (channel_num < 32) :
            CMD = 3;
            SelChannel  = channel_num;
            hex_val = np.uint32((clr_val_volt + 10)/20 * 0xfffff);
         
            hex_val1 = hex_val >> 16 & 0xff;
            hex_val2 = hex_val >> 8 & 0xff;
            hex_val3 = hex_val >> 0 & 0xff;
            
            SendData = [CMD,AllChannel,hex_val1,hex_val2,hex_val3];
            AllLDAC_buf = struct.pack("%dB" % (len(SendData)), *SendData)
            
            SendData1 = [CMD,SelChannel,hex_val1,hex_val2,hex_val3];
            SelLDAC_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
            
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
            client.connect(('192.168.4.222', 7))  
            
            if all_channel == 1 :
                client.send(AllLDAC_buf[:]) 
            else:
                client.send(SelLDAC_buf[:]) 
            
            rece_data = client.recv(2) 
 #           print(rece_data.decode(encoding='UTF-8',errors='strict'))  
                
            client.close() 
        else:
            print('set_clr_value函数参数输入错误');
            print('channel_num 输入范围0~31;输入值：',channel_num);
            return 0; 
    else:
        print('set_clr_value函数参数输入错误');
        print('clr_val_volt输入范围-10~+10;输入值：',clr_val_volt);
        return 0; 
    
####    CLR值输出使能
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
def CLR_load(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
       CMD = 4;
       SelChannel  = channel_num;
       
       SendData = [CMD,AllChannel];
       AllLDACload_buf = struct.pack("%dB" % (len(SendData)), *SendData)
       
       SendData1 = [CMD,SelChannel];
       SelLDACload_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
       
       client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
       client.connect(('192.168.4.222', 7))
        
       if all_channel == 1 :
           client.send(AllLDACload_buf[:]) 
       else:
           client.send(SelLDACload_buf[:]) 
        
       rece_data = client.recv(2) 
       print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
       client.close() 
    else:
        print('CLR_load函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
 
    
####    CHANNEL 输出持续时间与间隔时间计时值寄存器，计数时钟为系统100M时钟,计数器为32位
####    channel_num:0-31位对应0-31通道  all_channel为全部通道选择,1为全部通道，0为channel_num通道。
####    trigger信号输入，此时为CLR寄存器输出的电平值，持续时间为CLR_TIMER
####    CLR_TIMER结束后，输出LDAC寄存器的电平值，持续时间为LDAC_TIMER
####    LDAC_TIMER结束后，输出CLR寄存器的电平值，持续时间直至下次TRIGGER信号输入
####    CLR_TIMER LDAC_TIMER 单位为us
def Trigg_TIMER(CLR_TIMER,LDAC_TIMER,channel_num, all_channel):
    if(CLR_TIMER > 10):
        if(LDAC_TIMER > 10):
            channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
            channel_num = channel_index[channel_num - 1]
            if (channel_num < 32) :
                CMD = 5;
                SelChannel  = channel_num;
                
                CLR_val = np.uint32(CLR_TIMER * 100);
                CLR_val0 = CLR_val >> 24 & 0xff;
                CLR_val1 = CLR_val >> 16 & 0xff;
                CLR_val2 = CLR_val >> 8 & 0xff;
                CLR_val3 = CLR_val >> 0 & 0xff;
                
                LDAC_val = np.uint32(LDAC_TIMER * 100);
                LDAC_val0 = LDAC_val >> 24 & 0xff;
                LDAC_val1 = LDAC_val >> 16 & 0xff;
                LDAC_val2 = LDAC_val >> 8 & 0xff;
                LDAC_val3 = LDAC_val >> 0 & 0xff;
                
                SendData = [CMD,AllChannel,CLR_val0,CLR_val1,CLR_val2,CLR_val3,LDAC_val0,LDAC_val1,LDAC_val2,LDAC_val3];
                All_buf = struct.pack("%dB" % (len(SendData)), *SendData)
                
                SendData1 = [CMD,SelChannel,CLR_val0,CLR_val1,CLR_val2,CLR_val3,LDAC_val0,LDAC_val1,LDAC_val2,LDAC_val3];
                Sel_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
                
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
                client.connect(('192.168.4.222', 7))
                
                if all_channel == 1 :
                    client.send(All_buf[:]) 
                else:
                    client.send(Sel_buf[:]) 
                
                rece_data = client.recv(2) 
                print(rece_data.decode(encoding='UTF-8',errors='strict'))  
                    
                client.close() 
                 
            else:
                print('Trigg_TIMER函数参数输入错误');
                print('channel_num 输入范围0~31;输入值：',channel_num);
                return 0; 
        else:
             print('Trigg_TIMER函数参数输入错误');
             print('LDAC_TIMER应该大于10us');
             return 0; 
    else:
         print('Trigg_TIMER函数参数输入错误');
         print('CLR_TIMER应该大于10us');
         return 0; 

####系统TRIGGER使能，disen时可用手动触发通道电平输出，en时只可依照TRIGGER信号进行电平切换
def trig_en(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 6;
        TrigEn = 1;
        SelChannel  = channel_num;
        trigAllEn = 1;
        trigSel = 0;
        
        SendData = [CMD,SelChannel,TrigEn,trigAllEn];
        All_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        SendData1 = [CMD,SelChannel,TrigEn,trigSel];
        Sel_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        client.connect(('192.168.4.222', 7)) 
        
        if all_channel == 1 :
            client.send(All_buf[:]) 
        else:
            client.send(Sel_buf[:]) 
        
        rece_data = client.recv(2) 
        print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
        client.close() 
        
    else:
        print('trig_en函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
    
def trig_disen(channel_num, all_channel):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 6;
        Trigdisen = 0;
        SelChannel  = channel_num;
        trigAllEn = 2;
        trigSel = 0;
        
        SendData = [CMD,SelChannel,Trigdisen,trigAllEn];
        All_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        SendData1 = [CMD,SelChannel,Trigdisen,trigSel];
        Sel_buf = struct.pack("%dB" % (len(SendData1)), *SendData1)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
        client.connect(('192.168.4.222', 7)) 
        
        if all_channel == 1 :
            client.send(All_buf[:]) 
        else:
            client.send(Sel_buf[:]) 
        
        rece_data = client.recv(2) 
        print(rece_data.decode(encoding='UTF-8',errors='strict'))  
            
        client.close() 
        
    else:
        print('trig_en函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 

####    读取LDAC寄存器电压值并打印此值 只能在所选通道运行LDAC_load函数后再进行回读
####    channel_num:0-31位对应0-31通道  
def RdRegLDAC(channel_num):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 7;
        SelChannel  = channel_num;
        
        SendData = [CMD,SelChannel,0x1f,0xff,0xff];
        Send_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        client.connect(('192.168.4.222', 7))
        
        client.send(Send_buf[:]) 

        rece_data = client.recv(4) 
        net_recv_data = list(rece_data)  
        
        LDACData = ((net_recv_data[2] << 16) | (net_recv_data[1] << 8) | net_recv_data[0])& 0x0fffff
        
        LDACV = ((20*LDACData)/0xfffff)-10
        print(LDACV)
            
        client.close() 
        
    else:
        print('RdRegLDAC函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
    
####    读取CLR寄存器电压值并打印此值 只能在所选通道运行CLR_load函数后再进行回读
####    channel_num:0-31位对应0-31通道  
def RdRegCLR(channel_num):
    channel_index = [1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30,0,2,4,6,8,10,12,14,17,19,21,23,25,27,29,31]
    channel_num = channel_index[channel_num - 1]
    if (channel_num < 32) :
        CMD = 7;
        SelChannel  = channel_num;
        
        SendData = [CMD,SelChannel,0x3f,0xff,0xff];
        Send_buf = struct.pack("%dB" % (len(SendData)), *SendData)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        client.connect(('192.168.4.222', 7))
        
        client.send(Send_buf[:]) 

        rece_data = client.recv(4) 
        net_recv_data = list(rece_data)  
        
        LDACData = ((net_recv_data[2] << 16) | (net_recv_data[1] << 8) | net_recv_data[0])& 0x0fffff
        
        LDACV = ((20*LDACData)/0xfffff)-10
        print(LDACV)
            
        client.close() 
        
    else:
        print('RdRegLDAC函数参数输入错误');
        print('channel_num 输入范围0~31;输入值：',channel_num);
        return 0; 
    
####   输出电压按规律变化(增、减)
def TestLdac(channel_num):
    for i in range(2000):
        com = -9.98999 + (i*0.01);
        set_ldac_value(channel_num,com,0);
        LDAC_load(channel_num,0);
        time.sleep(0.5);
####   16通道按0.5递增
def TestLdac1():
    for ch_num in range(16):
        set_ldac_value(ch_num + 1, 0.25 * (ch_num + 1), 0);
        LDAC_load(ch_num + 1, 0);
#%% 
    initial_channel(11,0);
#%% 
    reset_channel(11,0); 
#%% 
    set_ldac_value(16,1.8,0);
#%% 
    LDAC_load(16,0);
    #%%    
    set_clr_value(3,-9,0);
#%% 
    LDAC_load(16,0);
#%% 
    CLR_load(3,0);
#%%    
    Trigg_TIMER(9000000,9000000,15,0);
#%% 
    trig_en(5,0);
#%% 
    trig_disen(1,1);
#%% 
    RdRegLDAC(3);
#%%    
    RdRegCLR(3);
#%%      
    NOTreset_channel(11,1);
    
#%% 
    set_ldac_value(11,1.9,0);
    LDAC_load(11,0);
 #%%    
    TestLdac1()