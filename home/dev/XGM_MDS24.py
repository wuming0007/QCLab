import time
from typing import Optional

import numpy as np
from waveforms import Waveform

from .common import BaseDriver, QBool, QInteger, QReal, QVector, get_coef
from .common.quantity import QString

# try:
from .common.XGM import mds24 as fpgadev
# except:
#     print('Import fpgadev of DDS ADDA Error!')
from .update_ip import update_ip

XY_SYSTEMQ_VER = 'xy-systemq版本 : V1.1-202500523'


class Driver(BaseDriver):

    support_models = ['XGM_MDS24']

    CHs_num = 24+1

    CHs = list(range(0,CHs_num+1,1))
    
    alg_use = [True]*CHs_num # 八个通道是否使用硬解模
    raw_use = [False]*CHs_num # 八个通道是否使用软解模
    alg_num = [0]*CHs_num  # 硬解模每个通道的频率数目，上限是30

    offset = [0]*CHs_num

    _sampling_mode = None  # 切换DAC采样率 0 为8Gsps, 不支持其它采样率
    _nyquist = [None]*CHs_num
    _trigger_us = 200
    _trigger_num = 1
    _trigger_source = 1  # 0 为内部触发，1为外部触发
    _trigger_continue = 0
    _intrinsic_waveform_length = 65e-6

    quants = [
        # SYSTEM SET
        QVector('Set_dev_ip', ch=1, value=[]),
        QBool('dev_shutdown', ch=1, value=False),
        QBool('dev_reboot', ch=1, value=False),
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
        QString('Trigger', value='on', ch=1),
        QInteger('SamplingRate', ch=1, value=8000),
        QInteger('XY-SamplingRate', ch=1, value=8000),
        QInteger('Z-SamplingRate', ch=1, value=8000),
        QInteger('RO-SamplingRate', ch=1, value=8000),


        # DA
        QReal('Offset', unit='V', ch=1),
        # QReal('Amplitude', unit='VPP', ch=1),
        QInteger('Output', value=1, ch=1),
        QVector('Waveform', value=[], ch=1),
        QBool('WaveformContinue', value=False, ch=1),  # 通道波形是否连续
        QString('Nyquist', value='mix', ch=1),

        # AD
        QReal('FrequencyList', value=[], unit='Hz', ch=1),  # 解调频率
        QReal('PhaseList', value=[], unit='1', ch=1),  # 解调频率
        QInteger('Shot', value=2048, ch=1),  # 利用setValue方法来对重复采样次数设置
        QInteger('PointNumber', value=2048, ch=1),  # 采集点数
        QBool('avg', value=False, ch=1),  # 是否对数据进行平均
        QInteger('Coefficient', value=None, ch=1),  # 解调系数
        QVector('Trace', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QInteger('StartCapture', value=1, ch=1),  # 开始采集模式：0连续，1触发
        # 是否使用硬解模, 'alg' 纯硬解模, 'raw' 纯解模, 'raw_alg' 软硬皆有
        QString('CaptureMode', value='alg', ch=1),
    ]

    def __init__(self, addr, **kw):
        print(XY_SYSTEMQ_VER)
        super().__init__(addr=addr, **kw)
        self.model = 'XGM_MDS24'
        self.handle = fpgadev()
        self.srate = 8e9
        self.srate_xy = 8e9
        self.srate_z = 8e9
        self.srate_ro = 8e9
        self.adc_srate = 2.5e9
        self.system_net = update_ip()
        # print(self.system_net.ip_list)

    def open(self):
        self.triggerClose()
        self.setValue('SamplingRate', 8000)
        for i in range(3):  
            self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = i)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch')

        if name.startswith('Trigger'):
            self.set_TRIG(name, value)
        # if name in ['FrequencyList', 'Coefficient', 'CaptureMode', 'StartCapture','TriggerDelay','PointNumber','Shot','avg']:
        #     if ch > 20 and ch < 25:  # AD
        #         self.set_AD(name, value, ch)
        #     else:
        #         raise ValueError('AD channel number error!!!')

        if name in ['Waveform', 'Output',  'Nyquist' ,  'WaveformContinue']:
            if ch > 0 and ch < 25:  # DA
                self.set_DA(name, value, ch)
            else:
                raise ValueError('DA channel number error!!!')
        elif name in ['SamplingRate']:
            new_sr = round(value/200)*200
            for i in range(3):  
                self.handle.rfdac_sampling(new_sr,i)
            # self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 0)
            # self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 1)
            # self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 2)
            self.srate = new_sr*1e6
            self.srate_xy = new_sr*1e6
            self.srate_z = new_sr*1e6
            self.srate_ro = new_sr*1e6
        elif name in ['XY-SamplingRate']:
            new_sr = round(value/200)*200
            self.handle.rfdac_sampling(new_sr,0)
            self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 0)
            self.srate_xy = new_sr*1e6
        elif name in ['Z-SamplingRate']:
            new_sr = round(value/200)*200
            self.handle.rfdac_sampling(new_sr,1)
            self.handle.rfdac_SetNyquistZone(NyquistZone = 0,board_num = 1)
            self.srate_z = new_sr*1e6
        elif name in ['RO-SamplingRate']:
            new_sr = round(value/200)*200
            self.handle.rfdac_sampling(new_sr,2)
            self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 2)
            self.srate_ro = new_sr*1e6
        elif name in ['Set_dev_ip']:
            print(value)
            self.system_net.set_ip(value[0],value[1],value[2])
        elif name in ['dev_shutdown']:
            if value == True:
                self.system_net.shutdown()
        elif name in ['dev_reboot']:
            if value == True:
                self.system_net.reboot()
        # return 

    def read(self, name: str, **kw):
        ch = kw.get('ch')
        if ch is None:
            ch = 1
        else:
            ch = self.CH_name[ch]
        if name in ['Trace', 'IQ']:
            # if (ch - 1) % 8 == 0 or (ch - 1) % 8 == 1:  # AD
            if name in ['Trace']:
                assert self.raw_use[ch-1], 'Trace is not collected. Please check settings.'
                avg = self.config['avg'][ch]['value']
                return self.getTraces(avg=avg, timeout=None, ch=ch)
            elif name in ['IQ']:
                assert self.alg_use[ch-1], 'IQ is not collected. Please check settings.'
                avg = self.config['avg'][ch]['value']
                return self.get_IQ_alg(avg=avg, timeout=None, ch=ch)
            else:
                return super().read(name, ch=ch, **kw)
            # else:
            #     raise ValueError('AD channel number error!!!')
        
    #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def set_TRIG(self, name, value):
        if name in ['TriggerPeriod']:
            periodTime = 160
            times = round(value * 1e9 / periodTime)
            assert periodTime*times == value * \
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
            continuous = self.config['WaveformContinue'][ch]['value']
            delay = 0
            ch_srate = self.srate_xy

            if isinstance(value, Waveform):
                if np.isinf(value.bounds[0]):
                    delay = 0
                    length = 1e-6
                else:
                    delay = round(value.bounds[0]*ch_srate)/ch_srate
                    length = round((value.bounds[-2]-value.bounds[0])*ch_srate)/ch_srate
                value <<= delay
                value.start, value.stop = 0, length
                value = value.sample(ch_srate)
            # print(delay)
            self.writeWaveform(value, ch=ch, trigger_delay=round(delay*ch_srate), continuous=continuous)
        elif name in ['Output']:
            if value:
                self.on(ch=ch)
            else:
                self.off(ch=ch)
        elif name in ['Nyquist']:
            if value == 'normal':
                if self._nyquist[ch-1] in ['mix', None]:
                    self.handle.rfdac_SetNyquistZone( NyquistZone=0,board_num=int((ch-1)//8))
                    self._nyquist[ch-1] = 'normal'
                    time.sleep(0.1)
            elif value == 'mix':
                if self._nyquist[ch-1] in ['normal', None]:
                    self.handle.rfdac_SetNyquistZone(NyquistZone=1,board_num=int((ch-1)//8))
                    self._nyquist[ch-1] = 'mix'
                    time.sleep(0.1)
            else:
                pass
        # elif name in ['Offset']:
        #     if value <= 1 and value>=-1:
        #         self.offset[ch-1] = value
        #         self.handle.set_ch_offset(ch-1, value)
        #     else:
        #         return 'The setting voltage is too high!!!'
        elif name in ['WaveformContinue']:
            self.config['WaveformContinue'][ch]['value'] = value

    def set_AD(self, name, value, ch):
        """ch starts from 1
        """
        if name in ['Coefficient', ]:

            assert len(value) in range(1, 17), f'Invalid coefficient number of frequencies.'
            f_list = []
            phases = []
            for i in range(len(value)):
                f_list.append(value[i]['Delta'])
                phases.append(value[i]['Phase'])
            self.config['FrequencyList'][ch]['value'] =  f_list #list(np.fmod(np.fmod(-np.array(f_list), self.adc_srate)+self.adc_srate, self.adc_srate)) #f_list 
            self.config['PhaseList'][ch]['value'] =  phases #ist(np.fmod(np.fmod(-np.array(phases), np.pi*2)+np.pi*2, np.pi*2)) #phases

        elif name in ['CaptureMode']:
            assert value in ['alg', 'raw',
                             'raw_alg'], f'Other mode is not supported.'
            self.alg_use[ch-1] = (value != 'raw')
            self.raw_use[ch-1] = (value != 'alg')
        elif name in ['StartCapture']:
            self.start_capture(ch=ch)
        elif name in ['TriggerDelay']:
            self.config['TriggerDelay'][ch]['value'] = value
        elif name in ['PointNumber']:
            self.config['PointNumber'][ch]['value'] = value
        elif name in ['Shot']:
            self.config['Shot'][ch]['value'] = value
        elif name in ['avg']:
            self.config['avg'][ch]['value'] = value

    def writeWaveform(self, data, ch=1, trigger_delay=0, continuous=False):
        data = np.asarray(data).clip(-1, 1)

        data_len = len(data)
        if data_len > 2**19:
            print('write dac data too long !!!')
            return 'write dac data too long !!!'

        replay_cnt = 100000000
        replay_continue_flag = int(continuous)

        self.triggerClose()
        self.handle.dac_updata(ch-1, trigger_delay, replay_cnt, replay_continue_flag, data)

        # if self._trigger_source:
        self.Trig()

    def on(self, ch):  # 打开通道
        ret = self.handle.dac_open(ch-1)

        assert ret == 'ok', 'Error in `on()`'

    def off(self, ch):  # 关闭通道
        ret = self.handle.dac_close(ch-1)
        assert ret == 'ok', 'Error in `off(2)`'

    def channel_ip(self):
        return self.handle.dev_id.da

    def triggerClose(self):
        '''
        该函数用于关闭触发器
        '''
        ret = self.handle.trigger_close()
        assert ret == 'ok', 'Error in `triggerClose()`'

    def start_capture(self,ch=1):
        self.triggerClose()
        self._adc_control(ch=ch, enable=1)
        self.Trig()

    def _adc_control(self, ch=1, enable=1):

        
        trigger_delay = round(
            self.config['TriggerDelay'][ch]['value']*self.adc_srate)

        save_len = int(round(self.config['PointNumber'][ch]['value']*self.adc_srate))
        times = self.config['Shot'][ch]['value']

        if self.raw_use[ch-1] == True:
            ret = self.handle.rd_adc_data_ctrl(ch-21, trigger_delay, times, save_len)
        elif self.alg_use[ch-1] == True:
            f_list = self.config['FrequencyList'][ch]['value']
            phase_list  = self.config['PhaseList'][ch]['value']
            self.alg_num[ch-1] = len(f_list)
            mul_f = []
            for i in range((len(phase_list))):
                mul_f_i = []
                mul_f_i.append(phase_list[i])
                mul_f_i.append(f_list[i])
                mul_f.append(mul_f_i)

            ret = self.handle.rd_adc_mul_data_ctrl(ch-21, trigger_delay, times,save_len, mul_f)
            


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
        save_len = int(round(self.config['PointNumber'][ch]['value']*self.adc_srate))
        times = self.config['Shot'][ch]['value']
        # print('xxxxxxxxxxxxxxxxxxxxxxxx')
        # print(save_len,times)
        if save_len > 2**17:
            return 'adc save data too long !!!'

        while 1:
            adc_data_buf, adc_data_save_len = self.handle.rd_adc_data(ch-21, times, save_len)
            if adc_data_save_len != -1:
                break
            else:
                time1 = time.time()
                if time1-time0 > (self.timeout if timeout is None else timeout):
                    raise Exception('rd_adc_data_return timeout!')

        return adc_data_buf
        # return adc_data_buf, np.zeros_like(adc_data_buf)

    def getTraces(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None):
        cha = self.get_data(ch=ch, timeout=timeout)
        times = self.config['Shot'][ch]['value']
        if avg:
            # return cha/times, chb/times
            return cha/times
        else:
            # return cha, chb
            return cha

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

        assert self.alg_num[ch-1] > 0, 'Hard demod coefficient is not set.'

        adc_data = []
        for modle_num in range(self.alg_num[ch-1]):
            # print('modle_num',modle_num)
            while 1:
                mul_data_bufe, read_data_len = self.handle.rd_adc_mul_data(ch-21, modle_num, times)
                if read_data_len != -1:
                    break
            adc_data.append(mul_data_bufe)
            # adc_data.append(mul_data_bufe/(2**17-1))

        adc_data = np.asarray(adc_data).T
        return np.real(adc_data), np.imag(adc_data)

    def get_IQ_alg(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None):
        I, Q = self.get_data_alg(ch=ch, timeout=timeout)

        if avg:
            return np.mean(I, axis=0), np.mean(Q, axis=0)
        else:
            return I, Q
    
