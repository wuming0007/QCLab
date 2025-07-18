from dev.common.PG import mf_daq
from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,
                        QVector, get_coef)
import numpy as np
from cmath import phase
import logging

log = logging.getLogger(__name__)

# import .mf_board as mf_board


def getExpArray(f_list, numOfPoints, phase_list=None, weight=None, sampleRate=1e9):
    e = []
    t = np.arange(0, numOfPoints, 1) / sampleRate
    if weight is None or len(weight) == 0:
        weight = np.ones(numOfPoints) / numOfPoints
    if phase_list is None or len(phase_list) == 0:
        phase_list = np.zeros_like(f_list)
    for f, phase in zip(f_list, phase_list):
        e.append(weight * np.exp(-1j * (2 * np.pi * f * t + phase)))
    return np.asarray(e).T


def setADALG(ad, f_list, samplesPerFrame, weight=None):
    """设置 AD 硬解模算法
    """
    assert samplesPerFrame % 1024 == 0, "samplesPerFrame 必须为 1024 的整数倍"
    ADSampleRate = 1e9  # Hz
    e = getExpArray(f_list, samplesPerFrame,
                    weight=weight, sampleRate=ADSampleRate)

    ad.write_coef(
        np.moveaxis(np.array([[e.real, e.imag]]), [1, 2, 3], [2, 3, 1]))


def getALGData(ad, f_num):
    ad.get_algData(alg_num=f_num)
    ad.start_sample(0)
    I, Q = ad.alg_iqDataf[0, :, 0, :], ad.alg_iqDataf[0, :, 1, :]
    return I, Q


def getTraces(ad):
    ad.get_Data()
    ad.start_sample(0)
    # i_data/q_data 的形状为（shots, pointNum）
    chA = ad.i_data / 2**15
    chB = ad.q_data / 2**15
    return chA, chB


def getTracesAndALGData(ad, f_num):
    ad.get_Data()
    ad.get_algData(alg_num=f_num)
    ad.start_sample(0)

    chA = ad.i_data / 2**15
    chB = ad.q_data / 2**15

    I, Q = ad.alg_iqDataf[0, :, 0, :], ad.alg_iqDataf[0, :, 1, :]
    return chA, chB, I, Q


class Driver(BaseDriver):

    __log__ = log
    support_models = ['PG_AD']

    CHs = [1]

    quants = [
        QReal('Shot', value=1000, ch=1),
        QInteger('PointNumber', value=2048, ch=1),  # 1024的整数倍
        QList('TriggerDelay', value=0, ch=1),
        QInteger('TriggerType', value=1, ch=1,),
        # daq_core.set_adc_trig_delays([80.35e-6]) #可以设触发延时列表，这里只设一个触发
        # 重复次数

        QBool('avg', value=False, ch=1),
        QList('FrequencyList', value=[50e6], ch=1),
        QVector('IQ', value=[], ch=1),
        QVector('TraceIQ', value=[], ch=1),
        QList('Coefficient', value=None, ch=1),

        # 采集模式：0连续，1触发
        QInteger('StartCapture', value=1, ch=1,),  # 采集模式：0连续，1触发
        QOption('CaptureMode', value=1, ch=1, options=[
                # 采集模式：0连续，1触发
                ('raw', 'raw'), ('alg', 'alg'), ('raw_alg', 'raw_alg')]),

        # 解调频率列表
    ]
    '''
    frame_size: 采集点数；整数；无单位；比如，2048；(等价于pointNum)
    RecordLength: 采集点数除以1024；整数；单位kB；比如，2；(等价于pointNum/1024)
    freq_cnt: 需解调频率个数，最多为10；整数；无单位；比如，5；
    frame_cnt/frameNum: 重复次数；整数；无单位；比如，1000；(等价于shots)
    wave_cnt: ?

    NOTE: 提供的API应在注释里写清楚参数的含义、类型、单位和示例值
    '''

    segment = ('mf', '104|105|106')

    def __init__(self, addr, **kw):
        '''addr: IP'''
        super().__init__(addr, **kw)
        self.model = 'PG_AD'
        self.srate = 1e9

    def open(self, self_test=False):
        daq_core = mf_daq.mf_daq()
        daq_core.connect(self.addr)
        daq_core.clear_udp_buf()  # 清除缓存
        daq_core._reset_ddr()  # 复位DDR
        if self_test:
            _r = daq_core.ddr_self_test()  # DDR自测
            print(_r)
#         daq_core.setTriggerType(1) # 外部触发
#         daq_core.sample_with_false_data(False)
        daq_core.configCapture(
            triggerSource='External',
            triggerEdge='Rising',
            triggerDelay=0,
            frame_cnt=1000,
            Mode='raw',
            frameSize=2,
            isTestData=False)
        self.handle = daq_core

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        self.config[name][ch]['value'] = value
        if name == 'StartCapture':
            self.handle.startCapture()
        elif name == 'CaptureMode':
            self.handle.set_mode(value)
        elif name == 'PointNumber':  # 采样长度
            assert value % 1024 == 0, f'PointNumber ({value}) is not integer multiples of 1024!'
            v = round(value / 1024)  # 1024的倍数
            self.handle.setRecordLength(recordLength=v)
        elif name == 'TriggerDelay':
            self.handle.set_adc_trig_delays([value])
        elif name == 'Shot':
            self.handle.setFrameNumber(frameNum=value)  # 重复次数
        elif name == 'TriggerType':
            self.handle.setTriggerType(value)
        elif name == 'Coefficient':
            self.set_coefficient(value)
        else:
            super().write(name, value, ch=ch, **kw)

        return value

    def read(self, name: str, ch=1, **kw):
        ch = kw.get('ch', 1)
        if name in ['TraceIQ']:
            avg = self.config['avg'][1]['value']
            return self.getTraces(avg=avg, timeout=None)
        elif name in ['IQ']:
            avg = self.config['avg'][1]['value']
            return self.getIQ(avg=avg, timeout=None)
        else:
            return super().read(name, ch=ch, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def set_coefficient(self, coef_info):
        # 根据api要求进行移轴，把I/Q轴移至倒数第二
        data, f_list, numberOfPoints, phase = get_coef(coef_info, self.srate)
        coef_data = np.moveaxis([data.real, data.imag], 0, -2)
        self.setValue('FrequencyList', f_list)
        self.setValue('PointNumber', numberOfPoints)
        self.handle.write_coef(coef_data)
        pass

    def getData(self, fft=False, avg=False, timeout=None):
        if fft:
            f_num = len(self.getValue('FrequencyList'))
            chA, chB = getALGData(self.handle, f_num)
            chA, chB = chA.T, chB.T
        else:
            chA, chB = getTraces(self.handle)
        if avg:
            chA = chA.mean(axis=0)
            chB = chB.mean(axis=0)
        return chA, chB

    def getIQ(self, avg=False, timeout=None):
        return self.getData(True, avg, timeout=timeout)

    def getTraces(self, avg=True, timeout=None):
        return self.getData(False, avg, timeout=timeout)
