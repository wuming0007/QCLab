import time
from typing import Optional

import numpy as np

from dev.common import (BaseDriver, QBool, QInteger, QList, QReal, QString,
                        QVector, get_coef)
from dev.common import newcfg

try:
    from dev.common.DDS_LH import ddsx86_ad
except:
    print('Import fpgadev of AD_DEV Error!')


class Driver(BaseDriver):
    support_models = ['LH_DDS_x86AD']

    CHs_num = 12

    CHs = []

    _sampling_mode = None  # 切换采样率 0 为5Gsps；1 为4Gsps

    alg_use = []  # 四个通道是否使用硬解模
    raw_use = []  # 四个通道是否使用软解模
    alg_num = []  # 硬解模每个通道的频率数目，上限是12

    _trigger_source = 1
    _trigger_us = 200
    _trigger_num = 1
    _trigger_continue = 0

    _data_cache = {}

    quants = [
        QReal('FrequencyList', value=[], unit='Hz', ch=1),  # 解调频率
        QInteger('TriggerDelay', value=0, unit='s',
                 ch=1),  # 利用setValue方法来对采样延迟点数设置
        QInteger('Shot', value=2048, ch=1),  # 利用setValue方法来对重复采样次数设置
        QInteger('PointNumber', value=2048, ch=1),  # 采集点数
        QBool('avg', value=False, ch=1),  # 是否对数据进行平均
        QList('Coefficient', value=None, ch=1),  # 解调系数
        QString('SamplingMode', ch=1, value='5G'),
        QString('SamplingRate', ch=1, value='5G'),
        QVector('TraceIQ', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QInteger('TriggerType', value=0, ch=1),  # 是否连续触发, 1 连续触发, 0 不连续触发
        QInteger('TriggerSource', value=1, ch=1),  # 触发源, 1 外部触发, 0, 内部触发
        QInteger('StartCapture', value=1, ch=1),  # 开始采集模式：0连续，1触发
        # 是否使用硬解模, 'alg' 纯硬解模, 'raw' 纯解模, 'raw_alg' 软硬皆有
        QString('CaptureMode', value='alg', ch=1),

        # 超前测试用
        QInteger('Classify', value=0, ch=1),
        QVector('Counts', value=[], ch=1)
    ]

    segment = ('lh', '107|108|109')

    def __init__(self, addr, **kw):
        super().__init__(addr=addr, timeout=10, **kw)
        self.model = 'LH_DDS_x86AD'

    def open(self):

        self.handle = ddsx86_ad()

        self.CHs = list(range(1, 1 + self.CHs_num))
        self.alg_use = [True] * self.CHs_num
        self.raw_use = [False] * self.CHs_num
        self.alg_num = [0] * self.CHs_num

        self.phi, self.threshold = {}, {}
        for i in range(self.CHs_num):
            self.phi[i + 1], self.threshold[i + 1] = None, None

        self.config = newcfg(self.quants, self.CHs)

        self.triggerClose()
        # self.setValue('SamplingMode', '5G', ch=1)
        # for ch in self.CHs:
        #     self.channel_reset(ch=ch)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)

        if name in [
                'Coefficient',
        ]:
            data, f_list, numberOfPoints, phases = get_coef(value, self.srate)
            assert len(f_list) in range(
                1, 20), f'Invalid coefficient number of frequencies.'
            # self.setValue('PointNumber',numberOfPoints,ch=ch)
            # self.update('PointNumber',numberOfPoints,ch=ch)
            self.config['PointNumber'][ch]['value'] = numberOfPoints
            assert numberOfPoints <= 16384, f'Maximum points exceeded hard demod limit.'
            self.set_coefficient(ch=ch, value=data)
            if value.get('wList', {}).get('phi', None) is not None:
                self.phi[ch] = np.array([kw['phi'] for kw in value['wList']])
                self.threshold[ch] = np.array(
                    [kw['threshold'] for kw in value['wList']])
        elif name in ['SamplingMode']:
            if value in ['4G']:
                if self._sampling_mode in [None, 0]:
                    self._sampling_mode = 1
                    self.handle.system_sampling(
                        sampling=self._sampling_mode, step=0, self_set=1)
                    self.srate = 2e9
                    time.sleep(1)
            elif value in ['5G']:
                if self._sampling_mode in [None, 1]:
                    self._sampling_mode = 0
                    self.handle.system_sampling(
                        sampling=self._sampling_mode, step=0, self_set=1)
                    self.srate = 2.5e9
                    time.sleep(1)
            else:
                raise ValueError(
                    'SamplingMode/Frequency error! It should be "4G" or "5G"')
        elif name in ['SamplingRate']:
            if value in ['4G']:
                self.srate = 2e9
            elif value in ['5G']:
                self.srate = 2.5e9
            else:
                raise ValueError(
                    'SamplingRate error! It should be "4G" or "5G"')
        elif name in ['CaptureMode']:
            assert value in ['alg', 'raw',
                             'raw_alg'], f'Other mode is not supported.'
            self.alg_use[ch - 1] = (value != 'raw')
            self.raw_use[ch - 1] = (value != 'alg')
        elif name in ['StartCapture']:
            self._data_cache = {}
            self.start_capture()
        elif name in ['TriggerType']:
            self._trigger_continue = value
        elif name in ['TriggerSource']:
            self._trigger_source = value

        return value

    def read(self, name: str, **kw):
        ch = kw.get('ch', 1)
        if name in ['TraceIQ']:
            assert self.raw_use[
                ch - 1], 'Trace is not collected. Please check settings.'
            avg = self.config['avg'][ch]['value']
            classfy = self.config['Classify'][ch]['value']
            return self.getTraces(avg=avg or ((classfy & 137) == 137), timeout=None, ch=ch)
        elif name in ['IQ']:
            assert self.alg_use[
                ch - 1], 'IQ is not collected. Please check settings.'
            avg = self.config['avg'][ch]['value']
            classfy = self.config['Classify'][ch]['value']
            data = self.get_IQ_alg(avg=avg or (
                (classfy & 146) == 146), timeout=None, ch=ch)
            if (classfy & 132) == 132:
                state = ((data[0] + 1j * data[1]) * np.exp(-1j *
                         self.phi[ch])).real > self.threshold[ch]
                if (classfy & 196) == 196:
                    self._data_cache[ch] = state
                    return np.zeros([self.alg_num[ch - 1]])
                elif (classfy & 164) == 164:
                    return state.mean(axis=-2)
                return state
            return data
        elif name in ['Counts']:
            shots = self.config['Shot'][ch]['value']
            order = [int(item[2:]) for item in sorted(
                [f'CH{i}' for i in self._data_cache.keys()])]
            ret = {}
            for i in range(shots):
                count_state = np.concatenate(
                    tuple(self._data_cache[j][i] for j in order))
                ret_key = tuple(int(state) for state in count_state)
                ret[ret_key] = ret.get(ret_key, 0) + 1
            return ret
        else:
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def triggerClose(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.trigger_close()
        assert ret == 'ok', 'Error in `triggerClose()`'

    def channel_reset(self, ch=1, reset=1):
        """
        通道复位

        Args:
            ch (int, optional): 通道编号. Defaults to 1.
            reset (int, optional): 复位信息，1复位，0取消复位（即正常）. Defaults to 1.
        """
        ret = self.handle.adc_modle_reset(ch - 1, reset)
        assert ret == 'ok', f'Error in `channel_reset({ch})`'

    def _adc_control(self, ch=1, enable=1):

        trigger_delay = round(self.config['TriggerDelay'][ch]['value'] *
                              self.srate)
        save_len = self.config['PointNumber'][ch]['value']
        times = self.config['Shot'][ch]['value']

        raw_model_en = int(enable and self.raw_use[ch - 1])
        alg_model_en = int(enable and self.alg_use[ch - 1])

        for modle_num in range(self.alg_num[ch - 1]):
            ret = self.handle.rd_adc_mul_data_ctrl(ch - 1,
                                                   modle_en=alg_model_en,
                                                   modle_num=modle_num,
                                                   trigger_delay=trigger_delay,
                                                   times=times,
                                                   save_len=save_len)
            assert ret == 'ok', f'Error in `_adc_control({ch})` and alg number {modle_num}'

        ret = self.handle.rd_adc_data_ctrl(ch - 1,
                                           modle_en=raw_model_en,
                                           trigger_delay=trigger_delay,
                                           times=times,
                                           save_len=save_len)
        assert ret == 'ok', f'Error in `_adc_control({ch}) all`'

    def Trig(self):
        '''  
           trigger_source 0 为内部触发，1为外部触发
           trigger_us 触发周期单位us; 5Gsps 78.125MHz, 对应12.8ns; 4Gsps 62.5MHz，对应16ns，必须为对应时长的整倍数
           trigger_num 触发次数，当trigger_continue为1时无效
           trigger_continue 1 为连续触发模式，此时触发次数无效；0 为按触发次数触发。
        '''

        ret = self.handle.trigger_ctrl(
            trigger_source=self._trigger_source,
            trigger_us=self._trigger_us,
            trigger_num=self._trigger_num,
            trigger_continue=self._trigger_continue)
        assert ret == 'ok', 'Error in `Trig()`'

    def set_coefficient(self, value, ch: int = 1):
        """
        系数格式, array[frequency number, points]

        Args:
            value ([type]): [description]
            ch (int, optional): [description]. Defaults to 1.
        """

        self.triggerClose()

        self.channel_reset(ch=ch)
        self.channel_reset(ch=ch, reset=0)

        self.alg_num[ch - 1] = value.shape[0]

        value = value * (2**13 - 1)

        for modle_num in range(value.shape[0]):
            generate_data = [
                np.int16(np.real(value[modle_num])),
                np.int16(np.imag(value[modle_num]))
            ]
            self.handle.adc_mul_data_wr(ch - 1,
                                        modle_num=modle_num,
                                        generate_data=generate_data)

    def start_capture(self):
        self.triggerClose()
        for ch in self.CHs:
            self.channel_reset(ch=ch)
            self._adc_control(ch=ch, enable=1)
            self.channel_reset(ch=ch, reset=0)
        self.Trig()

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
                if time1 - time0 > (self.timeout
                                    if timeout is None else timeout):
                    raise Exception('rd_adc_data_return timeout!')

        return np.asarray(adc_data_bufe), np.zeros_like(adc_data_bufe)

    def getTraces(self,
                  avg: bool = False,
                  ch: int = 1,
                  timeout: Optional[float] = None):
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
        """ """"""

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
                    if time1 - time0 > (self.timeout
                                        if timeout is None else timeout):
                        raise Exception('rd_adc_data_return timeout!')
            adc_data.append(adc_data_bufe)

        adc_data = np.asarray(adc_data).T
        return np.real(adc_data), np.imag(adc_data)

    def get_IQ_alg(self,
                   avg: bool = False,
                   ch: int = 1,
                   timeout: Optional[float] = None):
        I, Q = self.get_data_alg(ch=ch, timeout=timeout)
        if avg:
            return np.mean(I, axis=0), np.mean(Q, axis=0)
        else:
            return I, Q
