import time

import numpy as np

from dev.common import BaseDriver, QBool, QInteger, QReal, QVector
from dev.common.quantity import QString
from waveforms import Waveform
import time


try:
    from dev.common.ZWD_DDS import RF_AWG1000
except:
    print('Import fpgadev of ZW_RF_AWG1000 Error!')


class Driver(BaseDriver):

    CHs_num = 12
    CHs = list(range(1, CHs_num + 1, 1))
    _sampling_mode = None  # 切换采样率 0 为5Gsps；1 为4Gsps
    _nyquist = None
    # dev_ip = ["192.168.1.2:9003", 9003]

    quants = [
        QInteger('Output', value=1, ch=1),
        QString('SamplingMode', ch=1, value='5G'),
        QString('SamplingRate', ch=1, value='5G'),
        QString('Nyquist', value='mix', ch=1),
        QBool('continue', value=False, ch=1),  # 通道波形是否连续
        QVector('Waveform', value=[], ch=1),
        QReal('TriggerDelay', value=0, unit='s', ch=1),
        QInteger('RefClock', value=10, ch=1),
    ]

    segment = ('zw', '121|122|123|124|125')

    def __init__(self, addr, **kw):
        super().__init__(addr=addr, **kw)
        self.model = 'ZW_RF_AWG1000'
        self.srate = 4e9
        # self.port = int(port)
        # self.dev_ip = (addr, port)

    def open(self):
        self.handle = RF_AWG1000()
        self.addr = f'{self.addr}:9003'
        pp = self.addr.split(':')
        self.handle.connect(pp[0], int(pp[1]))  # 连接设备

    def close(self):
        self.handle.disconnect()  # 断开设备连接

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        # print(name,value,'sssssssssssssssssssssssssssssssssss')

        if name in ['SamplingMode']:
            if value in ['4G']:
                if self._sampling_mode in [None, 0]:
                    self._sampling_mode = 1
                    status = self.handle.set_sampling_rate("4G")  # 设置采样率为4G采样
                    assert status == True, 'Error in `write()` SamplingMode()'
                    self.srate = 4e9
                    time.sleep(1)
            elif value in ['5G']:
                if self._sampling_mode in [None, 1]:
                    self._sampling_mode = 0
                    status = self.handle.set_sampling_rate("5G")  # 设置采样率为5G采样
                    assert status == True, 'Error in `write()` SamplingMode()'
                    self.srate = 5e9
                    time.sleep(1)
            else:
                raise ValueError(
                    'SamplingMode error! It should be "4G" or "5G"')
        elif name in ['SamplingRate']:
            if value in ['4G']:
                self.srate = 4e9
            elif value in ['5G']:
                self.srate = 5e9
            else:
                raise ValueError(
                    'SamplingRate error! It should be "4G" or "5G"')
        elif name in ['Nyquist']:
            if value == 'normal':
                if self._nyquist in ['mix', None]:
                    status = self.handle.set_mode_switch("NRZ")  # 模式切换
                    assert status == True, 'Error in `write()` Nyquist'
                    self._nyquist = 'normal'
                    time.sleep(1)
            elif value == 'mix':
                if self._nyquist in ['normal', None]:
                    status = self.handle.set_mode_switch("MIX")  # 模式切换
                    assert status == True, 'Error in `write()` Nyquist'
                    self._nyquist = 'mix'
                    time.sleep(1)
            else:
                pass
        elif name in ['Output']:
            if value:
                self.on(ch=ch)
            else:
                self.off(ch=ch)
        elif name in ['Waveform']:
            # import pickle
            # with open('test1', 'wb') as f:
            #     pickle.dump(value, f)
            if isinstance(value, Waveform):
                if self.srate < 0:
                    raise ValueError(
                        'Please write `driver.srate`(`SamplingRate`) before waveform'
                    )
                value = value.sample(self.srate)
            trigger_delay = round(self.config['TriggerDelay'][ch]['value'])
            continuous = self.config['continue'][ch]['value']
            self.off(ch)
            self.writeWaveform(value,
                               ch=ch,
                               trigger_delay=trigger_delay,
                               continuous=continuous)

            self.on(ch)
            # time.sleep(5)
        elif name in ['RefClock']:
            if value in [10, 100]:
                status = self.handle.set_refclk("ext_ref", value)  # 设置外参考10M
                assert status == True, 'Error in `open()` set_refclk()'
            elif value in [0]:
                status = self.handle.set_refclk("int_ref")  # 设置外参考10M
                assert status == True, 'Error in `open()` set_refclk()'

        return value

    def read(self, quant, **kw):
        return super().read(quant, **kw)

    def writeWaveform(self, data, ch=1, trigger_delay=0, continuous=False):
        # data = np.asarray(data).clip(-1, 1)
        # data = data * (2**15 - 1)
        # data = np.int16(data)

        dac_data = data
        # import pickle
        # with open('test', 'wb') as f:
        #     pickle.dump(data, f)

        if continuous is True:
            # 设置播放模式为连续播放模式 ”continue“ "pulse"
            status1 = self.handle.set_play_mode("continue")
        else:
            # 设置播放模式为连续播放模式 ”continue“ "pulse"
            status1 = self.handle.set_play_mode("pulse")
        status2 = self.handle.set_channel_delay(
            ch, trigger_delay, self._sampling_mode)  # 设置通道一延时，单位s
        status3 = self.handle.send_waveform_data(ch, dac_data)
        assert status1 == True, 'Error in `writeWaveform()` set_play_mode()'
        assert status2 == True, 'Error in `writeWaveform()` set_channel_delay()'
        assert status3 == True, 'Error in `writeWaveform()` send_waveform_data()'

    def on(self, ch):  # 打开通道
        status = self.handle.open_channel([ch])  # 打开通道
        assert status == True, 'Error in `on()`'

    def off(self, ch):  # 关闭通道
        status = self.handle.close_channel([ch])  # 关闭通道
        assert status == True, 'Error in `off()`'

    def set_device_ip(self, ip: str):
        self.dev_ip[0] = ip
        status = self.handle.set_ip(self.dev_ip[0])  # 更改设备IP
        assert status == True, 'Error in `set_device_ip()`'
