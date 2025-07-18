
import numpy as np

from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,
                        QVector, get_coef)
from dev.common.QC import DeviceInterface, all_ip

dev = DeviceInterface()


class Driver(BaseDriver):

    support_models = ['QC_AD']

    CHs = [1]

    quants = [
        QInteger('PointNumber', value=2048, ch=1),  # 1024的整数倍
        QReal('TriggerDelay', value=0, ch=1),
        QReal('Shot', value=1000, ch=1),  # 重复次数
        QList('Coefficient', value=None, ch=1),
        QList('PhaseList', value=None, ch=1),
        QBool('avg', value=False, ch=1),

        QVector('IQ', value=[], ch=1),
        QReal('sampleRate', value=1e9, ch=1, unit='Hz',),
        QVector('TraceIQ', value=[], ch=1),

        QList('FrequencyList', value=[50e6], ch=1),  # 解调频率列表
        QList('start', value=[0], ch=1),            #
        QList('stop', value=[500], ch=1),            #

        QOption('CaptureMode', value=1, ch=1, options=[
                # 采集模式：0连续，1触发
                ('raw', 'raw'), ('alg', 'alg'), ('raw_alg', 'raw_alg')]),
        QInteger('StartCapture', value=1, ch=1,),  # 采集模式：0连续，1触发
    ]
    '''
    frame_size: 采集点数；整数；无单位；比如，2048；(等价于pointNum)
    RecordLength: 采集点数除以1024；整数；单位kB；比如，2；(等价于pointNum/1024)
    freq_cnt: 需解调频率个数，最多为10；整数；无单位；比如，5；
    frame_cnt/frameNum: 重复次数；整数；无单位；比如，1000；(等价于shots)
    wave_cnt: ?

    NOTE: 提供的API应在注释里写清楚参数的含义、类型、单位和示例值
    '''

    def __init__(self, addr, **kw):
        '''addr: IP'''
        super().__init__(addr, **kw)
        self.model = 'QC_AD'
        self.srate = 1e9
        self.ad_id = all_ip['AD'][self.addr]['id']
        self.ad_mac = all_ip['AD'][self.addr]['mac']
        self.host_mac = '74-86-E2-0C-65-B3'  # 主机mac地址

        self.master_id = 'QF10KBE0003'
        self.trigger_count = 2000
        self.trigger_interval = 200e-6
        self.triggerDelay = 0

    def open(self):
        ret = 0
        ret |= dev.ad_connect_device(self.ad_id, self.host_mac, self.ad_mac)
        ret |= dev.ad_init_device(self.ad_id)
        ret |= dev.ad_clear_wincap_data(self.ad_id)
        if ret != 0:
            print(f'ERROR:ad board:[{self.ad_id}]connect failure ,ret:[{ret}]')
        dev.ad_set_trigger_count(self.ad_id, self.trigger_count)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        self.config[name][ch]['value'] = value

        if name == 'PointNumber':  # 采样长度 [0, 18000]ns
            # print(name,self.ad_id,ch,value)
            dev.ad_set_sample_depth(self.ad_id, value)
        elif name == 'TriggerDelay':  # [0-2.56e-4]s
            pass
        elif name == 'StartCapture':
            # self.start_capture()
            pass
        elif name == 'CaptureMode':
            self.set_mode(value)

        elif name == 'Shot':
            # dev.ad_set_trigger_count(self.ad_id, value)
            pass
        elif name == 'Coefficient':
            data, f_list, numberOfPoints, phases = get_coef(value, 1e9)
            k = 0
            flist = []
            for param in value['wList']:
                dev.ad_set_window_width(self.ad_id, param['window'][1])
                dev.ad_set_window_start(self.ad_id, param['window'][0])
                dev.ad_set_demod_freq(self.ad_id, param['Delta'])
                dev.ad_commit_demod_set(self.ad_id, k)
                flist.append(param['Delta'])
                k = k + 1
            self.setValue('FrequencyList', flist)
            self.setValue('PhaseList', phases)
        elif name in ['FrequencyList', 'PhaseList']:
            pass
        else:
            super().write(name, value, ch=ch, **kw)

        return value

    def read(self, name: str, **kw):
        ch = kw.get('ch', 1)
        if name in ['TraceIQ']:
            avg = True  # self.config['avg'][1]['value']
            return self.getTraces(avg=avg, timeout=None)
        elif name in ['IQ']:
            avg = self.config['avg'][1]['value']
            phaseList = self.config['PhaseList'][ch]['value']
            e = np.exp(1j * np.asarray(phaseList))
            result = self.getIQ(avg=avg, timeout=None)
            # print('*****************************\r\n'*2)
            # print('1:',result[0].shape,len(result))
            result = result[0] * e, result[1] * e
            # print('*****************************\r\n'*2)
            # print('2:',result.shape)

            return result
        else:
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def set_mode(self, fft):
        if fft == 'alg':
            dev.ad_set_mode(self.ad_id, 1)  # fpga
        else:
            dev.ad_set_mode(self.ad_id, 0)
        # dev.ad_clear_wincap_data(self.ad_id1)
        # dev.ad_clear_wincap_data(self.ad_id2)
        dev.ad_clear_wincap_data(self.ad_id)
        # 注意顺序！！！！！！
        dev.ad_enable_adc(self.ad_id)

    def start_capture(self):
        dev.da_trigger_enable(self.master_id)

    def getData(self, fft=False, avg=False, timeout=None):
        f_list = self.getValue('FrequencyList', ch=1)
        n = len(f_list)

        res = dev.ad_receive_data(self.ad_id)

        # 默认返回8个解模频率
        # print(res.shape,res[0])
        A, B = res[1] / 1e5, res[2] / 1e5
        if avg:
            return np.mean(A, axis=0), np.mean(B, axis=0)  # Trace
        else:
            return A[:, :n], B[:, :n]

    def getIQ(self, avg=False, timeout=None):
        return self.getData(fft=True, avg=avg, timeout=timeout)

    def getTraces(self, avg=True, timeout=None):
        return self.getData(fft=False, avg=avg, timeout=timeout)

    def get_ad_status(self):
        dev.ad_query_status(self.ad_id)
