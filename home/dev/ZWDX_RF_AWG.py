import numpy as np

from dev.common import BaseDriver, Quantity
from dev.common.ZWD_DDS import ZWDDDS


class Driver(BaseDriver):

    CHs = list(range(1, 13))

    quants = [
        Quantity('OffsetDC', unit='V', ch=1,),
        Quantity('Amplitude', value=0.816, ch=1, unit='Vpp'),  # 振幅
        Quantity('Offset', value=0, ch=1, unit='Vpp'),  # 振幅
        Quantity('Waveform', value=[], ch=1),  # 波形
        Quantity('Output', value=[], ch=1),  # 波形

        Quantity('SamplingMode', ch=1, value='5G'),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.addr = (addr, kw.get('port', 9003))
        self.srate = 5e9

    def open(self):
        self.handle = ZWDDDS(*self.addr)
        self.handle.init_dev(10)
        self.handle.open(self.CHs)

    def close(self):
        self.handle.close(self.CHs)

    def write(self, name: str, value, **kw):
        ch = kw.get("ch", 1)
        if name == "Waveform":
            self.handle.write_wave_form(value, ch=ch)
        elif name == 'SamplingMode':
            self.handle.set_mode(value)
        # elif name == "Amplitude":
        #     self.set_amplitude(value, c_index)
        # elif name == "Offset":
        #     self.set_offset(value, c_index)
        # elif name == "Output":
        #     self.set_output(value, c_index)
        # elif name == 'OffsetDC':
        #     wflen = int(99e-6*self.srate)
        #     wfd = np.ones(wflen)*value
        #     self.set_waver(wfd, c_index)
        else:
            pass

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)
