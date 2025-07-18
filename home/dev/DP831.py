import numpy as np

from dev.common import Quantity, VisaDriver


class Driver(VisaDriver):
    # need libusb-1.0.dll
    segment = ('na', '101|102|103')
    # number of available channels
    CHs = list(range(2))

    quants = [
        # MW
        Quantity('Frequency', value=0, ch=1, unit='Hz'),  # float
        Quantity('Power', value=0, ch=1, unit='dBm'),  # loat
        Quantity('Output', value='OFF', ch=1),  # str
    ]

    def __init__(self, addr: str = '', **kw):
        super().__init__(addr=addr, **kw)
        # 'USB0::0x1AB1::0x0E11::DP8F211200089::INSTR'
        self.model = 'DP831'
        self.srate = 1e9

    def write(self, name: str, value, **kw):
        """write to device
        """
        if name == 'Output':
            self.handle.write(f':OUTP CH2,{value}')
        return value

    def read(self, name: str, **kw):
        """read from device
        """
        if name == 'Power':
            return 1
