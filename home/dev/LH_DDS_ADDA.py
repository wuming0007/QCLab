import time
from typing import Optional

import numpy as np

from dev.common import BaseDriver, QBool, QInteger, QReal, QVector, get_coef, QString

# try:
from dev.common.DDS_LH import adda_fpgadev as fpgadev
# except:
#     print('Import fpgadev of DDS ADDA Error!')


class Driver(BaseDriver):

    support_models = ['LH_DDS_DA']

    CHs_num = 12

    CHs = list(range(1, CHs_num + 1, 1))

    alg_use = [True] * CHs_num  # 四个通道是否使用硬解模
    raw_use = [False] * CHs_num  # 四个通道是否使用软解模
    alg_num = [0] * CHs_num  # 硬解模每个通道的频率数目，上限是12

    _sampling_mode = None  # 切换采样率 0 为5Gsps；1 为4Gsps
    _nyquist = [None] * CHs_num
    _trigger_us = 200
    _trigger_num = 1
    _trigger_source = 1  # 0 为内部触发，1为外部触发
    _trigger_continue = 0

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
        QString('SamplingMode', ch=1, value='5G'),

        # DA
        QReal('Offset', unit='V', ch=1),
        QReal('Amplitude', unit='VPP', ch=1),
        QInteger('Output', value=1, ch=1),
        QVector('Waveform', value=[], ch=1),
        QBool('WaveformContinue', value=False, ch=1),  # 通道波形是否连续
        QString('Nyquist', value='mix', ch=1),

        # AD
        QReal('FrequencyList', value=[], unit='Hz', ch=1),  # 解调频率
        QInteger('Shot', value=2048, ch=1),  # 利用setValue方法来对重复采样次数设置
        QInteger('PointNumber', value=2048, ch=1),  # 采集点数
        QBool('avg', value=False, ch=1),  # 是否对数据进行平均
        QInteger('Coefficient', value=None, ch=1),  # 解调系数
        QVector('TraceIQ', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QInteger('StartCapture', value=1, ch=1),  # 开始采集模式：0连续，1触发
        # 是否使用硬解模, 'alg' 纯硬解模, 'raw' 纯解模, 'raw_alg' 软硬皆有
        QString('CaptureMode', value='alg', ch=1),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'LH_DDS_ADDA'
        self.handle = fpgadev(addr)
        self.srate = 5e9

    def open(self):
        self.triggerClose()
        self.setValue('SamplingMode', '5G')

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)

        if name.startswith('Trigger'):
            self.set_TRIG(name, value)

        if name in ['SamplingMode']:
            if value in ['4G']:
                if self._sampling_mode in [None, 0]:
                    self._sampling_mode = 1
                    self.handle.system_sampling(sampling=self._sampling_mode)
                    self.srate = 4e9
                    time.sleep(1)
            elif value in ['5G']:
                if self._sampling_mode in [None, 1]:
                    self._sampling_mode = 0
                    self.handle.system_sampling(sampling=self._sampling_mode)
                    self.srate = 5e9
                    time.sleep(1)
            else:
                raise ValueError(
                    'SamplingMode/Frequency error! It should be "4G" or "5G"')

        if name in ['FrequencyList', 'Coefficient', 'CaptureMode', 'StartCapture']:
            if (ch - 1) % 4 == 0 or (ch - 1) % 4 == 1:  # AD
                self.set_AD(name, value, ch)
            else:
                raise ValueError('AD channel number error!!!')

        if name in ['Waveform', 'Output', 'Nyquist']:
            if (ch - 1) % 4 == 2 or (ch - 1) % 4 == 3:  # DA
                self.set_DA(name, value, ch)
            else:
                raise ValueError('DA channel number error!!!')

        return value

    def read(self, name: str, **kw):
        ch = kw.get('ch', 1)
        if name in ['TraceIQ', 'IQ']:
            if (ch - 1) % 4 == 0 or (ch - 1) % 4 == 1:  # AD
                if name in ['TraceIQ']:
                    assert self.raw_use[ch -
                                        1], 'Trace is not collected. Please check settings.'
                    avg = self.config['avg'][ch]['value']
                    return self.getTraces(avg=avg, timeout=None, ch=ch)
                elif name in ['IQ']:
                    assert self.alg_use[ch -
                                        1], 'IQ is not collected. Please check settings.'
                    avg = self.config['avg'][ch]['value']
                    return self.get_IQ_alg(avg=avg, timeout=None, ch=ch)
                else:
                    return super().read(name, ch=ch, **kw)
            else:
                raise ValueError('AD channel number error!!!')

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def set_TRIG(self, name, value):
        if name in ['TriggerPeriod']:
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
        elif name in ['Trigger']:
            self.Trig()

    def Trig(self):
        '''  
           trigger_source 0 为内部触发，1为外部触发
           trigger_us 触发周期单位us; 5Gsps 78.125MHz, 对应12.8ns; 4Gsps 62.5MHz，对应16ns，必须为对应时长的整倍数
           trigger_num 触发次数，当trigger_continue为1时无效
           trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        '''

        ret = self.handle.dac_trigger_ctrl(trigger_source=self._trigger_source,
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
                    self.handle.dac_Nyquist_cfg(
                        dac_chennel_in=ch - 1, Nyquist=0)
                    self._nyquist[ch - 1] = 'normal'
                    time.sleep(0.1)
            elif value == 'mix':
                if self._nyquist[ch - 1] in ['normal', None]:
                    self.handle.dac_Nyquist_cfg(
                        dac_chennel_in=ch - 1, Nyquist=1)
                    self._nyquist[ch - 1] = 'mix'
                    time.sleep(0.1)
            else:
                pass

    def set_AD(self, name, value, ch):
        """ch starts from 1
        """
        if name in ['Coefficient', ]:
            data, f_list, numberOfPoints, phases = get_coef(
                value, self.srate / 2)
            assert len(f_list) in range(
                1, 13), f'Invalid coefficient number of frequencies.'
            self.config['PointNumber'][ch]['value'] = numberOfPoints
            if self.alg_use[ch - 1]:
                assert numberOfPoints <= 16384, f'Maximum points exceeded hard demod limit.'
                self.set_coefficient(data, ch=ch)
        elif name in ['CaptureMode']:
            assert value in ['alg', 'raw',
                             'raw_alg'], f'Other mode is not supported.'
            self.alg_use[ch - 1] = (value != 'raw')
            self.raw_use[ch - 1] = (value != 'alg')
        elif name in ['StartCapture']:
            self.start_capture(ch=ch)

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

        self.triggerClose()
        self.handle.dac_updata(ch - 1, dac_data)
        self.handle.dac_point_updata(ch - 1, data_point)

        if self._trigger_source:
            self.Trig()

    def on(self, ch):  # 打开通道
        ret = self.handle.dac_ch_ctrl(
            slot_dac=self.handle.dev_id.da[((ch - 1) // 4) * 2 + (ch - 1) % 2], dac_reset=0, dac_en=1)
        assert ret == 'ok', 'Error in `on()`'

    def off(self, ch):  # 关闭通道
        ret = self.handle.dac_ch_ctrl(
            slot_dac=self.handle.dev_id.da[ch - 1], dac_reset=1, dac_en=0)
        assert ret == 'ok', 'Error in `off(1)`'
        ret = self.handle.dac_ch_ctrl(
            slot_dac=self.handle.dev_id.da[ch - 1], dac_reset=0, dac_en=0)
        assert ret == 'ok', 'Error in `off(2)`'

    def channel_ip(self):
        return self.handle.dev_id.da

    def set_coefficient(self, value, ch: int = 1):
        """
        系数格式, array[frequency number, points]

        Args:
            value ([type]): [description]
            ch (int, optional): [description]. Defaults to 1.
        """

        self.triggerClose()

        self.channel_reset(ch=ch, reset=1)

        self.alg_num[ch - 1] = value.shape[0]

        value = value * (2**13 - 1)

        for modle_num in range(value.shape[0]):
            generate_data = [np.int16(np.real(value[modle_num])), np.int16(
                np.imag(value[modle_num]))]
            self.handle.adc_mul_data_wr(
                ch - 1, modle_num=modle_num, generate_data=generate_data)
        self.channel_reset(ch=ch, reset=0)

    def channel_reset(self, ch=1, reset=1):
        """
        通道复位

        Args:
            ch (int, optional): 通道编号. Defaults to 1.
            reset (int, optional): 复位信息，1复位，0取消复位（即正常）. Defaults to 1.
        """
        ret = self.handle.adc_modle_reset(ch - 1, reset)
        assert ret == 'ok', f'Error in `channel_reset({ch})`'

    def triggerClose(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.dac_trigger_close()
        assert ret == 'ok', 'Error in `triggerClose()`'

    def start_capture(self, ch=1):
        self.triggerClose()
        self.channel_reset(ch=ch)
        self._adc_control(ch=ch, enable=1)
        self.channel_reset(ch=ch, reset=0)
        self.Trig()

    def _adc_control(self, ch=1, enable=1):

        trigger_delay = round(
            self.config['TriggerDelay'][ch]['value'] * self.srate / 2)
        save_len = self.config['PointNumber'][ch]['value']
        times = self.config['Shot'][ch]['value']

        raw_model_en = int(enable and self.raw_use[ch - 1])
        alg_model_en = int(enable and self.alg_use[ch - 1])

        for modle_num in range(self.alg_num[ch - 1]):
            ret = self.handle.rd_adc_mul_data_ctrl(ch - 1,
                                                   modle_en=alg_model_en, modle_num=modle_num, trigger_delay=trigger_delay,
                                                   times=times, save_len=save_len)
            assert ret == 'ok', f'Error in `_adc_control({ch})` and alg number {modle_num}'

        ret = self.handle.rd_adc_data_ctrl(ch - 1,
                                           modle_en=raw_model_en, trigger_delay=trigger_delay, times=times, save_len=save_len)

        assert ret == 'ok', f'Error in `_adc_control({ch}) all`'

    def get_data(self, ch: int = 1, timeout: Optional[float] = None):
        """
        shape in [shots, pointNum].

        默认触发相关设置已经配置好，只是从卡中读取采集的数据。

        Args:
            ch (int, optional): id of channel. Defaults to 1.

        Raises:
            Exception: rd_adc_data_return timeout!

        Returns:
            np.ndarray, np.ndarray: I, Q in the shape
        """

        time0 = time.time()
        save_len = self.config['PointNumber'][ch]['value']
        times = self.config['Shot'][ch]['value']

        while 1:
            adc_data_bufe, data_len = self.handle.rd_adc_data(
                ch - 1, times, save_len)
            if data_len != -1:
                break
            else:
                time1 = time.time()
                if time1 - time0 > (self.timeout if timeout is None else timeout):
                    raise Exception('rd_adc_data_return timeout!')

        return np.asarray(adc_data_bufe), np.zeros_like(adc_data_bufe)

    def getTraces(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None):
        cha, chb = self.get_data(ch=ch, timeout=timeout)
        if avg:
            return np.mean(cha, axis=0), np.mean(chb, axis=0)
        else:
            return cha, chb

    def get_data_alg(self, ch: int = 1, timeout: Optional[float] = None):
        """
        shape in [shots, number of demod frequency].

        Args:
            avg (bool, optional): [description]. Defaults to True.
            ch (int, optional): [description]. Defaults to 1.

        Raises:
            Exception: [description]

        Returns:
            [type]: [description]
        """        """"""

        time0 = time.time()
        times = self.config['Shot'][ch]['value']

        assert self.alg_num[ch - 1] > 0, 'Hard demod coefficient is not set.'

        adc_data = []

        for modle_num in range(self.alg_num[ch - 1]):
            while 1:
                adc_data_bufe, data_len = self.handle.rd_adc_mul_data(
                    ch - 1, modle_num=modle_num, times=times)
                if data_len != -1:
                    break
                else:
                    time1 = time.time()
                    if time1 - time0 > (self.timeout if timeout is None else timeout):
                        raise Exception('rd_adc_data_return timeout!')
            adc_data.append(adc_data_bufe)

        adc_data = np.asarray(adc_data).T
        return np.real(adc_data), np.imag(adc_data)

    def get_IQ_alg(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None):
        I, Q = self.get_data_alg(ch=ch, timeout=timeout)
        if avg:
            return np.mean(I, axis=0), np.mean(Q, axis=0)
        else:
            return I, Q
