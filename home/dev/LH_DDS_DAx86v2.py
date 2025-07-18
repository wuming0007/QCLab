import time

import numpy as np

from dev.common import BaseDriver, QBool, QInteger, QReal, QVector, QString
from waveforms import Waveform
import time

try:
    from dev.common.DDS_LH import ddsx86
except:
    print('Import fpgadev of DDS DA Error!')


class Driver(BaseDriver):

    support_models = ['LH_DDS_DA']

    CHs_num = 12

    CHs = list(range(1, CHs_num + 1, 1))

    _sampling_mode = None  # 切换采样率 0 为5Gsps；1 为4Gsps
    _nyquist = [None] * CHs_num
    _trigger_us = 200
    _trigger_num = 1
    _trigger_source = 1  # 0 为内部触发，1为外部触发
    _trigger_continue = 0

    quants = [
        QReal('Offset', unit='V', ch=1),
        QReal('Amplitude', unit='VPP', ch=1),
        QInteger('Output', value=1, ch=1),
        QVector('Waveform', value=[], ch=1),

        QString('SamplingMode', ch=1, value='5G'),
        # TriggerPeriod(float)： 单位us, 5Gsps 78.125MHz, 对应12.8ns; 4Gsps 62.5MHz，对应16ns，必须为对应时长的整倍数
        QString('SamplingRate', ch=1, value='5G'),
        QReal('TriggerPeriod', ch=1, unit='s', value=200e-6),
        # TriggerSource 0 为内部触发，1为外部触发
        QString('TriggerSource', ch=1, value='External'),
        # TriggerNumber 触发次数，当trigger_continue为1时无效
        QInteger('TriggerNumber', ch=1, unit='', value=1),
        # TriggerContinue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        QBool('TriggerContinue', ch=1, value=False),
        QString('Nyquist', value='mix', ch=1),

        QReal('TriggerDelay', value=0, unit='s', ch=1,),
        QBool('continue', value=False, ch=1),  # 通道波形是否连续

        QInteger('TRIG', value=0, ch=1),
    ]

    segment = ('lh', '107|108|109')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'LH_DDSx86'

    def open(self):
        # self.CHs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.handle = ddsx86()
        self.handle.trigger_close()

        # self.setValue('SamplingMode', '5G')
        # for ch in self.CHs:
        #     self.setValue('Nyquist', 'mix', ch=ch)
        #     self.on(ch=ch)

        # if self._trigger_source:
        #     self.Trig()

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name in ['Waveform']:
            if isinstance(value, Waveform):
                if self.srate < 0:
                    raise ValueError(
                        'Please write `driver.srate`(`SamplingRate`) before waveform'
                    )
                value = value.sample(self.srate)
            trigger_delay = round(self.config['TriggerDelay'][ch]['value'] *
                                  self.srate)
            continuous = self.config['continue'][ch]['value']
            t0 = time.time()
            self.writeWaveform(value,
                               ch=ch,
                               trigger_delay=trigger_delay,
                               continuous=continuous)
        elif name in ['Output']:
            if value:
                self.on(ch=ch)
            else:
                self.off(ch=ch)
        elif name in ['SamplingMode']:
            if value in ['4G']:
                if self._sampling_mode in [None, 0]:
                    self._sampling_mode = 1
                    self.handle.system_sampling(sampling=self._sampling_mode,
                                                step=0,
                                                self_set=1)
                    self.srate = 4e9
                    time.sleep(1)
            elif value in ['5G']:
                if self._sampling_mode in [None, 1]:
                    self._sampling_mode = 0
                    self.handle.system_sampling(sampling=self._sampling_mode,
                                                step=0,
                                                self_set=1)
                    self.srate = 5e9
                    time.sleep(1)
            else:
                raise ValueError(
                    'SamplingMode error! It should be "4G" or "5G"')
        elif name in ['SamplingRate']:
            if value in ['4G']:
                self.srate = 4e9
                self._sampling_mode = 1
            elif value in ['5G']:
                self.srate = 5e9
                self._sampling_mode = 0
            else:
                raise ValueError(
                    'SamplingRate error! It should be "4G" or "5G"')
        elif name in ['Nyquist']:
            if value == 'normal':
                if self._nyquist[ch - 1] in ['mix', None]:
                    self.handle.dac_Nyquist_cfg(chennel_num=ch - 1, Nyquist=0)
                    self._nyquist[ch - 1] = 'normal'
                    time.sleep(0.1)
            elif value == 'mix':
                if self._nyquist[ch - 1] in ['normal', None]:
                    self.handle.dac_Nyquist_cfg(chennel_num=ch - 1, Nyquist=1)
                    self._nyquist[ch - 1] = 'mix'
                    time.sleep(0.1)
            else:
                pass
        elif name in ['TriggerPeriod']:
            periodTime = 16.0 if self._sampling_mode else 12.8
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
        elif name in ['TRIG']:
            self.Trig()
        else:
            super().write(name, value, **kw)

        return value

    def read(self, quant, **kw):
        return super().read(quant, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def Trig(self):
        '''  
           trigger_source 0 为内部触发，1为外部触发
           trigger_us 触发周期单位us; 5Gsps 78.125MHz, 对应12.8ns; 4Gsps 62.5MHz，对应16ns，必须为对应时长的整倍数
           trigger_num 触发次数，当trigger_continue为1时无效
           trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        '''

        ret = self.handle.trigger_ctrl(trigger_source=self._trigger_source,
                                       trigger_us=self._trigger_us,
                                       trigger_num=self._trigger_num,
                                       trigger_continue=self._trigger_continue)
        assert ret == 'ok', 'Error in `Trig()`'

    def writeWaveform(self, data, ch=1, trigger_delay=0, continuous=False):
        data = np.asarray(data).clip(-1, 1)
        data = data * (2**15 - 1)
        data = np.int16(data)

        dac_data = []
        dac_data.append(data)

        replay_cnt = 1
        replay_continue_flag = int(continuous)

        data_point = []
        data_point_i = [0, 0, trigger_delay, replay_cnt, replay_continue_flag]
        data_point.append(data_point_i)

        # self.triggerClose()
        self.handle.dac_updata(ch - 1, dac_data)
        self.handle.dac_point_updata(ch - 1, data_point)

        # if self._trigger_source:
        #     self.Trig()

    def triggerClose(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.trigger_close()
        assert ret == 'ok', 'Error in `triggerClose()`'

    def on(self, ch):  # 打开通道
        slot = self.handle.da_ch[ch - 1][0]
        ch_num = self.handle.da_ch[ch - 1][1]
        ret = self.handle.dac_ch_ctrl(slot=slot,
                                      chennel_num=ch_num,
                                      dac_reset=0,
                                      dac_en=1)
        assert ret == 'ok', 'Error in `on()`'

    def off(self, ch):  # 关闭通道
        slot = self.handle.da_ch[ch - 1][0]
        ch_num = self.handle.da_ch[ch - 1][1]
        ret = self.handle.dac_ch_ctrl(slot=slot,
                                      chennel_num=ch_num,
                                      dac_reset=1,
                                      dac_en=0)
        assert ret == 'ok', 'Error in `off(1)`'
        ret = self.handle.dac_ch_ctrl(slot=slot,
                                      chennel_num=ch_num,
                                      dac_reset=0,
                                      dac_en=0)
        assert ret == 'ok', 'Error in `off(2)`'

    def channel_ip(self):
        return self.handle.dev_id.da
