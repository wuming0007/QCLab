import time
from typing import Optional

import numpy as np

from dev.common import BaseDriver, QBool, QInteger, QReal, QVector, QString

from waveforms import Waveform
# try:
from dev.common.ZWD_DDS import ddssoc as fpgadev
# except:
#     print('Import fpgadev of DDS ADDA Error!')


class Driver(BaseDriver):

    support_models = ['ZW_RFSOC_AWG']

    CHs_num = 24

    CHs = list(range(1, CHs_num + 1, 1))

    alg_use = [True] * CHs_num  # 八个通道是否使用硬解模
    raw_use = [False] * CHs_num  # 八个通道是否使用软解模
    alg_num = [0] * CHs_num  # 硬解模每个通道的频率数目，上限是30

    _sampling_mode = None  # 切换DAC采样率 0 为8Gsps, 不支持其它采样率
    _nyquist = [None] * CHs_num
    _trigger_us = 200
    _trigger_num = 1
    _trigger_source = 1  # 0 为内部触发，1为外部触发
    _trigger_continue = 0
    _intrinsic_waveform_length = 61e-6

    quants = [
        # ADDA
        # TriggerSource 0 为内部触发，1为外部触发
        QString('TriggerSource', ch=1, value='External'),
        # TriggerPeriod(float)： 单位us, 5Gsps 78.125MHz, 对应12.8ns; 4Gsps 62.5MHz，对应16ns，必须为对应时长的整倍数
        QReal('TriggerPeriod', ch=1, unit='s', value=200e-6),
        # TriggerNumber 触发次数，当trigger_continue为1时无效
        QInteger('TriggerNumber', ch=1, unit='', value=1),
        # TriggerContinue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        QBool('TriggerContinue', ch=1, value=False),
        QReal('TriggerDelay', value=0, unit='s', ch=1,),
        QInteger('Trigger', value=0, ch=1),
        QInteger('SamplingMode', ch=1, value=6000),
        QInteger('SamplingRate', ch=1, value=6000),

        # DA
        QReal('Offset', unit='V', ch=1),
        QReal('Amplitude', unit='VPP', ch=1),
        QInteger('Output', value=1, ch=1),
        QVector('Waveform', value=[], ch=1),
        QBool('WaveformContinue', value=False, ch=1),  # 通道波形是否连续
        QString('Nyquist', value='mix', ch=1),

        # # AD
        # QReal('FrequencyList', value=[], unit='Hz', ch=1),  # 解调频率
        # QReal('PhaseList', value=[], unit='1', ch=1),  # 解调频率
        # QInteger('Shot', value=2048, ch=1),  # 利用setValue方法来对重复采样次数设置
        # QInteger('PointNumber', value=2048, ch=1),  # 采集点数
        # QBool('avg', value=False, ch=1),  # 是否对数据进行平均
        # QInteger('Coefficient', value=None, ch=1),  # 解调系数
        # QVector('TraceIQ', value=[], ch=1),
        # QVector('IQ', value=[], ch=1),
        # QInteger('StartCapture', value=1, ch=1),  # 开始采集模式：0连续，1触发
        # # 是否使用硬解模, 'alg' 纯硬解模, 'raw' 纯解模, 'raw_alg' 软硬皆有
        # QString('CaptureMode', value='alg', ch=1),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr=addr, **kw)
        self.model = 'ZW_RFAWG1000_24'
        self.handle = fpgadev()
        self.srate = 8e9

    def open(self):
        self.triggerClose()
        # self.setValue('SamplingMode', 6000)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)

        if name.startswith('Trigger'):
            self.set_TRIG(name, value)

        if name in ['Waveform', 'Output', 'Nyquist']:
            if ch > 0 and ch < 25:  # DA
                self.set_DA(name, value, ch)
            else:
                raise ValueError('DA channel number error!!!')

        elif name in ['SamplingMode']:
            new_sr = round(value / 200) * 200
            self.handle.rfdac_sampling(new_sr)
            self.srate = new_sr * 1e6
        elif name in ['SamplingRate']:
            new_sr = round(value / 200) * 200
            # self.handle.rfdac_sampling(new_sr)
            self.srate = new_sr * 1e6

        return value

    def read(self, name: str, **kw):
        super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def set_TRIG(self, name, value):
        if name in ['TriggerPeriod']:
            periodTime = 160
            times = round(value * 1e9 / periodTime)
            assert periodTime * times == value * \
                1e9, 'Sampling mode does not mach triggerTime! Please change trigger_us via setValue() function'
            self._trigger_us = value * 1e6
        elif name in ['TriggerSource']:
            assert value in ['Internal',
                             'External'], 'Trigger source is not supported.'
            self._trigger_source = int(value == 'External')
        elif name in ['TriggerNumber']:
            self._trigger_num = value
        elif name in ['TriggerContinue']:
            self._trigger_continue = int(value)
        elif name in ['Trigger']:
            self.Trig()

    def Trig(self):
        '''  
           trigger_source 0 为内部触发，1为外部触发
           trigger_us 触发周期单位us; 8Gsps 6.25MHz, 对应160ns,必须为对应时长的整倍数
           trigger_num 触发次数，当trigger_continue为1时无效
           trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        '''
        ret = self.handle.trigger_ctrl(trigger_source=self._trigger_source,
                                       trigger_us=self._trigger_us,
                                       trigger_num=self._trigger_num,
                                       trigger_continue=self._trigger_continue)
        assert ret == 'ok', 'Error in `Trig()`'

    def set_DA(self, name, value, ch):
        """ch starts from 1
        """
        if name in ['Waveform']:
            trigger_delay = round(
                self.config['TriggerDelay'][ch]['value'] * self.srate)
            continuous = self.config['WaveformContinue'][ch]['value']
            if isinstance(value, Waveform):
                value = value.sample(self.srate)
            self.writeWaveform(
                value, ch=ch, trigger_delay=trigger_delay, continuous=continuous)
        elif name in ['Output']:
            if value:
                self.on(ch=ch)
            else:
                self.off(ch=ch)
        elif name in ['Nyquist']:
            if value == 'normal':
                if self._nyquist[ch - 1] in ['mix', None]:
                    self.handle.rfdac_SetNyquistZone(NyquistZone=0)
                    self._nyquist[ch - 1] = 'normal'
                    time.sleep(0.1)
            elif value == 'mix':
                if self._nyquist[ch - 1] in ['normal', None]:
                    self.handle.rfdac_SetNyquistZone(NyquistZone=1)
                    self._nyquist[ch - 1] = 'mix'
                    time.sleep(0.1)
            else:
                pass

    def writeWaveform(self, data, ch=1, trigger_delay=0, continuous=False):
        data = np.asarray(data).clip(-1, 1)
        data = data * (2**13 - 1)
        dac_data = np.int16(data)
        data_len = len(dac_data)
        if data_len > 15360 * 32:
            return 'write dac data too long !!!'

        replay_cnt = 100000000
        replay_continue_flag = int(continuous)

        # self.triggerClose()
        self.handle.dac_updata(ch - 1, trigger_delay,
                               replay_cnt, replay_continue_flag, dac_data)

        # if self._trigger_source:
        #     self.Trig()

    def on(self, ch):  # 打开通道
        ret = self.handle.dac_open(ch - 1)

        assert ret == 'ok', 'Error in `on()`'

    def off(self, ch):  # 关闭通道
        ret = self.handle.dac_close(ch - 1)
        assert ret == 'ok', 'Error in `off(2)`'

    def channel_ip(self):
        return self.handle.dev_id.da

    def triggerClose(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.trigger_close()
        assert ret == 'ok', 'Error in `triggerClose()`'
