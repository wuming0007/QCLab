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
        # MW
        Quantity('CenterFrequency', value=0, ch=1, unit='Hz'),  # float
        Quantity('SidebandFrequency', value=0, ch=1, unit='Hz'),  # float
        Quantity('Power', value=0, ch=1, unit='dBm'),  # loat
        Quantity('Output', value='OFF', ch=1),  # str

        # AWG
        Quantity('Amplitude', value=0, ch=1, unit='Vpp'),  # float
        Quantity('Offset', value=0, ch=1, unit='V'),  # float
        Quantity('Waveform', value=np.array([]), ch=1),  # np.array or Waveform

        # ADC
        Quantity('PointNumber', value=1024, ch=1, unit='point'),  # int
        Quantity('ReferenceClock', value='internal', ch=1, unit='point'),
        Quantity('TriggerSource', value=0, ch=1, unit='s'),  # float
        Quantity('TriggerDelay', value=0, ch=1, unit='s'),  # float
        Quantity('Shot', value=512, ch=1),  # int
        Quantity('TraceIQ', value=np.array([]), ch=1),  # np.array
        Quantity('Trace', value=np.array([]), ch=1),  # np.array
        Quantity('IQ', value=np.array([]), ch=1),  # np.array
        Quantity('Coefficient', value=np.array([]), ch=1),  # np.array
        Quantity('StartCapture', value=1, ch=1,),  # int
        Quantity('Trigger', value=1, ch=1,),  # int

        Quantity('CaptureMode', value='raw', ch=1),  # raw->TraceIQ, alg-> IQ
    ]

    def __init__(self, addr: str, **kwds):
        super().__init__(addr=addr, **kwds)
        self.srate = 2e9
        self.qacode = ''

    def open(self, **kwds):
        session = Session("localhost")
        self.handle = session.connect_device("DEV12363")

    def close(self, **kwds):
        pass

    def read(self, name, **kwds):
        if name == 'IQ':
            return self.handle.qachannels[0].readout.read()[:2]

        return super().read(name, **kwds)

    def write(self, name, value, **kwds):
        ch = kwds.get('ch', 1) - 1
        if name == 'Waveform':
            sbf = self.getValue('SidebandFrequency')
            if isinstance(value, Waveform):
                t = np.arange(value.start, value.stop, 1 / value.sample_rate)
                weight = value.sample() * np.exp(-2j * np.pi * sbf * t)
                value = value.sample() * np.exp(2j * np.pi * sbf * t)

            nz = np.nonzero(value.real)
            value = value[nz]
            weight = weight[nz]
            if len(value) > int(2e-6 * 2e9):
                print(f"maximum length({len(value)}) exceeded!")
                value = value[:4000]
                weight = weight[:4000]
            fnzp = nz[0][0] - 1
            delay = int((fnzp * 1 / 2e9) / 4e-9) + 1 if fnzp > 0 else 0

            self.execute_qa(value, ch, delay, shots=1024)
            self.setValue('Coefficient', weight)
            # print(type(square_pulse))
            # t = np.arange(value.start,value.stop,1/self.srate)

            # wave[q]= value * np.exp(2j * np.pi * frequency[q] * t + 1j*phase[q])
        elif name == 'CenterFrequency':
            # assert value/200e6
            # 200MHz的整数倍
            self.handle.qachannels[0].centerfreq(value)
        elif name == 'Power':
            self.handle.qachannels[0].input.range(value)
            self.handle.qachannels[0].output.range(value)
        elif name == 'Output':
            self.handle.qachannels[0].input.on(int(value))
            self.handle.qachannels[0].output.on(int(value))

        elif name == 'Shot':
            self.handle.qachannels[0].readout.result.length(value)
            self.handle.system.internaltrigger.repetitions(value)  # ?
        elif name == 'Coefficient':
            wave = Waveforms()
            # data, f_list, numberOfPoints, phases = get_coef(value, self.srate)
            wave[0] = value  # self.getValue('Waveform')
            self.handle.qachannels[0].readout.write_integration_weights(wave)
            self.handle.qachannels[0].readout.integration.delay(200e-9)
        elif name == 'ReferenceClock':
            # internal, external, zsync
            self.handle.system.clocks.referenceclock.in_.source(value)
        elif name == 'TriggerSource':
            # Readout Pulse Generator setting
            # 8 for internal trigger
            self.handle.qachannels[0].generator.auxtriggers[0].channel(value)
        elif name == 'TriggerDelay':
            self.handle.qachannels[0].readout.integration.delay(value)
        elif name == 'CaptureMode':
            pass
        elif name == 'StartCapture':
            # self.handle.qachannels[0].mode(1)  # 1: readout mode 0: spectroscopy mode
            self.handle.qachannels[0].generator.wait_done()
            assert (self.handle.qachannels[0].generator.enable(
                True, deep=True))
            self.handle.qachannels[0].readout.run()
            self.handle.qachannels[0].readout.result.enable(True)
        elif name == 'Trigger':
            self.handle.system.internaltrigger.enable(True)
        return value

    def execute_qa(self, rf_pulse: np.ndarray, channel: int, delay: int, shots: int = 1024):
        qacode = f"""
        repeat({shots}) {{
            waitDigTrigger(1) ;
            //waitZSyncTrigger() ;
            wait({delay}); // 45000ns/4  
            //playZero(90000); 
            //startQA(QA_GEN_ALL, QA_INT_ALL, true, 0, 0x0);
            startQA(QA_GEN_0|QA_GEN_1, QA_INT_0|QA_INT_1, true, 0);
            //startQA(QA_INT_0, QA_INT_0, true, 0);
            }}
        """
        if self.qacode != qacode:
            # shfqc.sgchannels[0].generator.load_sequencer_program(sg_program)
            self.qacode = qacode
            # print(self.qacode)
            self.handle.qachannels[channel].generator.load_sequencer_program(
                self.qacode)  # 先写code 再写wf
        # shfqc.sgchannels[0].generator.load_sequencer_program(sg_program)
        w = Waveforms()
        w[0] = rf_pulse
        self.handle.qachannels[channel].generator.write_to_waveform_memory(w)
        # self.handle.qachannels[channel].generator.load_sequencer_program(
        #     qacode)
