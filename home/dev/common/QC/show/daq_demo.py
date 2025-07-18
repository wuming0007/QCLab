# -- coding: utf-8 --
'''
    展示解模功能
    为了直观地观察是否有效控制awg输出理想波形以及daq的硬件后处理算法是否有效。
    将采集到的模拟信号经过后处理（解模）在复频域用极坐标的方式直观展示出来。
    采集到的波形的相位即是圆心角，幅度也可以用半径间接表征。只有awg被有效控制，
    同时daq正确采数并实时后处理才能呈现出好的圆。
'''
import sys
from os.path import dirname, abspath

sys.path.append(r'E:\PythonQOS\Repository\MeasModule\QOS\Driver\drivers\lib')
from device_interface import DeviceInterface 

import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from util import step_function

dev = DeviceInterface()
# da_list = [
#     ('QF10KBE0003', '10.0.200.1'), ('QF10KBE0004', '10.0.200.2'),('QF10KBE0005', '10.0.200.3'),('QF10KBE0006', '10.0.200.4'),('QF10KBE0002', '10.0.200.5'),('QF10KBE0007', '10.0.200.6'),('QF10KBE0009', '10.0.200.7'),
#     ('QF10KBE0008', '10.0.200.11'),('QF10KBE0010', '10.0.200.12'),('QF10L4S0004', '10.0.200.13'),('QF10L4S0007', '10.0.200.14'),('QF10L4S0006', '10.0.200.15'),('QF10L4S0003', '10.0.200.16')
# ]
# master_da_board = ('QF10KBE0003', '10.0.200.1')

da_id, da_ip = ('QF10L4S0005', '10.0.200.10')#('QF10L4S0005', '10.0.200.10')  # 列出所有AWG ID
ad_id , ad_mac = ('QE10KBE0002', '00-00-00-00-00-87')  # 列出与AWG对应的DAQ
host_mac = "74-86-E2-0C-65-B3"  # 本机MAC
channel_i = 1  # I通道
channel_q = 2  # Q通道
master_id, master_ip = ('QF10KBE0003', '10.0.200.1')
path = 'E:\PythonQOS\Repository\MeasModule\QOS\Driver\drivers'+'/pic/'

# 配置参数
depth = 800
trig_count = 3000
trig_interval = 20e-6
freq_list = [250e6, 120e6, 70e6, 76.9e6, 50e6, 20e6, 12.5e6, 10e6]
phase_count = 100
amp = 32767.5  # 避免越界，比32768略小
freq_str = ['{freq:6.2f} MHz'.format(freq=freq / 1e6) for freq in freq_list]

# AWG连接初始化
ret = 0
ret |= dev.da_connect_device(da_id, da_ip)
ret |= dev.da_init_device(da_id)
if master_id is not None:
    ret |= dev.da_connect_device(master_id, master_ip)
    ret |= dev.da_init_device(master_id)
if ret != 0:
    print(f'Error:DA:[{da_id}] connect fauilure, ret:[{ret}] .')
    sys.exit(0)
else:
    print(f'DA:[{da_id}] connect success .')

# DAQ连接初始化
ret |= dev.ad_connect_device(ad_id, host_mac, ad_mac)
ret |= dev.ad_init_device(ad_id)
if ret != 0:
    print(f'Error:AD:[{ad_id}] connect fauilure, ret:[{ret}] .')
    sys.exit(0)
else:
    print(f'AD:[{ad_id}] connect success .')

# 设置主板的触发次数触发间隔,如果是单板则触发单板
if master_id is not None:
    ret |= dev.da_set_trigger_count_l1(master_id, trig_count)
    ret |= dev.da_set_trigger_interval_l1(master_id, trig_interval)
    dev.da_set_trigger_delay(master_id, 40.4e-6)
    
else:
    ret |= dev.set_multi_board(da_id,1)
    ret |= dev.da_set_trigger_count_l1(da_id, trig_count)
'''多板触发，从板也需要设置触发间隔'''
ret |= dev.da_set_trigger_interval_l1(da_id, trig_interval)
dev.da_set_trigger_delay(da_id, 40.4e-6)
if ret != 0:
    print(f'ERROR:da board:[{da_id}] set trig failure, ret:[{ret}].')
    sys.exit(0)
else:
    print(f'da board:[{da_id}] set trig success .')

# 设置DAQ参数
# 1、设置DAQ板硬件解模模式
# 2、设置DAQ板采样深度
# 3、设置DAQ板触发次数
ret |= dev.ad_set_mode(ad_id, 1)
ret |= dev.ad_set_sample_depth(ad_id, depth)
ret |= dev.ad_set_trigger_count(ad_id, trig_count)
if ret != 0:
    print(f'ERROR:ad board:[{ad_id}] set param failure, ret:[{ret}].')
    sys.exit(0)
else:
    print(f'da board:[{da_id}] set param success .')

# 设置八个频点窗口参数，包括解模窗口长度、解模起始位置、解模频率、提交
k = 0
for freq in freq_list:
    ret |= dev.ad_set_window_width(ad_id, depth)
    ret |= dev.ad_set_window_start(ad_id, 0)
    ret |= dev.ad_set_demod_freq(ad_id, freq)
    ret |= dev.ad_commit_demod_set(ad_id, k)
    k += 1

# 设置I/Q通道默认偏置
ret |= dev.da_set_data_offset(da_id, channel_i, 0)
ret |= dev.da_set_data_offset(da_id, channel_q, 0)
# dev.da_set_channel_default_voltage()

# 建立图层
fig = plt.figure()
ax = fig.add_subplot(2, 2, 1)
plt.ion()  # 使图片的显示模式转换为交互模式

ax.cla()
ax.axis("equal")
ax.set_title(f'{da_id}_{ad_id}')
ax.grid(True)
ax_i = 0

i = 0
legend = 0
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
    # 1、写波形到i/q通道
    # 2、停止i/q通道波形输出，防止在输出波形前有残留波形
    # 3、开始i/q通道波形输出
    # 4、DAQ触发使能
    # 5、AWG触发使能输出
    ret |= dev.da_write_wave(wave_data_i_list, da_id, channel_i, 'i', 0, 0, 0)
    ret |= dev.da_write_wave(wave_data_q_list, da_id, channel_q, 'q', 0, 0, 0)
    ret |= dev.da_stop_output_wave(da_id, channel_i)
    ret |= dev.da_stop_output_wave(da_id, channel_q)
    ret |= dev.da_start_output_wave(da_id, channel_i)
    ret |= dev.da_start_output_wave(da_id, channel_q)
    ret |= dev.ad_enable_adc(ad_id)
    if master_id is None:
        ret |= dev.da_trigger_enable(da_id)
    else:
        ret |= dev.da_trigger_enable(master_id)

    time.sleep(0.01)
    # 采数
    res = dev.ad_receive_data(ad_id)
    if isinstance(res, int):
        break 
    a = np.mean(res[1], axis=0)  # 对各列求均值
    b = np.mean(res[2], axis=0)

    # 绘图
    color_list = list(colors.cnames.values())
    for k in range(0, len(freq_list)):
        ax.scatter(a[k], b[k], c=color_list[10 + k * 5], label=freq_str[k], marker='.')
    if legend == 0:
        ax.legend(loc=2, bbox_to_anchor=(1.05,1.0),borderaxespad = 0.)
        legend += 1
    plt.pause(20e-3)
    i += 1
data_pic_file = f'{path}{da_id}_{ad_id}_multi_freq_demo_{time.time()}.png'
plt.savefig(data_pic_file)
