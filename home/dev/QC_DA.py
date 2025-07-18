import sys

import numpy as np

from dev.common import BaseDriver, QOption, QReal, QVector, QList, QInteger
from dev.common.QC import DeviceInterface, all_ip

dev = DeviceInterface()


class Driver(BaseDriver):
    support_models = ['QC_DA']

    CHs = [1, 2, 3, 4]

    quants = [
        QReal('Offset', unit='V', ch=1,),
        QReal('Amplitude', unit='VPP', ch=1,),
        QOption('Output', ch=1),
        QVector('Waveform', value=[], ch=1),
        QReal('OffsetDC', unit='V', ch=1,),
        QList('Coefficient', value=None, ch=1),
        QReal('TriggerDelay', value=0.0, ch=1,),
        QReal('Shot', value=2000, ch=1,),

        QInteger('SingleTrigger',
                 set_cmd='',
                 get_cmd=''),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'QC_DA'
        self.srate = 2e9
        self.master_id = 'QF10KBE0003'
        self.master_id2 = 'QF10L4S0005'

        self.da_id = all_ip['DA'][self.addr]['id']
        self.da_ip = all_ip['DA'][self.addr]['ip']
        self.channel_gain = all_ip['DA'][self.addr]['init_gain']
        self.data_offset = all_ip['DA'][self.addr]['init_offset']

        self.trigger_count = 2000
        self.trigger_interval = 200e-6
        self.triggerDelay = 0e-6

    def open(self):
        ret = 0
        # 每次连接需要调表
        ret |= dev.da_connect_device(
            self.da_id, self.da_ip, False, self.channel_gain, self.data_offset)
        if ret != 0:
            print(f'ERROR:da board:[{self.da_id}]connect failure ,ret:[{ret}]')

        ret |= dev.da_init_device(self.da_id)

        ret |= dev.da_set_trigger_count_l1(self.da_id, self.trigger_count)
        ret |= dev.da_set_trigger_interval_l1(
            self.da_id, self.trigger_interval)

        if self.da_id == self.master_id:
            ret = dev.da_set_trigger_delay(self.master_id, self.triggerDelay)
            print('set_trigger_delay:', ret, self.master_id)
        elif self.da_id == self.master_id2:
            ret = dev.da_set_trigger_delay(self.master_id2, self.triggerDelay)
            print('set_trigger_delay:', ret, self.master_id2)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        # Amp -32768~32768
        if name in ['OffsetDC']:
            assert abs(value) <= 1, f'{value} >1 !'
            points = np.array([value] * int(2.0e9 * 50e-6))
            self.writeWaveform(points, ch=ch)
            # self.writeWaveformcontinue(points,ch=ch)
        # elif name in ['Offset']:
        #     assert abs(value)<=1, f'{value} >1 !'
        #     points = np.array([value]*int(2.0e9*50e-6))
        #     self.writeWaveform(points,ch=ch)
            # self.writeWaveformcontinue(points,ch=ch)
        elif name in ['Amplitude']:
            pass
        elif name in ['Output']:
            pass
        elif name == 'SingleTrigger':
            self.enable_triggger()
        elif name in ['Waveform']:
            self.writeWaveform(value, ch=ch)
        elif name in ['TriggerDelay']:
            self.da_set_trig_delay(value)
        elif name in ['Coefficient']:
            self.da_set_trig_delay(value['start'])
        elif name in ['Shot']:
            # dev.da_set_trigger_count_l1(self.da_id, value)
            pass
        else:
            super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def da_set_trig_delay(self, ad_trig_delay):
        # ad_trig_delay: s
        dev.da_set_trigger_delay(self.da_id, ad_trig_delay)

    def on(self, ch):  # 关闭通道
        dev.da_start_output_wave(self.da_id, ch)

    def off(self, ch):  # 打开通道
        dev.da_stop_output_wave(self.da_id, ch)

    def offset(self, ch, value):
        dev.da_set_data_offset(self.da_id, ch, value)

    def enable_triggger(self):
        ret = dev.da_trigger_enable(self.master_id)
        if ret != 0:
            print(
                f'ERROR:master da board [{self.master_id}] trigger enable failure ,ret:[{ret}].')
            sys.exit(0)
        else:
            print(
                f'master da board [{self.master_id}] trigger enable success .')

    def da_disconnect_device(self):
        dev.da_disconnect_device(self.da_id)

    # Amp -65536~65536
    def writeWaveform(self, data, ch=1, mode=0, padding=0, channel_output_delay=0):
        data = data * 32300
        # print(f'da_id={self.da_id}',f'ch={ch}','max',np.max(data),'min',np.min(data))
        # print('wave1',len(data))
        # print(data)
        dev.da_stop_output_wave(self.da_id, ch)
        # channel_output_delay=channel_output_delay/1e9)
        dev.da_write_wave(data, self.da_id, ch, 'i', mode, padding)
        dev.da_start_output_wave(self.da_id, ch)
        # print('wave2')

    def writeWaveformcontinue(self, data, ch=1, mode=1, padding=0, channel_output_delay=0):
        data = data * 32300  # 32768
        print(self.master_id, self.da_id)
        dev.da_stop_output_wave(self.da_id, ch)
        dev.da_write_wave(data, self.da_id, ch, 'i', mode=mode,
                          padding=padding, channel_output_delay=channel_output_delay / 1e9)
        dev.da_start_output_wave(self.da_id, ch)
        dev.da_trigger_enable(self.master_id)
