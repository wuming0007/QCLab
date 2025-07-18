from dev.common import BaseDriver, QInteger, QList, QReal
from dev.common.PG import AWGboard


class Driver(BaseDriver):

    support_models = ['PGAWG']

    CHs = [1, 2, 3, 4]

    quants = [
        QReal('Offset', value=0, unit='V', ch=1,),
        QReal('Amplitude', value=1.351, unit='V', ch=1,),
        QInteger('Output', value=1, ch=1,),
        QList('Waveform', value=[], ch=1,),
        QList('Marker1', value=None, ch=1,),

        QReal('TriggerDelay', value=0, unit='s', ch=1,),

        QReal('OffsetDC', value=0, unit='V', ch=1,),
    ]

    segment = ('mf', '104|105|106')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'PGAWG'
        self.srate = 2e9

    def open(self):
        self.handle = AWGboard.AWGBoard()
        self.handle.connect(self.addr)
        self.handle.InitBoard()
        self._output_status = [0, 0, 0, 0]
        self.init_output()

        self.handle.mark_is_in_wave = True

        import numpy as np

        for ch in self.CHs:
            self.setValue('Waveform', np.zeros([1000]), ch=ch)

    def close(self):
        # self.handle.disconnect()
        pass

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name == 'Offset':
            self.setOffset(value, ch)
        elif name == 'Amplitude':
            self.setVpp(value, ch)
        elif name == 'Output':
            if value == 1 or value == 'ON':
                self.on(ch)
            elif value == 0 or value == 'OFF':
                self.off(ch)
            else:
                raise Exception(f'Output: {value}, Wrong Value!')
        elif name == 'Waveform':
            assert len(value) <= int(99e-6 * self.srate), 'Wave is too long!'
            if self.handle.mark_is_in_wave:
                mk1 = self.config['Marker1'][ch]['value']
                if mk1 is None or len(mk1) != len(value):
                    mk1 = value * 0
            else:
                mk1 = None
            delay = self.config['TriggerDelay'][ch]['value']
            if mk1 is None:
                self.setWaveform(value, ch=ch, delay=delay)
            else:
                self.setWaveform(value, ch=ch, mk1=1 * (mk1 > 0), delay=delay)
        elif name == 'Marker1':
            if self.handle.mark_is_in_wave:
                wf = self.config['Waveform'][ch]['value']
                if wf is None or len(wf) != len(value):
                    wf = value * 0
                self.setWaveform(wf, ch=ch, mk1=1 * (value > 0))
            else:
                pass
        elif name == 'OffsetDC':
            self.setOffsetDC(value, ch=ch)
        else:
            super().write(name, value, ch=1, **kw)

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def set_mark_is_in_wave(self, v=False):
        self.handle.mark_is_in_wave = v

    def init_output(self):
        for ch in self.CHs:
            self.on(ch)
            self.setOffset(0, ch)
            self.setVpp(1.351, ch)
            # self.setWaveform(value,ch=ch,mk1=1*(mk1>0),delay=delay)
            self.handle.SetOutputKeep(ch, 1)

    def on(self, ch=1):
        self.handle.Start(ch)
        self._output_status[ch - 1] = 1

    def off(self, ch=1):
        self.handle.Stop(ch)
        self._output_status[ch - 1] = 0

    def setWaveform(self,
                    points,
                    ch=1,
                    wtype='trig',
                    delay=0,
                    mk1=None,
                    is_continue=False):
        if self.handle.mark_is_in_wave:
            wlist = [self.handle.gen_wave_unit(points, wtype, delay, mk1)]
        else:
            wlist = [self.handle.gen_wave_unit(points, wtype, delay)]
        self.handle.wave_compile(ch, wlist, is_continue=is_continue)
        self.handle.SetLoop(ch, 2000000000)  # 默认播放2e9次，5k触发下约100个多小时
        for index, on in enumerate(self._output_status):
            if on:
                self.handle.Start(index + 1)

    def setVpp(self, vpp, ch=1):
        vpp = min(abs(vpp), 1.351)
        volt = 1.351
        gain = vpp / volt
        # self.handle.set_channel_gain(ch, gain)
        self.handle._SetDACMaxVolt(ch, volt)
        self.handle.SetAmpGain(ch, gain)

    def setOffset(self, offs, ch=1):
        self.handle.SetOffsetVolt(ch, offs)

    def setOffsetDC(self, offs_dc, ch=1):
        '''offs_dc: 为(-1, 1)之间的值'''
        if self.handle.mark_is_in_wave:
            mk1 = [0] * 32
        else:
            mk1 = None
        self.setWaveform([offs_dc] * 32, ch=ch,
                         wtype='continue', mk1=mk1, is_continue=True)
