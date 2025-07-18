'''
    通过波形文件写波形或者直接波形数据，调用set_dac和set_adc方法
'''
import sys
import pickle
import zlib
import numpy as np
from os.path import dirname, abspath

project_path = dirname(dirname(abspath(__file__)))
sys.path.append(project_path+r'/lib_linux')

from device_interface import DeviceInterface
from logging_util import logger
dev = DeviceInterface()

def load(self, data):
    if data[0] == 0:
        return pickle.loads(data[1:])
    return pickle.loads(zlib.decompress(data[1:]))


def dump(obj, compress=False):
    b = pickle.dumps(obj)
    if compress:
        return b'\xff' + zlib.compress(b)
    return b'\x00' + b


def step_function(x, width):
    # 阶跃函数
    y = x < width  # numpy数组中的每个元素都与width比较大小，得到一个布尔型numpy数组
    return y.astype(np.int)  # astype()方法将numpy数组的布尔型转换为int型

def pressure_test():
    depth = 800
    trig_interval = 20e-6
    phase_count = 100
    amp = 26340  # 避免越界，比32768略小
    freq_list = [250e6, 120e6, 70e6, 76.9e6, 50e6, 20e6, 12.5e6, 10e6]
    freq_str = ['{freq:6.2f} MHz'.format(freq=freq / 1e6) for freq in freq_list]
    amp_temp = amp / len(freq_list)
    f_path = r'/home/test'
    session_id = "adda_pressure_test_001"
    host_mac = "00-50-56-87-c4-d3"
    ad_boards_list = [('QE10K4N0010', '00-00-00-00-00-5A')]
    master_da_board = ('QF10K4N0046', '10.0.200.73')
    ret = 0
    i = 0
    while i < phase_count:
        phase = 2 * np.pi / 100 * i
        i += 1
        # 生成八个频点的i/q波形
        wave_data = []
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

        for k in range(len(wave_data_i_list)):
            complex_vlaue = complex(wave_data_i_list[k],wave_data_q_list[k])
            wave_data.append(complex_vlaue)

        wave_data_b = np.array(wave_data).astype('c8').tobytes()
        wave_data = zlib.compress(wave_data_b, 1)

        if f_path:
            with open(f_path, 'wb') as wave_file:
                wave_file.write(wave_data)

        ad_lists =[]
        adc = {'target': 'QE10K4N0010', 'board_mac': '00-00-00-00-00-5A', 'demodulation_frequencies': [76900000.0, 70000000.0, 50000000.0, 20000000.0], 'demodulation_window_widths': [400, 400, 400, 400], 'sample_depth': 400, 'trigger_count': 2000, 'onboard_demodulation': True, 'demodulation_window_start_offsets': [0, 0, 0, 0], 'readable_qubits': ['Q00', 'Q01', 'Q02', 'Q03'], 'qubits': ['Q00', 'Q01', 'Q02', 'Q03'], 'work_mode': 'demo'}
        ad_lists.append(adc)

        #set_dac参数配置
        stop_item = [('QF10K4N0046',[1, 2]),('QF10K4N0016',[3, 4]),('QF10K4N0003',3),('QF10K4N0055',[3, 4]),('QF10K4N0016',[1, 2]),('QF10K4N0003',1),('QF10K4N0055',[1, 2]),('QF10K4N0055',[3, 4]),('QF10K4N0003',4)]
        da_dirs = {'control': {'QF10K4N0016[1, 2]': {'target': 'QF10K4N0016', 'target_ip': '10.0.200.74', 'init_gain': [192, 194, 185, 178], 'init_offset': [-452, -456, -178, -215], 'channel': [1, 2], 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q00', 'xy'), 'wave_data': wave_data}, 'QF10K4N00031': {'target': 'QF10K4N0003', 'target_ip': '10.0.200.76', 'init_gain': [224, 225, 174, 171], 'init_offset': [-130, -478, -452, -345], 'channel': 1, 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q00', 'z'), 'wave_data': wave_data}, 'QF10K4N0016[3, 4]': {'target': 'QF10K4N0016', 'target_ip': '10.0.200.74', 'init_gain': [192, 194, 185, 178], 'init_offset': [-452, -456, -178, -215], 'channel': [3, 4], 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q01', 'xy'), 'wave_data': wave_data}, 'QF10K4N00032': {'target': 'QF10K4N0003', 'target_ip': '10.0.200.76', 'init_gain': [224, 225, 174, 171], 'init_offset': [-130, -478, -452, -345], 'channel': 2, 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q01', 'z'), 'wave_data': wave_data}, 'QF10K4N0055[1, 2]': {'target': 'QF10K4N0055', 'target_ip': '10.0.200.75', 'init_gain': [194, 195, 177, 179], 'init_offset': [-476, -424, -451, -538], 'channel': [1, 2], 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q02', 'xy'), 'wave_data': wave_data}, 'QF10K4N00033': {'target': 'QF10K4N0003', 'target_ip': '10.0.200.76', 'init_gain': [224, 225, 174, 171], 'init_offset': [-130, -478, -452, -345], 'channel': 3, 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q02', 'z'), 'wave_data': wave_data}, 'QF10K4N0055[3, 4]': {'target': 'QF10K4N0055', 'target_ip': '10.0.200.75', 'init_gain': [194, 195, 177, 179], 'init_offset': [-476, -424, -451, -538], 'channel': [3, 4], 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q03', 'xy'), 'wave_data': wave_data}, 'QF10K4N00034': {'target': 'QF10K4N0003', 'target_ip': '10.0.200.76', 'init_gain': [224, 225, 174, 171], 'init_offset': [-130, -478, -452, -345], 'channel': 4, 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q03', 'z'), 'wave_data': wave_data}},
                    'readout': {'QF10K4N0046[1, 2]': {'target': 'QF10K4N0046', 'target_ip': '10.0.200.73', 'init_gain': [188, 181, 199, 199], 'init_offset': [-378, -360, -225, -282], 'channel': [1, 2], 'wave_data': wave_data, 'sync_delay': -16, 'output_delay': 16, 'trigger_delay': 16, 'qagent': 'R01'}},
                    'pump': {}, 'num_shots': 2000}

        #set_dac_sample参数配置
        # da_dirs = {'QF10K4N0046[1, 2]': {'target': 'QF10K4N0046', 'target_ip': '10.0.200.73', 'init_gain': [188, 181, 199, 199], 'init_offset': [-378, -360, -225, -282], 'channel': [1, 2], 'wave_data': wave_data, 'sync_delay': -16, 'output_delay': 16, 'trigger_delay': 16, 'qagent': 'R01'},
        #            'QF10K4N00031': {'target': 'QF10K4N0003', 'target_ip': '10.0.200.76', 'init_gain': [224, 225, 174, 171], 'init_offset': [-130, -478, -452, -345], 'channel': 1, 'sync_delay': -16, 'output_delay': 0, 'data_offset': None, 'qagent': ('Q00', 'z'), 'wave_data': wave_data}
        #           , 'num_shots': 2000
        #            }
        # stop_item = [('QF10K4N0046',[1, 2]),('QF10K4N0003',3)]

        da_cmd = dump(da_dirs)
        stop_cmd = dump(stop_item)
        ad_cmd = dump(ad_lists)

        ret |= dev.set_dac(da_cmd)
        #ret |= dev.set_dac_sample(da_cmd)
        ret |= dev.set_adc(ad_cmd)
        ret |= dev.da_trigger_enable(flag=True)

        for ad in ad_boards_list:
            ad_id = ad[0]
            res = dev.ad_receive_data(ad[0])
            if not isinstance(res, int):
                logger.info("采数成功")

    ret = dev.stop_dac(stop_cmd)
pressure_test()

    

    

