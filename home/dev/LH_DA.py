import numpy as np

from dev.common import BaseDriver, QOption, QReal, QVector
from dev.common.UNIVI_LH import xdma
from waveforms import Waveform


class Driver(BaseDriver):
    support_models = ['6DA']

    CHs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

    default_triggertime = 200  # us
    trigger_source = 1  # 0：内部触发，1：外部触发

    quants = [
        QReal('Offset', unit='V', ch=1,),
        QReal('Amplitude', unit='VPP', ch=1,),
        QOption('Output', ch=1),
        QVector('Waveform', value=[], ch=1),
        QReal('OffsetDC', unit='V', ch=1,),
        QVector('Marker1', value=[], ch=1),
        QReal('TriggerDelay', value=0, ch=1, unit='s',),
        # QReal('Trigger',unit='V',ch=1,)
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.srate = 2.5e9
        self.model = 'LHAWG'
        # self.datalist = []
        # for i in range(10):
        #     self.datalist.append([[],[],[],[],[],[]])
        # self.data_point_i = {'wave_id':0,'amp':0,'repeat_num':1,'continuous':0}
        # self.data_point_bufe =[[]]
        # self.data_point_bufe[0] = self.data_point_i
        # self.data_point = {}
        # for i in range(6):
        #     self.data_point[i] = self.data_point_bufe

    def open(self):
        xdma.StructPointer()
        xdma.dma_data()
        xdma.dma_data_sum()
        xdma.fpgadevdll()
        self.handle = xdma.fpgadev()
        self.Trig(self.default_triggertime, 1, continueflag=False,
                  trigger_source=self.trigger_source)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name in ['OffsetDC']:
            assert abs(value) <= 1, f'{value} >1 !'
            # wd=WD.DC(40e-6,2.5e9).setLen(49.9e-6)>>(2.5e-6)
            # points=wd.data*value
            points = np.array([value] * 1024)
            self.writeWaveform(points, ch=ch, continuous=True)
        elif name in ['Offset']:
            try:
                assert abs(value) <= 1, f'{value} >1 !'
                self.offset(ch - 1, value)
            except:
                pass
        elif name in ['Amplitude']:
            pass
        elif name in ['Output']:
            pass
        # elif name in ['Trigger']:
        #     num=self.config['Shot'][ch]['value']
        #     self.Trig(500,num,continueflag=False)
        elif name in ['Waveform']:
            if isinstance(value, Waveform):
                value = value.sample(self.srate)
            # elif isinstance(value, tuple):
            #     value = self.dist(*value)
            else:
                print('type error')
                return
            assert len(np.nonzero(value)[0]) <= int(
                50e-6 * self.srate), 'Wave is too long!'
            self.writeWaveform(value, ch=ch, continuous=False)
        elif name in ['Marker1']:
            self.writeMarker(value, ch=ch, marker_delay=0)
        else:
            super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    # def dist(self, func, distortion):
    #     data = func.sample(self.srate)
    #     from waveforms.math.signal import exp_decay_filter, correct_reflection, predistort, exp_decay_filter_old

    #     if isinstance(distortion, dict):
    #         filters = []
    #         ker = None
    #         if 'decay' in distortion and isinstance(distortion['decay'], list):
    #             for amp, tau in distortion['decay']:
    #                 filters.append(exp_decay_filter(amp, tau, self.srate))
    #         data = predistort(data, filters, ker)
    #     return data

    def Trig(self, triggertime, times=2048, continueflag=True, trigger_source=False, slot='slot6'):
        '''
           triggertime是triger长度，contunueflag = False，波形回放times次后停止；trigger_source= Ture, 外部触发
        '''
        self.handle.settrigT(triggertime, times,
                             continueflag, trigger_source, slot)

    def on(self, slot):  # 关闭所有通道
        self.handle.open_dac_board(slot)

    def off(self, slot):  # 打开所有通道
        self.handle.close_dac_board(slot)

    def offset(self, ch, value):
        # self.handle.dac_set_offset(ch,value,self.addr)
        self.handle.dac_offset(ch, value, self.addr)

    # 目前的连续波模式下data必须是寄存器的整数倍的情况下波形收尾连续
    # def writeWaveform(self,data,ch=1,continuous=False):
    #     # import pickle
    #     # import time

    #     # with open(f"{time.strftime('%Y%m%d%H%M%S')}.pickle", 'wb') as f:
    #     #     pickle.dump((data, slot, ch, continuous), f)

    #     # if ch in [1,2,3,4,5,6]:
    #     #     self.datalist[ch-1]=data*(2**15-1)
    #     # else:
    #     #     print('wrong data type or wrong ch number, must be in [1-6].')
    #     # print(self.datalist)
    #     # self.handle.wr_dac_data(self.datalist,continuous,self.addr)
    #     # self.handle.close_dac_board(self.addr)

    #     data_buf = [[]]
    #     data_buf[0] = data*(2**15-1)
    #     if ch in [1,2,3,4,5,6]:
    #         self.datalist[ch-1]=data_buf
    #         self.data_point[ch-1][0] = {'wave_id':0,'amp':1,'repeat_num':1,'continuous':continuous}
    #     else:
    #         print('wrong data type or wrong ch number, must be in [1-6].')
    #     try:
    #         print(f'{ch}',self.datalist[1][0][0])
    #     except:
    #         print('None')
    #     # for i in range(6):
    #     #     self.datalist[i]=data_buf
    #     # print(self.datalist[0])
    #     setting_save =self.handle.wr_dac_data(self.datalist,self.addr)

    #     setting_save1 = self.handle.wr_dac_setting(self.data_point,setting_save,self.addr)
        # time.sleep(0.001)
    # def writeWaveform(self,data,ch=1,continuous=False):
    #     # if ch in [1,2,3,4,5,6]:
    #     #     self.datalist[int(self.addr[4:])-1][ch-1]=[data*(2**15-1)]
    #     #     self.data_point[ch-1][0] = {'wave_id':0,'amp':1,'repeat_num':1,'continuous':continuous}
    #     # else:
    #     #     print('wrong data type or wrong ch number, must be in [1-6].')
    #     # print('s'*10,data)
    #     setting_save =self.handle.wr_dac_data_single_ch([data*(2**15-1)],ch,self.addr)
    #     setting_save1 = self.handle.wr_dac_setting_single_ch({0: {'wave_id': 0, 'amp': 1, 'repeat_num': 1, 'continuous': False}},setting_save,ch,self.addr)

    def writeWaveform(self, data, ch=1, continuous=False):
        data_point_ch = [{'wave_id': 0, 'amp': 1,
                          'repeat_num': 1, 'continuous': continuous}]
        setting_save = self.handle.wr_dac_data_single_ch(
            [data * (2**15 - 1)], ch, self.addr)
        setting_save1 = self.handle.wr_dac_setting_single_ch(
            data_point_ch, setting_save, ch, self.addr)

    def writeMarker(self, data, ch=1, marker_delay=0):
        self.handle.close_all_marker('slot6')

        if ch in list(range(1, 17)):
            marker_setting = self.handle.wr_marker_singlechennel(
                ch - 1, [data], 'slot6')
            marker_data_point = []
            marker_data_point.append(
                {'marker_trigger_delay': marker_delay, 'marker_num': 0, 'marker_repeat_num': 1})
            self.handle.wr_marker_single_setting(
                ch - 1, marker_data_point, marker_setting, 'slot6')
        else:
            print('wrong data type or wrong ch number, must be in [1-16].')
        self.handle.open_marker('slot6')

    def beforeSet(self):
        self.handle.settrigT(self.default_triggertime, 1,
                             continueflag=0, trigger_source=0, slot='slot6')
        # time.sleep(0.1)

    def afterSet(self):
        # print('wait')
        # time.sleep(0.1)
        self.handle.settrigT(self.default_triggertime, 1, continueflag=1,
                             trigger_source=self.trigger_source, slot='slot6')

    def set_clk_baord_trigger_out(self, trigger_out_sel, slot):
        self.handle.set_clk_baord_trigger_out(trigger_out_sel, slot)

    def resync_awg(self):
        self.handle.resync_awg()
