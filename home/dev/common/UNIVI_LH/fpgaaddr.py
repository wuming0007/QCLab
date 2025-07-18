# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 10:41:25 2009
创建一个字典 其中第一个包括板卡类型，第二个包括模块 内含有其特征起始地址信息
特征地址包括：
    0：重要寄存器读写地址
    1：板卡模块设置起始地址
    2：板卡模块写数据 I通道起始地址
    3：板卡模块写数据 Q通道起始地址
    4：板卡读数据模块I,Q地址
@author: wz
"""
T2DAAD={
        'baisc':{},
        'module0':{'daCtrolReg':0x10000,#module 0 2 DA
                   'setting':0x10004,
                   'Gain_I':0x20,#Gain
                   'Gain_Q':0x21,
                   'offset':0x10104,
                   'Idata':0x20000,   #每个模块I只对应其数据地址
                   'Qdata':0x40000      
                },
        'module1':{'adCtrolReg':0x22,#module 1 2 AD
                   'setting':0x22,
                   'Gain_I':0x40,#Gain
                   'Gain_Q':0x41,
                   'Idata':0x50000,   #每个模块I只对应其数据地址
                   'Qdata':0x60000      
                }
        }
Clock={'baisc':{'slot1_trig_delay':0x20,#slot1
                'slot2_trig_delay':0x21,#slot2
                'slot3_trig_delay':0x22,#  clock slot3 
                'slot4_trig_delay':0x23,#2ad2da slot4
                'slot5_trig_delay':0x24,#6da  slot5
                'slot6_trig_delay':0x25,#slot6
                'slot7_trig_delay':0x26,#slot7
                'slot8_trig_delay':0x27,#slot8
                'outtrig_delay':0x28,#triger out beiban
                }}
S6DA={
      'baisc':{},
        'module0':{'daCtrolReg':0x10000,#module 0 2 DA  dac A B 通道
                   'Gain_I':0x20,
                   'Gain_Q':0x21,
                   'offset':0x10104,
                   'setting':0x10004,
                   'Idata':0x20000,   #每个模块I只对应其数据地址
                   'Qdata':0x40000      
                },
        'module1':{'daCtrolReg':0x50000,#module 1 2 DA  dac  D E 通道
                   'setting':0x50004,
                   'Gain_I':0x23,
                   'Gain_Q':0x24,
                   'offset':0x50104,
                   'Idata':0x60000,   #每个模块I只对应其数据地址
                   'Qdata':0x70000       
                },
        'module2':{'daCtrolReg':0x80000,#module 2 1 DA  dac  C 通道
                   'Gain_I':0x22,
                   'offset':0x80104,
                   'setting':0x80004,
                   'Idata':0x90000,   #每个模块I只对应其数据地址
                   'Qdata':0x90000      
                },
        'module3':{'daCtrolReg':0xa0000,#module 3 1 DA   dac  F 通道
                   'setting':0xa0004,
                   'Gain_I':0x25,
                   'offset':0xa0104,
                   'Idata':0xb0000,   #每个模块I只对应其数据地址
                   'Qdata':0xb0000       
                }
        }

alladdr={'2DA2AD':T2DAAD,
         'Clock':Clock,
         '6DA':S6DA
        }

def addr(cardstr,modulestr,addrstr):
       if cardstr in alladdr.keys():
           if modulestr in alladdr[cardstr].keys():
               if addrstr in alladdr[cardstr][modulestr].keys():
                   return alladdr[cardstr][modulestr][addrstr]
       print('错误，没有找到相应键值！！！')
       return cardstr,modulestr,addrstr
    #%%
if __name__=='__main__':
    addr('2DA2AD','module0','setting')
    addr('6DA','module3','daCtrolReg')
    pass