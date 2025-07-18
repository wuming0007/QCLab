# -*- coding: utf-8 -*-
"""
Created on Fri May 31 14:51:04 2024

@author: XGKJ
"""
import os,re
import time

class update_ip(object):
    def __init__(self):
        self.ip_list = self.get_ip()  

    def get_ip(self):  
        result = os.popen('ipconfig')  
        res = result.read()  
        resultlist = re.findall('''(?<=以太网适配器 ).*?(?=:)''', res)  
        return resultlist 

    def set_ip(self,ip="192.168.201.137",mask="255.255.248.0",gateway="192.168.200.1"):  
        time.sleep(1)
        name = self.ip_list[0]
        net_cmd = f"netsh interface ip set address name={name} static {ip} {mask} {gateway}"
        result = os.system(net_cmd)
        if result == 0:
            print('set ip ok!')
        else:
            print('set ip err!')
        # print(result)

    def reboot(self):
        net_cmd = f"shutdown -r -f -t 0"
        os.system(net_cmd) 
    def shutdown(self):
        net_cmd = f"shutdown -s -f -t 0"
        os.system(net_cmd) 

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