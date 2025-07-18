from textwrap import dedent

import numpy as np
from waveforms import Waveform
from zhinst.toolkit import *

from dev.common import BaseDriver, Quantity


class Driver(BaseDriver):

    segment = ('na', '101|102|103')
    # number of available channels
    CHs = list(range(1, 9, 1))

    quants = [
        # AWG
        # output range, in unit of V
        Quantity('Range', value=0, ch=1, unit='Vpp'),
        Quantity('Offset', value=0, ch=1, unit='V'),  # float
        Quantity('Waveform', value=np.array([]), ch=1),  # np.array or Waveform
        Quantity('Diomode', value=3, ch=1),  # Dio-mode: QCCS
        Quantity('Output', value=0, ch=1),  # output on
        Quantity('Hold', value=0, ch=1),  # keep last point
    ]

    def __init__(self, addr: str, **kwds):
        super().__init__(addr=addr, **kwds)
        self.srate = 2e9

    def open(self):
        session = Session("localhost")
        self.handle = session.connect_device("DEV8932")
        self.handle.system.clocks.sampleclock.freq(2e9)
        # self.sg_initial()

    def close(self):
        pass

    def read(self):
        pass

    def write(self, name, value, **kwds):
        ch = kwds.get('ch', 1) - 1
        shots = kwds.get('shots')
        if name == 'Waveform':
            # if isinstance(value, Waveform):
            # value = value.sample()

            from waveforms import cos, sin, square

            i = 0.5 * square(2e-6)
            i.start = 0
            i.stop = 8e-6
            i.sample_rate = 2e9
            q = 1 * square(6e-6)
            q.start = 0
            q.stop = 8e-6
            q.sample_rate = 2e9
            value = (i.sample(), q.sample())

            self.execute_awg(value, ch, shots=shots)
            # print(type(square_pulse))
            # t = np.arange(value.start,value.stop,1/self.srate)

            # wave[q]= value * np.exp(2j * np.pi * frequency[q] * t + 1j*phase[q])
        elif name == 'Range':
            assert value in [0.2, 0.4, 0.6, 0.8, 1, 2, 3, 4, 5]
            self.handle.sigouts[ch].range(value)
        elif name == 'Offset':
            self.handle.sigouts[ch].offset(value)
        elif name == "Diomode":
            assert value in [0, 1, 2, 3]
            self.handle.dios[0].mode(value)   # 3: QCCS
        elif name == 'Output':
            assert value in [0, 1]
            self.handle.sigouts[ch].on(value)   # output on
        elif name == 'Hold':
            assert value in [0, 1]
            self.handle.awgs[(ch) // 2].outputs[(ch) % 2].hold(value)

    def execute_awg(self, rf_pulse, channel, shots=1024):
        print(len(rf_pulse[0]))
        awg_code = dedent(f"""
        // Constants
        const AWG_WS = {len(rf_pulse[0])};
        wave w_L = placeholder(AWG_WS) ;  
        wave w_R = placeholder(AWG_WS) ;  
        assignWaveIndex(w_L,w_R, 0) ; 
        repeat({shots}) {{ 
            waitZSyncTrigger() ; 
            playWave(1, w_L, 2, w_R) ; 
            //waitWave();
        }}
        """
        )
        w = Waveforms()
        w[0] = rf_pulse
        self.handle.awgs[channel].load_sequencer_program(
            awg_code)  # 先写code 再写wf
        self.handle.awgs[channel].write_to_waveform_memory(w)
        assert (self.handle.awgs[channel].enable(True, deep=True))
