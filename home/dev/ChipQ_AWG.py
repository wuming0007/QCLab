'''
Title: 
Description: Design for BAQIS, greeting to JJ who can't come in person
Version: 
Company: Casia
Author: hsj
Date: 2022-02-28 17:28:03
LastEditors: hsj
LastEditTime: 2022-07-08 19:16:27
'''

import numpy as np
from chipdriver import AWGDriver, LoadConfig
from waveforms import Waveform

from dev.common import BaseDriver, Quantity

# from pathlib import Path
# import json
# with open(Path(__file__).parent/'common/ChipQ/config.json', 'r', encoding='utf-8') as cfg:
#     LoadConfig(json.load(cfg))

cfg = {
    "version": "v2",
    "Network_Interface": "enp1s0f0",
    "Hosts_Table": {
        "board_43": {
            "mac": "00:12:47:0b:cc:24"
        },
        "board_44": {
            "mac": "00:0e:22:88:cc:52"
        },
        "board_45": {
            "mac": "00:0c:df:fb:cc:52"
        },
        "board_46": {
            "mac": "00:02:1a:69:cc:24"
        },
        "board_47": {
            "mac": "00:21:8e:bb:cc:5f"
        },
        "board_48": {
            "mac": "00:17:92:c7:cc:1e"
        },
        "board_49": {
            "mac": "00:27:84:36:cc:67"
        },
        "board_50": {
            "mac": "00:1a:fa:21:cc:1e"
        },
        "board_51": {
            "mac": "00:16:0f:cf:cc:24"
        },
        "board_52": {
            "mac": "00:2a:5f:22:cc:52"
        },
        "board_53": {
            "mac": "00:0c:88:42:cc:52"
        },
        "board_54": {
            "mac": "00:22:87:55:cc:24"
        },
        "board_55": {
            "mac": "00:27:4c:99:cc:1e"
        },
        "board_56": {
            "mac": "00:1f:f0:e1:cc:5f"
        },
        "board_57": {
            "mac": "00:1c:c9:c5:cc:52"
        },
        "board_58": {
            "mac": "00:09:f8:d3:cc:67"
        },
        "board_59": {
            "mac": "00:12:25:8e:cc:52"
        },
        "board_60": {
            "mac": "00:08:96:c7:cc:52"
        },
        "board_61": {
            "mac": "00:0b:75:00:cc:1e"
        },
        "board_62": {
            "mac": "00:1e:e1:7f:cc:24"
        },
        "board_63": {
            "mac": "00:1a:fd:27:cc:24"
        },
        "board_64": {
            "mac": "00:0f:50:0d:cc:1e"
        },
        "board_65": {
            "mac": "00:1a:3e:1a:3b:b8"
        },
        "board_66": {
            "mac": "00:14:46:ec:83:07"
        },
        "board_67": {
            "mac": "00:28:ba:e4:0c:31"
        },
        "board_68": {
            "mac": "00:10:20:22:0c:42"
        },
        "board_69": {
            "mac": "00:24:8c:ef:3b:4f"
        },
        "board_70": {
            "mac": "00:21:77:b9:3c:37"
        },
        "board_71": {
            "mac": "00:20:1c:55:0c:36"
        },
        "board_72": {
            "mac": "00:24:f3:5f:83:5d"
        },
        "board_73": {
            "mac": "00:0b:bd:d5:0c:3c"
        },
        "board_74": {
            "mac": "00:0e:e0:f5:0b:34"
        },
        "board_75": {
            "mac": "00:1f:89:96:3b:b2"
        },
        "board_76": {
            "mac": "00:0d:18:83:83:01"
        },
        "board_77": {
            "mac": "00:0c:0d:b9:0c:42"
        },
        "board_78": {
            "mac": "00:08:e5:21:0c:31"
        },
        "board_79": {
            "mac": "00:19:14:c4:3b:b2"
        },
        "board_80": {
            "mac": "00:27:92:16:0c:31"
        },
        "board_81": {
            "mac": "00:1d:e5:de:3b:b8"
        },
        "board_82": {
            "mac": "00:15:d4:b9:3b:49"
        },
        "board_83": {
            "mac": "00:0c:58:48:0b:39"
        },
        "board_84": {
            "mac": "00:1e:e9:4d:0c:36"
        }
    }
}


LoadConfig(cfg)


class Driver(BaseDriver):  # AWGDriver,

    CHs = [1, 2, 3, 4]

    quants = [
        Quantity('OffsetDC', unit='V', ch=1,),
        Quantity('Amplitude', value=1.38, ch=1, unit='Vpp'),  # 振幅
        Quantity('Offset', value=0, ch=1, unit='Vpp'),  # 振幅
        Quantity('Waveform', value=[], ch=1),  # 波形
        Quantity('Output', value=[], ch=1),  # 波形
        Quantity('IIR_FILTER_COE', value=[], ch=1),
    ]

    segment = ('xt', '116|117|118|119|120')

    def __init__(self, addr, **kw):
        '''
        :param host: str, 目标主机名
        :param default_amplitude: int, 默认振幅值, missing 0.
        :param default_offset: int, 默认偏移值, missing 0.
        '''

        # AWGDriver.__init__(self, addr, **kw)
        super().__init__(addr, **kw)
        self.addr = '192.168.116.2'
        # AWG模块名
        self.model = 'ChipQ-AWG'
        # AWG采样率
        self.srate = 2e9
        # AWG满量程 unit V
        self.max_v = 0.408
        self.mac = addr

    def open(self, **kw):
        self.handle = AWGDriver(self.mac)
        return super().open(**kw)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        c_index = kw.get("ch", 1) - 1
        if name == "Waveform":
            if isinstance(value, Waveform):
                wave = value.sample(self.srate)
            elif isinstance(value, np.ndarray):
                wave = value
            else:
                raise TypeError("未知的Waveform对象类型:{}.".format(type(value)))
            self.handle.set_waver(wave, c_index)
        elif name == "Amplitude":
            self.handle.set_amplitude(value, c_index)
        elif name == "Offset":
            self.handle.set_offset(value, c_index)
        elif name == "Output":
            self.handle.set_output(value, c_index)
        elif name == 'OffsetDC':
            wflen = int(99e-6 * self.srate)
            wfd = np.ones(wflen) * value
            self.handle.set_waver(wfd, c_index)
        elif name == 'IIR_FILTER_COE':
            self.handle.set_iir(value, c_index)
        else:
            pass

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)
