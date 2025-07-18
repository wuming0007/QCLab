# -- coding: utf-8 --
'''
    该程序主要展示同时控制多块DAQ/AWG板在单板、多板模式下输出波形、采数画圆功能
'''

import sys
from os.path import dirname, abspath

project_path = dirname(dirname(abspath(__file__)))
sys.path.append(project_path+r'/lib')


from device_interface import DeviceInterface
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from util import step_function

dev = DeviceInterface()

'''
    输入参数设置区域
    da_board_list：需要连接控制的AWG列表，类型list，元素是AWG元组，格式（'AWG ID','AWG IP地址'），
    ad_board_list：需要连接控制的DAQ列表，类型list，元素是DAQ元组，格式（'DAQ ID','DAQ Mac地址'），
                   DAQ元组的位置和AWG元组位置一一对应；
    host_mac: 主机mac地址
    channel_i：I通道号
    channel_q：Q通道号
    master_da_board：AWG ID元组，格式('AWG主板ID','AWG主板IP地址')，当触发模式为单板触发时，
                     格式(None,None)元组中元素填空；
    path：图片保存路径，需提前建好；
    depth：采样深度
    trig_count：触发次数
    trig_interval：触发间隔，单位4ns
    freq_list：频点，DAQ 最高支持8个频点同时解模；
    phase_count：相位变换最大个数
    amp：幅值
    freq_str：图片频率显示title
'''
da_boards_list = [('QF10K4N0046', '10.0.200.73')]  # 列出所有AWG ID
ad_boards_list = [('QE10K4N0010', '00-00-00-00-00-5A')]  # 列出与AWG对应的DAQ
host_mac = "00-50-56-87-c8-9F"
channel_i = 1
channel_q = 2
master_da_board = ('QF10K4N0046', '10.0.200.73')
path = project_path+'/pic/'

'''配置参数'''
depth = 800
trig_count = 1000
trig_interval = 20e-6
freq_list = [250e6, 120e6, 70e6, 76.9e6, 50e6, 20e6, 12.5e6, 10e6]
phase_count = 100
amp = 32767.5
freq_str = ['{freq:6.2f} MHz'.format(freq=freq / 1e6) for freq in freq_list]

ret = 0
'''连接并初始化所有AWG'''
for da_id, da_ip in da_boards_list:
    '''连接AWG'''
    ret |= dev.da_connect_device(da_id, da_ip)
    '''初始化AWG'''
    ret |= dev.da_init_device(da_id)
    if ret != 0:
        print(f'ERROR:da board [{da_id}] connect failure ,ret:[{ret}].')
        sys.exit(0)
print("all da boards connect and init success.")

'''连接并初始化所有DAQ'''
for ad_id, ad_mac in ad_boards_list:
    '''连接DAQ'''
    ret |= dev.ad_connect_device(ad_id, host_mac, ad_mac)
    '''初始化DAQ'''
    ret |= dev.ad_init_device(ad_id)
    if ret != 0:
        print(f'ERROR:ad board [{ad_id}] connect failure ,ret:[{ret}].')
        sys.exit(0)
print("all ad boards connect and init success.")

'''如果主板ID不为空，设置主板的触发次数触发间隔'''
if master_da_board[0] is not None:
    '''如果主板在da_board_list中，则不需要重复连接'''
    if master_da_board not in da_boards_list:
        ret |= dev.da_connect_device(master_da_board[0],master_da_board[1])
        ret |= dev.da_init_device(master_da_board[0])
    '''设置AWG 主板触发次数'''
    ret |= dev.da_set_trigger_count_l1(master_da_board[0], trig_count)
    '''设置AWG 主板触发间隔'''
    ret |= dev.da_set_trigger_interval_l1(master_da_board[0], trig_interval)
    if ret != 0:
        print(f'ERROR:master da board [{master_da_board[0]}] set trig failure,ret:[{ret}].')
        sys.exit(0)
    else:
        print(f'master da board [{master_da_board[0]}] set trig success .')

counts = len(ad_boards_list)
count = 0
cost_total = 0
ax = []
fig = plt.figure(figsize=(16, 8))
for i in range(0, counts):
    ax.append(fig.add_subplot(2, 2, i + 1))
plt.ion()  # 使图片的显示模式转换为交互模式

'''
    DAQ/AWG参数设置:
       1、如果单板触发，则设置单板模式，设置触发次数和触发延时；
       2、设置DAQ硬件解模模式、采样深度、触发次数；
       3、按频点设置解模窗口长度、起始位置、频率和提交；
       4、设置i/q通道偏置。
'''
for da, ad in zip(da_boards_list, ad_boards_list):
    ad_id = ad[0]
    da_id = da[0]
    if master_da_board[0] is None:
        '''设置AWG单板模式，mode=1为单板，默认mode为0'''
        ret |= dev.set_multi_board(da_id,1)
        ret |= dev.da_set_trigger_count_l1(da_id, trig_count)
    '''多板触发，从板也需要设置触发间隔'''
    ret |= dev.da_set_trigger_interval_l1(da_id, trig_interval)
    
    '''设置DAQ解模为硬件解模模式，mode=1为硬件解模模式，mode=0为软件解模模式'''
    ret |= dev.ad_set_mode(ad_id, 1)
    '''设置DAQ采样深度,depth为采样深度'''
    ret |= dev.ad_set_sample_depth(ad_id, depth)
    '''设置DAQ触发次数，与AWG触发次数一致'''
    ret |= dev.ad_set_trigger_count(ad_id, trig_count)

    k = 0
    for freq in freq_list:
        '''设置DAQ解模窗口长度'''
        ret |= dev.ad_set_window_width(ad_id, depth)
        '''设置DAQ解模窗口起始位置'''
        ret |= dev.ad_set_window_start(ad_id, 0)
        '''设置DAQ解模频率'''
        ret |= dev.ad_set_demod_freq(ad_id, freq)
        '''提交DAQ解模参数设置'''
        ret |= dev.ad_commit_demod_set(ad_id, k)
        k += 1
    '''设置通道偏置值'''
    ret |= dev.da_set_data_offset(da_id, channel_i, 0)
    ret |= dev.da_set_data_offset(da_id, channel_q, 0)
    if ret != 0:
        print(f'Error:da board[{da_id},ad board[{ad_id}] set params failure, ret:[{ret}].')
        sys.exit(0)

print('all da/ad boards set params success.')

#target_list = da_boards_list
#if master_da_board[0] is not None:
#    target_list.append(master_da_board)
#target_list = list(set(target_list))
#for target in target_list:
#    da_id = target[0]
#    dev.da_commit(da_id)

'''建立图层'''
for i in range(0, counts):
    ax[i].cla()
    ax[i].axis("equal")
    ax[i].set_title(f'{da_boards_list[i][0]}_{ad_boards_list[i][0]}')
    ax[i].grid(True)

ax_i = 0
for da, ad in zip(da_boards_list, ad_boards_list):
    legend = 0
    da_id = da[0]
    ad_id = ad[0]
    i = 0
    while i < phase_count:
        phase = 2 * np.pi / 100 * i
        amp_temp = amp / len(freq_list)

        # 生成八个频点的i/q波形
        wave_data_i_list = None
        wave_data_q_list = None
        x = list(range(2 * depth))
        for j in range(len(freq_list)):
            y = amp_temp * (step_function(np.arange((2 * depth))
                                          - step_function(np.arange(2 * depth) - 2 * depth, 2 * depth), 2 * depth))

            wave_data_i = y * np.cos(2 * np.pi * (freq_list[j] / 2e9) * np.array(x) + phase)
            wave_data_q = y * np.sin(2 * np.pi * (freq_list[j] / 2e9) * np.array(x) + phase)
            if wave_data_i_list is None:
                wave_data_i_list = wave_data_i
                wave_data_q_list = wave_data_q
            else:
                wave_data_i_list += wave_data_i
                wave_data_q_list += wave_data_q
        # print(wave_data)
        # plt.plot(wave_data)
        # plt.show()
        '''写波形，i 为通道i输出，q为通道q输出'''
        ret |= dev.da_write_wave(wave_data_i_list, da_id, channel_i, 'i', 0, 0, 0)
        ret |= dev.da_write_wave(wave_data_q_list, da_id, channel_q, 'q', 0, 0, 0)
        '''停止波形输出，防止通道有残留波形'''
        ret |= dev.da_stop_output_wave(da_id, channel_i)
        ret |= dev.da_stop_output_wave(da_id, channel_q)
        '''开始输出波形'''
        ret |= dev.da_start_output_wave(da_id, channel_i)
        ret |= dev.da_start_output_wave(da_id, channel_q)
        '''DAQ使能触发，开始接收数据，该设置必须在AWG使能触发之前做'''
        ret |= dev.ad_enable_adc(ad_id)
        if master_da_board[0] is None:
            '''AWG使能触发，AWG开始输出波形'''
            ret |= dev.da_trigger_enable(da_id)
        else:
            ret |= dev.da_trigger_enable(master_da_board[0])
        if ret != 0:
            print(f'Error:da board [{da_id}] wave output failure, ret:[{ret}].')
            sys.exit(0)
        else:
            print(f'da board [{da_id}] wave output success .')

        #ret |= dev.da_commit(da_id)
        #if ret != 0:
        #    print(f'Error:da board [{da_id}] commit failure, ret:[{ret}].')
        #    sys.exit(0)
        #else:
        #    print(f'da board [{da_id}] commit success .')

        time.sleep(0.01)
        '''DAQ采数'''
        res = dev.ad_receive_data(ad_id)
        if isinstance(res, int):
            break 
        '''对采到的数据求均值处理'''
        a = np.mean(res[1], axis=0) 
        b = np.mean(res[2], axis=0)

        '''实时画图'''
        color_list = list(colors.cnames.values())
        for k in range(0, len(freq_list)):
            ax[ax_i].scatter(a[k], b[k], c=color_list[10 + k * 5], label=freq_str[k], marker='.')
        if legend == 0:
            ax[ax_i].legend(loc='upper right')
            legend += 1
        plt.pause(20e-3)
        i += 1
    ret = dev.da_disconnect_device(da_id)
    if ret != 0:
        print(f'Error:da board [{da_id}] disconnect failure , ret:[{ret}].')
    ret = dev.ad_disconnect_device(ad_id)
    if ret != 0:
        print(f'Error:ad board [{ad_id}] disconnect failure , ret:[{ret}].')
    ax_i += 1
    data_pic_file = f'{path}multi_freq_demo_{time.time()}.png'
    plt.savefig(data_pic_file)
