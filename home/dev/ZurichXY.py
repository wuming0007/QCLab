from textwrap import dedent

import numpy as np
from waveforms import Waveform
from zhinst.toolkit import *

from dev.common import BaseDriver, Quantity


class Driver(BaseDriver):

    segment = ('na', '101|102|103')
    # number of available channels
    CHs = [0, 1]

    quants = [
        # MW
        Quantity('CenterFrequency', value=0, ch=1, unit='Hz'),  # float
        Quantity('SidebandFrequency', value=0, ch=1, unit='Hz'),  # float
        Quantity('Power', value=0, ch=1, unit='dBm'),  # loat
        Quantity('Output', value='OFF', ch=1),  # str

        # AWG
        Quantity('TriggerSource', value=8, ch=1, unit='s'),  # float
        Quantity('Amplitude', value=0, ch=1, unit='Vpp'),  # float
        Quantity('Offset', value=0, ch=1, unit='V'),  # float
        Quantity('Waveform', value=np.array([]), ch=1),  # np.array or Waveform
        Quantity('DIOZysnc', value='zsync', ch=1),  # np.array or Waveform
    ]

    def __init__(self, addr: str, **kwds):
        super().__init__(addr=addr, **kwds)
        self.srate = 2e9
        self.sgcode = ''

    def open(self, **kwds):
        session = Session("localhost")
        self.handle = session.connect_device("DEV12363")
        self.handle.system.clocks.referenceclock.in_.source("internal")
        # self.sg_initial()

    def close(self, **kwds):
        pass

    def read(self, name, **kwds):
        pass

    def write(self, name, value, **kwds):
        ch = kwds.get('ch', 1) - 1
        shots = kwds.get('shots', 1024)
        if name == 'Waveform':
            sbf = self.getValue('SidebandFrequency')
            if isinstance(value, Waveform):
                t = np.arange(value.start, value.stop, 1 / value.sample_rate)
                value = value.sample()  # *np.exp(2j * np.pi * sbf * t)

            self.execute_sg(value, ch, shots=shots)
        elif name == 'DIOZysnc':
            assert value in ["zsync", "dio"]
            self.handle.sgchannels[ch].awg.diozsyncswitch(
                value)    # AWG 右侧trigger --DIO/Zysnc Trigger
        elif name == 'TriggerSource':
            # AWG setting
            # 8 for internal trigger
            self.handle.sgchannels[0].awg.auxtriggers[0].channel(value)
        elif name == 'Frequency':
            # assert value/200e6
            # 200MHz的整数倍
            for i in [0, 1]:
                self.handle.synthesizers[i].centerfreq(value)
        elif name == 'Power':
            assert value in np.arange(-30, 11, 5)
            self.handle.sgchannels[ch].output.range(value)
        elif name == 'Output':
            assert value in [0, 1]
            self.handle.sgchannels[ch].output.on(value)

    # def run(self):
    #     self.handle.

    def sg_initial(self, sg_local_frequency, sg_power):
        # print(local_frequency)
        self.handle.synthesizers[1].centerfreq(sg_local_frequency)
        sg_channel = [0, 1]
        for i in sg_channel:
            self.handle.sgchannels[i].awg.diozsyncswitch(
                "zsync")    # AWG 右侧trigger --DIO/Zysnc Trigger
            self.handle.sgchannels[i].output.range(sg_power[i])  # [-30,10]
            self.handle.sgchannels[i].output.on(True)  # dBm
        return

    def execute_sg(self, rf_pulse, channel, shots=1024):
        # repeat({shots}) {{
        sgcode = dedent(f"""
        const SG_WS  = {len(rf_pulse)} ; 
        wave  w_I = placeholder(SG_WS) ; 
        wave  w_Q = placeholder(SG_WS) ;
        assignWaveIndex(1, w_I , 2, w_Q , 0) ;
        repeat({shots}) {{
            waitDigTrigger(1);
            //waitZSyncTrigger() ;
            //playWave(w_I, w_Q);   
            //playWave(1,w_I,2, w_Q); 
            playWave(1,2,w_I,1,2, w_Q); 
        }}
        """)
        if self.sgcode != sgcode:
            # shfqc.sgchannels[0].generator.load_sequencer_program(sg_program)
            self.sgcode = sgcode
            print(self.sgcode)
            self.handle.sgchannels[channel].awg.load_sequencer_program(
                self.sgcode)  # 先写code 再写wf
        w = Waveforms()
        w[0] = rf_pulse
        self.handle.sgchannels[channel].awg.write_to_waveform_memory(w)
        assert (self.handle.sgchannels[channel].awg.enable(True, deep=True))
