from textwrap import dedent

import numpy as np
from waveforms import Waveform
from zhinst.toolkit import *

from dev.common import BaseDriver, Quantity


class Driver(BaseDriver):

    segment = ('na', '101|102|103')
    # number of available channels
    CHs = [1]

    quants = [
        # AWG
        # output range, in unit of V
        Quantity('BurstPeriod', value=0, ch=1, unit='Vpp'),
        Quantity('Shot', value=0, ch=1, unit='V'),
    ]

    def __init__(self, addr: str, **kwds):
        super().__init__(addr=addr, **kwds)
        self.srate = 2e9

    def open(self):
        session = Session("localhost")
        self.handle = session.connect_device("DEV10181")
        self.handle.system.clocks.referenceclock.in_.source(0)
        self.handle.zsyncs[0].output.source("register_forwarding")  # feedback
        self.handle.zsyncs[0].output.enable(False)  # feedback
        # feedback
        self.handle.zsyncs[0].output.registerbank.sources["*"].enable(False)
        self.handle.triggers.out[0].enable(False)  # ports

    def close(self):
        pass

    def read(self):
        pass

    def write(self, name, value, **kwds):
        ch = 1
        if name == 'BurstPeriod':
            self.handle.execution.holdoff(value)
        elif name == 'Shot':
            self.handle.execution.repetitions(value)

    def BurstMode_init(self, count=1024, period=200e-6, **kwds):
        self.setValue('BurstPeriod', period, **kwds)
        self.setValue('BurstCount', count, **kwds)
