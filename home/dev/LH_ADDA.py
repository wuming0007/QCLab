import numpy as np

from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,
                        QVector, get_coef)
from dev.common.UNIVI_LH import xdma


class Driver(BaseDriver):
    support_models = ['LHADC']

    CHs = [1]

    default_triggertime = 200  # us
    trigger_source = 1  # 0：内部触发，1：外部触发

    quants = [
        QReal('FrequencyList', value=[100e6], ch=1, unit='Hz',),  # 解调频率
        # 利用setValue方法来对采样延迟点数设置
        QReal('TriggerDelay', value=0, ch=1, unit='s',),
        QInteger('Shot', value=2048, ch=1),  # 利用setValue方法来对重复采样次数设置
        QInteger('n', value=2048, ch=1),  # 利用setValue方法来对采样延迟点数设置
        QInteger('PointNumber', value=2048, ch=1),
        QBool('avg', value=False, ch=1),  # 是否对数据进行平均，平均是采样点数需小于2048
        QList('Coefficient', value=None, ch=1),
        QReal('Trigger', unit='V', ch=1,),
        QOption('CaptureMode', value=1, ch=1, options=[
                # 采集模式：0连续，1触发
                ('raw', 'raw'), ('alg', 'alg'), ('raw_alg', 'raw_alg')]),
        QInteger('StartCapture', value=1, ch=1,),  # 采集模式：0连续，1触发
        QVector('TraceIQ', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QVector('algIQ', value=[], ch=1),

    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'LHADC'
        self.srate = 1.25e9

    def open(self):
        xdma.StructPointer()
        xdma.dma_data()
        xdma.dma_data_sum()
        xdma.fpgadevdll()
        self.handle = xdma.fpgadev()
        self.open_init()

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = 1
        self.config[name][ch]['value'] = value  # 更新到config

        if name in ['PointNumber',]:
            self.config['PointNumber'][ch]['value'] = value
        # elif name in ['TriggerDelay','Shot','PointNumber',]:
        #     delay=round(self.config['TriggerDelay'][ch]['value']*self.srate)
        #     num=self.config['Shot'][ch]['value']
        #     read_data_len=self.config['PointNumber'][ch]['value']
        #     self.handle.rd_adc_data_set(delay,read_data_len,num,self.addr)
        elif name in ['FrequencyList',]:
            _kw = {
                'freq': self.config['FrequencyList'][ch]['value'],
                'sRate': self.srate,
                'pointNum': self.config['PointNumber'][ch]['value'],
            }
            # coef = u_getExp(**_kw)
            # self.setValue('Coefficient',(coef,))
        elif name in ['Coefficient',]:
            data, f_list, numberOfPoints, phases = get_coef(value, self.srate)
            assert len(f_list) in range(
                1, 13), f'Invalid coefficient number of frequencies.'
            self.setValue('PointNumber', numberOfPoints)

            # _,pointnum = value[0].shape
            assert numberOfPoints == self.config['PointNumber'][
                ch]['value'], f'{numberOfPoints} != numOfPoint'
            self.setcoefficient(data)
        elif name == 'StartCapture':
            self.startCapture()
        elif name == 'CaptureMode':
            # self.handle.set_mode(value)
            pass
        elif name == 'Trigger':
            pass
        else:
            return super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        # mode = self.config[name][ch]['value']

        # if mode == "raw":
        #     return self.getTrace()
        # elif mode == 'alg':
        #     return self.get_FPGA_IQ_new()
        ch = kw.get('ch', 1)
        if name in ['TraceIQ']:
            return self.getTrace()
        elif name in ['algIQ']:
            return self.getsingleIQ()
        elif name in ['IQ']:
            return self.get_FPGA_IQ_new()
            # return self.getsingleIQ()
        else:
            return super().read(name, ch=ch, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def open_init(self):
        ch = 1
        #########################################################################
        delay = round(self.config['TriggerDelay'][ch]['value'] * self.srate)
        num = self.config['Shot'][ch]['value']
        read_data_len = self.config['PointNumber'][ch]['value']
        self.handle.rd_adc_data_set(delay, read_data_len, num, self.addr)
        #########################################################################
        self.Trig(self.default_triggertime, 1, continueflag=False,
                  trigger_source=self.trigger_source)

    def Trig(self, triggertime=None, times=1, continueflag=True, trigger_source=False, slot='slot6'):
        '''
           triggertime是triger长度，contunueflag = False，波形回放times次后停止；trigger_source= Ture, 外部触发
        '''
        if triggertime is None:
            triggertime = self.default_triggertime
        self.handle.settrigT(triggertime, times, continueflag,
                             trigger_source, slot='slot6')

    def getTrace(self):  # 采样点数可以设置到采样上线 1025*1023个
        ch = 1
        avg = self.getValue('avg')
        if avg:
            dataI, dataQ = self.getSumTrace()
        else:
            num = self.config['Shot'][ch]['value']
            read_data_len = self.config['PointNumber'][ch]['value']
            dataI, dataQ, _ = self.handle.rd_adc_data_return(
                read_data_len, num, slot=self.addr)
            # dataI =np.mean(dataI,axis=0)
            # dataQ =np.mean(dataQ,axis=0)
        return np.asarray(dataI), np.asarray(dataQ)

    def getSumTrace(self):  # 采样点数只能小于2048
        Data_length = self.getValue('PointNumber')
        if Data_length > 2048:
            print('Data_length is larger than 2048 point')
        else:
            delay = round(self.config['TriggerDelay'][1]['value'] * self.srate)
            shots = self.config['Shot'][1]['value']
            dataI, dataQ = self.handle.rd_adc_sum_data(
                delay, shots, Data_length, slot=self.addr)
            dataI = np.asarray(dataI) / shots
            dataQ = np.asarray(dataQ) / shots
        return dataI, dataQ

    # def datafft(self, data):
    #     f_list=self.getValue('FrequencyList')
    #     "sample_rate, f_list使用Hz为单位"
    #     fft_y=fft(data)              #快速傅里叶变换
    #     N=len(data)
    #     x = np.arange(N)             # 频率个数
    #     half_x = x[range(int(N/2))]  #取一半区间

    #     abs_y=np.abs(fft_y)          # 取复数的绝对值，即复数的模(双边频谱)
    #     angle_y=np.angle(fft_y)      #取复数的角度
    #     normalization_y=abs_y/N*2    #归一化处理（双边频谱）
    #     normalization_half_y = normalization_y[range(int(N/2))]      #由于对称性，只取一半区间（单边频谱）
    #     amp = []
    #     for ii in range(len(f_list)):
    #         n = round(f_list[ii]/self.srate*N)
    #         amp.append(normalization_half_y[n])
    #     return amp

    # def getIQ(self):

    #     dataI,dataQ = self.getTrace()
    #     cha = self.datafft(dataI)
    #     chb = self.datafft(dataQ)
    #     return np.array(cha) + 1j * np.array(chb)

    def getsingleIQ(self):
        coeff = self.config['Coefficient'][1]['value'][0]
        pointNum = self.config['PointNumber'][1]['value']

        dataI, dataQ = self.getTrace()
        A_lst = (dataI[:, :pointNum]).dot(coeff.T) / pointNum
        B_lst = (dataQ[:, :pointNum]).dot(coeff.T) / pointNum

        return A_lst, B_lst

    # def getsumIQ(self):

    #     dataI,dataQ = self.getSumTrace()
    #     cha = self.datafft(dataI)
    #     chb = self.datafft(dataQ)
    #     return np.array(cha) + 1j * np.array(chb)

    def setcoefficient(self, coeff):
        size, pointnum = coeff.shape
        assert pointnum < 4097, f'{pointnum} > 4096 !'
        coeff_real = (coeff.real * (2**11 - 1)).astype(np.int32)
        coeff_imag = (coeff.imag * (2**11 - 1)).astype(np.int32)
        for i in range(10):
            if i < size:
                self.handle.set_demodulation_data(
                    channelnum=i + 1, data_i=coeff_imag[i], data_q=coeff_real[i], slot=self.addr)
                self.handle.demodulation_channelsetting(
                    channelnum=i + 1, channel_en=1, compare_continue=1, compare_len=pointnum, real_sin=0, imag_cos=0, compare_value=0, slot=self.addr)
            else:
                self.handle.demodulation_channelsetting(
                    channelnum=i + 1, channel_en=0, compare_continue=1, compare_len=0, real_sin=0, imag_cos=0, compare_value=0, slot=self.addr)

    def startCapture(self):
        delay = round(self.config['TriggerDelay'][1]['value'] * self.srate)
        shots = self.config['Shot'][1]['value']
        read_data_len = self.config['PointNumber'][1]['value']
        assert shots < 32768, f'{shots} > 32767 !'
        self.handle.rd_adc_data_set(delay, read_data_len, shots, self.addr)
        self.handle.demodulation_allsetting(
            reset=1, demodulation_en=0, delay=delay, compare_times=shots, slot=self.addr)
        self.handle.demodulation_allsetting(
            reset=0, demodulation_en=0, delay=delay, compare_times=shots, slot=self.addr)
        self.handle.demodulation_allsetting(
            reset=0, demodulation_en=1, delay=delay, compare_times=shots, slot=self.addr)
        # self.handle.demodulation_result_update(slot=self.addr)

    # def get_FPGA_IQ_once(self,size):
    #     iq_data = []
    #     for i in range(size):
    #         res_dict = self.handle.get_demodulation_result(channelnum=i+1,slot=self.addr)
    #         iq_data.append(res_dict['demo_now_data'])
    #     return np.array(iq_data)/(2**11-1)

    # def get_FPGA_IQ(self):
    #     size=len(self.config['Coefficient'][1]['value'][0])
    #     shots=self.config['Shot'][1]['value']
    #     iq_res=[]
    #     for _ in range(shots):
    #         self.startCapture()
    #         iq_once=self.get_FPGA_IQ_once(size)
    #         iq_res.append(iq_once)
    #     res = np.array(iq_res)
    #     return res,np.zeros_like(res)

    def get_FPGA_IQ_new(self):
        size = len(self.config['Coefficient'][1]['value'][0])
        shots = self.config['Shot'][1]['value']
        pointNum = self.config['PointNumber'][1]['value']
        iq_data_A = []
        iq_data_B = []
        # self.startCapture(shots)
        for i in range(size):
            A, B = self.handle.get_demo_save_data(channelnum=i + 1,
                                                  data_len=shots,
                                                  slot=self.addr)
            iq_data_A.append(A)
            iq_data_B.append(B)
        res_A = np.array(iq_data_A).T / (2**11 - 1) / pointNum * 1j
        res_B = np.array(iq_data_B).T / (2**11 - 1) / pointNum * 1j
        return res_A, res_B
