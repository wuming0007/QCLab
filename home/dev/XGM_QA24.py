import time
from typing import Optional

import numpy as np
from waveforms import Waveform
import numpy as np
from waveforms import Waveform, wave_eval
from waveforms.math.signal import getFTMatrix, shift

from .common import BaseDriver, QBool, QInteger, QReal, QVector
from .common.quantity import QString

# try:
from .common.XGM import qa24 as fpgadev
# except:
#     print('Import fpgadev of DDS ADDA Error!')
from .update_ip import update_ip

QA_SYSTEMQ_VER = 'qa-systemq版本 : V1.1-20250523'

def new_round(_float, _len):
    '''
    四舍五入保留小数位，如果想实现 0.2 显示为 0.20，可使用 '%.2f' % num 实现
    :param _float:
    :param _len: 保留的小数位
    :return:
    '''
    _float=float(_float)
    if len(str(_float).split('.')[1])<= _len:
        return round(_float, _len)
    elif str(_float)[-1] == '5':
        return round(float(str(_float)[:-1] + '6'), _len)
    else:
        return round(_float, _len)

def get_coef(coef_info, sampleRate):
    start, stop = coef_info['start'], coef_info['stop']
    numberOfPoints = int(
        (stop - start) * sampleRate)
    if numberOfPoints % 1024 != 0:
        numberOfPoints = numberOfPoints + 1024 - numberOfPoints % 1024
    t = np.arange(numberOfPoints) / sampleRate + start

    fList = []
    wList = []
    phases = []
    steds = []
    phi = []

    for kw in coef_info['wList']:
        Delta, t0, weight, w, phase,phase_s = kw['Delta'], kw['t0'], kw['weight'], kw['w'], kw['phase'], kw['phi']
        fList.append(Delta)
        phi.append(phase_s)
        
        if w is not None:
            w = np.zeros(numberOfPoints, dtype=complex)
            w[:len(w)] = w
            w = shift(w, t0 - start)
            phases.append(np.mod(phase + 2 * np.pi * Delta * start, 2*np.pi))
        else:
            weight = weight
            if isinstance(weight, np.ndarray):
                pass
            else:
                if isinstance(weight, str):
                    fun = wave_eval(weight) >> t0
                elif isinstance(weight, Waveform):
                    fun = weight >> t0
                else:
                    raise TypeError(f'Unsupported type {weight}')
                weight = fun(t)
            steds.append([fun.bounds[0], fun.bounds[-2]])
            phase += 2 * np.pi * Delta * start
#             w = getFTMatrix([Delta],
#                             numberOfPoints,
#                             phaseList=[phase],
#                             weight=weight,
#                             sampleRate=sampleRate)[:, 0]
            phases.append(np.mod(phase, 2*np.pi))
        wList.append(w)
    ffs = np.unique(fList)
    phis = [[] for f in ffs]
    ffs_num = 0
    # for i in range(len(fList)):
    #     if ffs[ffs_num] == fList[i]:
    #         phis[ffs_num] = phi[i]
    #         ffs_num += 1
    #         if ffs_num == len(ffs):
    #             break
    ffs[0] = fList[0]
    phis[0] = phi[0]
    f_now = fList[0]
    phi_now = phi[0]
    
    for i in range(len(fList)):
        
        if f_now != fList[i]:
            f_now = fList[i]
            phi_now = phi[i]
            ffs_num += 1
            ffs[ffs_num] = f_now
            phis[ffs_num] = phi_now
        if ffs_num == len(ffs)-1:
            break
    
    new_fList, new_sted, rnks = [], [[] for f in ffs], [[] for f in ffs]
    for i, freq in enumerate(fList):
        for ind in range(len(ffs)):
            if ffs[ind] == freq:
                break
        # ind = np.searchsorted(ffs, freq)

        new_sted[ind].append(np.round(np.array(steds[i])*sampleRate))
        rnks[ind].append(i)
    return np.asarray(wList), ffs,phis, numberOfPoints, phases, new_sted, rnks


class Driver(BaseDriver):

    support_models = ['XGM_MDS24']

    CHs_num = 24

    CHs = list(range(1,CHs_num+1,1))

    alg_use = [True]*CHs_num # 八个通道是否使用硬解模
    raw_use = [False]*CHs_num # 八个通道是否使用软解模
    alg_num = [0]*CHs_num  # 硬解模每个通道的频率数目，上限是30

    _sampling_mode = None  # 切换DAC采样率 0 为8Gsps, 不支持其它采样率
    _nyquist = [None]*CHs_num
    _data_mixtype = None #normal为正常回放不插值，其他为插值，mix_p1 插值乘1,mix_0 插值乘0,mix_n1 插值乘-1
    _trigger_us = 200
    _trigger_num = 1
    _trigger_source = 1  # 0 为内部触发，1为外部触发
    _trigger_continue = 0
    _intrinsic_waveform_length = 65e-6
    _trigger_delay_sub = [0]*CHs_num

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
        QReal('StartDelay', value=0, unit='s', ch=1,),
        
        QInteger('Trigger', value=0, ch=1),
        QInteger('SamplingRate', ch=1, value=8000),
        QInteger('XY-SamplingRate', ch=1, value=8000),
        QInteger('Z-SamplingRate', ch=1, value=8000),
        QInteger('RO-SamplingRate', ch=1, value=8000),

        # DA
        # QReal('Offset', unit='V', ch=1),
        # QReal('Amplitude', unit='VPP', ch=1),
        QInteger('Output', value=1, ch=1),
        QVector('Waveform', value=[], ch=1),
        QVector('Pulse', value=[], ch=1),
        QBool('WaveformContinue', value=False, ch=1),  # 通道波形是否连续
        QString('Nyquist', value='mix', ch=1),
        QString('Data_mixtype', value='normal', ch=1),#回放波形数据补偿类型

        # AD
        QReal('FrequencyList', value=[], unit='Hz', ch=1),  # 解调频率
        QReal('PhaseList', value=[], unit='1', ch=1),  # 解调频率
        QReal('Delta_PhaseList', value=[], unit='1', ch=1),  # 解调频率
        QInteger('Shot', value=2048, ch=1),  # 利用setValue方法来对重复采样次数设置
        QInteger('PointNumber', value=2048, ch=1),  # 采集点数
        QBool('avg', value=False, ch=1),  # 是否对数据进行平均
        QInteger('Coefficient', value=None, ch=1),  # 解调系数
        QVector('TraceIQ', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QVector('Sample_time', value=[], ch=1), #采集时刻
        QVector('rnks', value=[], ch=1), #解模重排系数
        QInteger('StartCapture', value=1, ch=1),  # 开始采集模式：0连续，1触发
        # 是否使用硬解模, 'alg' 纯硬解模, 'raw' 纯解模, 'raw_alg' 软硬皆有
        QString('CaptureMode', value='alg', ch=1),
    ]

    def __init__(self, addr, **kw):
        print(QA_SYSTEMQ_VER)
        super().__init__(addr=addr, **kw)
        self.model = 'XGM_MDS24'
        self.handle = fpgadev()
        self._data_mixtype = 'normal'
        self.srate = 8e9
        self.adc_srate = 2.5e9
        self.system_net = update_ip()
       

    def open(self):
        # self.triggerClose()
        # self.setValue('Data_mixtype', 'mix_p1')
        self.setValue('SamplingRate', 8000)
        for i in range(3):  
            self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = i)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)

        if name.startswith('Trigger'):
            self.set_TRIG(name, value)
        
        if name in ['Coefficient','CaptureMode','StartCapture','TriggerDelay','PointNumber','Shot','avg' ]:
            if ch > 12 and ch < 25:  # AD
                self.set_AD(name, value, ch)
            else:
                raise ValueError('AD channel number error!!!')
            
        if name in ['Pulse']:
            print(value,'qiskit pulse test')

        if name in ['Waveform', 'Output',  'Nyquist','WaveformContinue']:
            if ch > 0 and ch < 13:  # DA
                self.set_DA(name, value, ch)
            else:
                raise ValueError('DA channel number error!!!')
        if name in ['SamplingRate']:
            new_sr = round(value/200)*200
            for i in range(3):  
                self.handle.rfdac_sampling(new_sr,i)
            # self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 0)
            # self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 1)
            # self.handle.rfdac_SetNyquistZone(NyquistZone = 1,board_num = 2)
            if self._data_mixtype == 'normal':
                self.srate = new_sr*1e6
            else:
                self.srate = new_sr*1e6/2
            print(self.srate)

        if name in ['Data_mixtype']:
            if value == 'normal':
                if self._data_mixtype in ['mix_p1','mix_0','mix_n1', None]:
                    for i in range(12):
                        self.handle.dac_replay_type(chennel_num = i,replay_type = 0)
                    self._data_mixtype = 'normal'
            elif value == 'mix_p1':
                if self._data_mixtype in ['normal','mix_0','mix_n1', None]:
                    for i in range(12):
                        self.handle.dac_replay_type(chennel_num = i,replay_type = 1)
                    self._data_mixtype = 'mix_p1'
            elif value == 'mix_0':
                if self._data_mixtype in ['normal','mix_p1','mix_n1', None]:
                    for i in range(12):
                        self.handle.dac_replay_type(chennel_num = i,replay_type = 2)
                    self._data_mixtype = 'mix_0'
            elif value == 'mix_n1':
                if self._data_mixtype in ['normal','mix_p1','mix_0', None]:
                    for i in range(12):
                        self.handle.dac_replay_type(chennel_num = i,replay_type = 3)
                    self._data_mixtype = 'mix_n1'
            else:
                raise ValueError('Data_mixtype error!!!')
        if name in ['Set_dev_ip']:
            print(value)
            self.system_net.set_ip(value[0],value[1],value[2])
        if name in ['dev_shutdown']:
            if value == True:
                self.system_net.shutdown()
        if name in ['dev_reboot']:
            if value == True:
                self.system_net.reboot()
        
        return value

    def read(self, name: str, **kw):
        ch = kw.get('ch', 1)
        if name in ['TraceIQ', 'IQ']:
            # if (ch - 1) % 8 == 0 or (ch - 1) % 8 == 1:  # AD
            if name in ['TraceIQ']:
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
            # times = round(value * 1e9 / periodTime)
            times = new_round(value * 1e9 / periodTime, 0)
            # times = round((value * 1e9 / periodTime)*self._fs)//self._fs
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
            ch_srate = self.srate
            if isinstance(value, Waveform):
                if np.isinf(value.bounds[0]):
                    delay = 0
                    length = 1e-6
                else:
                    
                    # delay = round((value.bounds[0]*ch_srate)*self._fs)//self._fs/ch_srate
                    # length = round(((value.bounds[-2]-value.bounds[0])*ch_srate)*self._fs)//self._fs/ch_srate
                    # delay = round(value.bounds[0]*ch_srate)/ch_srate
                    # length = round((value.bounds[-2]-value.bounds[0])*ch_srate)/ch_srate
                    delay = new_round(value.bounds[0]*ch_srate, 0)/ch_srate
                    length = new_round((value.bounds[-2]-value.bounds[0])*ch_srate, 0)/ch_srate
                value <<= delay
                value.start, value.stop = 0, length
                value = value.sample(ch_srate)
                
            if self._data_mixtype == 'normal':
                ch_srate = ch_srate
            else:
                ch_srate = ch_srate*2
            # if self._data_mixtype != 0:
            #     ch_srate = ch_srate*2
            # trigger_delay = round((delay*ch_srate)*self._fs)//self._fs
            trigger_delay = new_round(delay*ch_srate, 0)
            
            self.writeWaveform(value, ch=ch, trigger_delay=trigger_delay, continuous=continuous)
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
        #         self.config['Offset'][ch]['value']
        #         self.handle.set_ch_offset(ch-1, value)
        #     else:
        #         return 'The setting voltage is too high!!!'
        elif name in ['WaveformContinue']:
            self.config['WaveformContinue'][ch]['value'] = value
  

    def set_AD(self, name, value, ch):
        """ch starts from 1
        """
        if name in ['Coefficient', ]:
            # print(value)
            self.config['StartDelay'][ch]['value'] = value['start']
            for i in range(len(value['wList'])):
                value['wList'][i]['t0'] -= value['start']
            value['stop'] -= value['start']
            value['start'] = 0
            # print(value['wList'][i]['t0'])

            wList, f_list,phi, numberOfPoints, phases, new_sted, rnks = get_coef(value, self.adc_srate)
            
            assert len(f_list) in range(1, 17), f'Invalid coefficient number of frequencies.'
            self.config['PointNumber'][ch]['value'] = numberOfPoints
            self.config['FrequencyList'][ch]['value'] =  f_list #list(np.fmod(np.fmod(-np.array(f_list), self.adc_srate)+self.adc_srate, self.adc_srate)) #f_list 
            self.config['PhaseList'][ch]['value'] =  phases #ist(np.fmod(np.fmod(-np.array(phases), np.pi*2)+np.pi*2, np.pi*2)) #phases
            self.config['Delta_PhaseList'][ch]['value'] =   phi

            self.config['Sample_time'][ch]['value'] =  new_sted
            self.config['rnks'][ch]['value'] =  rnks
            # print(ch,'TriggerDelay',self.config['TriggerDelay'][ch]['value'])
            # print(ch,'PointNumber',self.config['PointNumber'][ch]['value'])
            # print(ch,'FrequencyList',self.config['FrequencyList'][ch]['value'])
            # print(ch,'PhaseList',self.config['PhaseList'][ch]['value'])
            # print(ch,'Sample_time',self.config['Sample_time'][ch]['value'])
            # print(ch,'rnks',self.config['rnks'][ch]['value'])
            # if self.alg_use[ch-1]:
            #     assert numberOfPoints <= 16384, f'Maximum points exceeded hard demod limit.'
            #     self.set_coefficient(data, ch=ch)

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
        
        # self.triggerClose()
        self.handle.dac_updata(ch-1, trigger_delay, replay_cnt, replay_continue_flag, data)

        # if self._trigger_source:
        #     self.Trig()

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
        # self.triggerClose()
        self._adc_control(ch=ch, enable=1)
        # self.Trig()

    def _adc_control(self, ch=1, enable=1):
        
        trigger_delay_point = new_round((self.config['TriggerDelay'][ch]['value'])*1e12,0)/int(400)
        
        trigger_delay = new_round(trigger_delay_point,0)
        self._trigger_delay_sub[ch-1] = trigger_delay/self.adc_srate

        #self._trigger_delay_sub[ch-1] = trigger_delay/self.adc_srate%(1/8e9)
        #print(ch,self._trigger_delay_sub[ch-1])
        #if self._trigger_delay_sub[ch-1]/0.125e-9>=0.5:
        #    self._trigger_delay_sub[ch-1] -= 0.125e-9
        # self._trigger_delay_sub[ch-1] = self.config['TriggerDelay'][ch]['value'] + (trigger_delay - trigger_delay_point)/self.adc_srate
        
        # trigger_delay = round((self.config['TriggerDelay'][ch]['value']*self.adc_srate)*self._fs)//self._fs
        # trigger_delay = round(self.config['TriggerDelay'][ch]['value']*self.adc_srate)
        # print('ad', trigger_delay)
        # print('adc delay',trigger_delay)
        save_len = self.config['PointNumber'][ch]['value']
        # print("adc delay :",self._trigger_delay_sub[ch-1],trigger_delay,self.config['TriggerDelay'][ch]['value']*self.adc_srate)
        times = self.config['Shot'][ch]['value']

        if self.raw_use[ch-1] == True:
            ret = self.handle.rd_adc_data_ctrl(ch-13, trigger_delay, times, save_len)
        elif self.alg_use[ch-1] == True:
            f_list = self.config['FrequencyList'][ch]['value']
            phase_list  = self.config['PhaseList'][ch]['value']
            Sample_time_list = self.config['Sample_time'][ch]['value']

            self.alg_num[ch-1] = len(f_list)
            mul_f = []
            for i in range((len(f_list))):
                mul_f_i = []
                mul_f_i.append(phase_list[i])
                mul_f_i.append(f_list[i])
                mul_f_i.append(Sample_time_list[i])
                mul_f.append(mul_f_i)
            # print('adc',ch,trigger_delay,mul_f)
            ret = self.handle.rd_adc_mul_data_ctrl(ch-13, trigger_delay, times,save_len, mul_f)



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
        # print('xxxxxxxxxxxxxxxxxxxxxxxx')
        # print(save_len,times)
        if save_len > 2**17:
            return 'adc save data too long !!!'

        while 1:
            adc_data_buf, adc_data_save_len = self.handle.rd_adc_data(ch-13, times, save_len)
            if adc_data_save_len != -1:
                break
            else:
                time1 = time.time()
                if time1-time0 > (self.timeout if timeout is None else timeout):
                    raise Exception('rd_adc_data_return timeout!')


        return adc_data_buf, np.zeros_like(adc_data_buf)

    def getTraces(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None):
        cha, chb = self.get_data(ch=ch, timeout=timeout)
        if avg:
            times = self.config['Shot'][ch]['value']
            return cha/times, chb/times
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
        
        times = self.config['Shot'][ch]['value']

        assert self.alg_num[ch-1] > 0, 'Hard demod coefficient is not set.'

        
        rnks = np.array(self.config['rnks'][ch]['value'],dtype=object)
        
        adc_data = []
        for i in range(len(rnks)):
            for j in range(len(rnks[i])):
                adc_data.append([])
        # time0 = time.time()
        # print('rnks.size',rnks.size,rnks,adc_data)
        trig_point_sub = []
        for modle_num in range(len(self.config['Sample_time'][ch]['value'])):
            trig_point_sub_sub = []
            for samp_n in range(len(self.config['Sample_time'][ch]['value'][modle_num])):
                trig_point_sub_sub.append(self._trigger_delay_sub[ch-1] + self.config['Sample_time'][ch]['value'][modle_num][samp_n][0]/2.5e9)
            trig_point_sub.append(trig_point_sub_sub)
        # print(trig_point_sub)

        f_list = self.config['FrequencyList'][ch]['value']
        for modle_num in range(self.alg_num[ch-1]):
            # print('modle_num',modle_num)
            while 1:
                mul_data_bufe, read_data_len = self.handle.rd_adc_mul_data(ch-13, modle_num, times)
                if read_data_len != -1:
                    break
            
            # print(len(mul_data_bufe))
            sample_times = len(self.config['Sample_time'][ch]['value'][modle_num])
            mul_data_bufe = np.reshape(mul_data_bufe,(sample_times,-1),order = 'f')
            
            for i in range(len(trig_point_sub[modle_num])):
                mul_data_bufe[i] = mul_data_bufe[i] * np.exp(1j*2*np.pi*f_list[modle_num]*trig_point_sub[modle_num][i])
            # print(len(rnks[modle_num]),len(mul_data_bufe))
            for i in range(len(rnks[modle_num])):
                adc_data[rnks[modle_num][i]] = mul_data_bufe[i]
        # print(ch,rnks,np.shape(adc_data),self.config['Shot'][ch]['value'])

        # time1 = time.time()
        # print(ch,time1-time0)
        
        adc_data = np.array(adc_data).T
        # 
        return adc_data

    def get_IQ_alg(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None):
        data_alg = self.get_data_alg(ch=ch, timeout=timeout)
        if avg:
            return np.mean(data_alg, axis=1)
        else:
            return data_alg
    
