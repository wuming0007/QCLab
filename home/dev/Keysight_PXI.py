import re

from dev.common import BaseDriver, QInteger, QList, QOption, QReal, QVector
from dev.common.Keysight import keysightSD1


class Driver(BaseDriver):

    support_models = ['M3202A', ]

    quants = [
        QReal('Amplitude', value=1, unit='V', ch=1),
        # DC WaveShape
        QReal('Offset', value=0, unit='V', ch=1),
        # Function Generators(FGs) mode
        QReal('Frequency', unit='Hz', ch=1),
        QReal('Phase', value=0, unit='deg', ch=1),

        QOption('WaveShape', ch=1, value='HIZ',
                options=[
                    ('HIZ', keysightSD1.SD_Waveshapes.AOU_HIZ),
                    ('OFF', keysightSD1.SD_Waveshapes.AOU_OFF),
                    ('SINUSOIDAL', keysightSD1.SD_Waveshapes.AOU_SINUSOIDAL),
                    ('TRIANGULAR', keysightSD1.SD_Waveshapes.AOU_TRIANGULAR),
                    ('SQUARE', keysightSD1.SD_Waveshapes.AOU_SQUARE),
                    ('DC', keysightSD1.SD_Waveshapes.AOU_DC),
                    ('AWG', keysightSD1.SD_Waveshapes.AOU_AWG),
                    ('PARTNER', keysightSD1.SD_Waveshapes.AOU_PARTNER)
                ]),
        # clock
        QReal('clockFrequency', unit='Hz'),
        QReal('clockSyncFrequency', unit='Hz'),
        # 板卡向外输出的时钟，默认状态关闭
        QOption('clockIO', value='OFF', options=[('OFF', 0), ('ON', 1)]),
        QOption('triggerIO', value='SyncIN',
                options=[('noSyncOUT', (0, 0)),
                         ('SyncOUT', (0, 1)),
                         ('noSyncIN', (1, 0)),
                         ('SyncIN', (1, 1))]),

        QOption('triggerMode', value='EXTTRIG_CYCLE', ch=1,
                options=[
                    ('AUTOTRIG', keysightSD1.SD_TriggerModes.AUTOTRIG),
                    ('VIHVITRIG', keysightSD1.SD_TriggerModes.VIHVITRIG),
                    ('SWHVITRIG', keysightSD1.SD_TriggerModes.SWHVITRIG),
                    ('EXTTRIG', keysightSD1.SD_TriggerModes.EXTTRIG),
                    ('ANALOGTRIG', keysightSD1.SD_TriggerModes.ANALOGTRIG),
                    ('SWHVITRIG_CYCLE',
                     keysightSD1.SD_TriggerModes.SWHVITRIG_CYCLE),
                    ('EXTTRIG_CYCLE',
                     keysightSD1.SD_TriggerModes.EXTTRIG_CYCLE),
                    ('ANALOGAUTOTRIG',
                     keysightSD1.SD_TriggerModes.ANALOGAUTOTRIG),
                ]),
        QOption('triExtSource', value='PXI1', ch=1,
                options=[
                    ('EXTERN', keysightSD1.SD_TriggerExternalSources.TRIGGER_EXTERN),
                    ('PXI0', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI0),
                    ('PXI1', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI1),
                    ('PXI2', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2),
                    ('PXI3', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI3),
                    ('PXI4', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI4),
                    ('PXI5', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI5),
                    ('PXI6', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI6),
                    ('PXI7', keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI7)
                ]),
        QOption('triggerBehavior', value='RISE', ch=1,
                options=[
                    ('NONE', keysightSD1.SD_TriggerBehaviors.TRIGGER_NONE),
                    ('HIGH', keysightSD1.SD_TriggerBehaviors.TRIGGER_HIGH),
                    ('LOW', keysightSD1.SD_TriggerBehaviors.TRIGGER_LOW),
                    ('RISE', keysightSD1.SD_TriggerBehaviors.TRIGGER_RISE),
                    ('FALL', keysightSD1.SD_TriggerBehaviors.TRIGGER_FALL),
                ]),
        # Defines the delay between the trigger and the waveform launch in tens of ns
        QInteger('startDelay', value=0, unit='ns', ch=1, ),
        # Number of times the waveform is repeated once launched (negative means infinite)
        QInteger('cycles', value=0, ch=1,),
        # Waveform prescaler value, to reduce the effective sampling rate
        QInteger('prescaler', value=0, ch=1,),

        QOption('Output', ch=1, value='Close', options=[('Stop', 0), ('Run', 1),
                                                        ('Pause',
                                                         2), ('Resume', 3),
                                                        ('Close', -1)]),
        QList('WList', value=[]),
        QList('SList', value=[], ch=1),

        QVector('Waveform', value=[], ch=1)
    ]
    # CHs : 仪器通道
    CHs = [1, 2, 3, 4]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.timeout = 10

    def open(self):
        # SD_AIN/SD_AOU module
        dict_parse = self._parse_addr(self.addr)
        CHASSIS = dict_parse.get('CHASSIS')  # default 1
        SLOT = dict_parse.get('SLOT')

        self.CHASSIS = CHASSIS
        self.SLOT = SLOT

        SD_M = keysightSD1.SD_Module()
        self.model = SD_M.getProductNameBySlot(CHASSIS, SLOT)
        if self.model in ['M3102A']:
            self.handle = keysightSD1.SD_AIN()
        elif self.model in ['M3202A']:
            self.handle = keysightSD1.SD_AOU()
        else:
            raise Exception(
                f"Model '{self.model}' not support by this Driver!")
        moduleID = self.handle.openWithSlot(self.model, CHASSIS, SLOT)
        if moduleID < 0:
            print("Module open error:", moduleID)

        for ch in self.CHs:
            self.setValue('WaveShape', 'AWG', ch=ch)

    def close(self):
        """Perform the close instrument connection operation"""
        # refer labber driver keysight_pxi_awg.py
        # do not check for error if close was called with an error
        try:
            self.setValue('clockIO', 'OFF')
            # clear old waveforms and stop awg
            self.waveformFlush()
            for ch in self.CHs:
                self.closeCh(ch)
            # close instrument
            # self.handle.close()
        except Exception:
            # never return error here
            pass

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name == 'Amplitude':
            self.handle.channelAmplitude(ch, value)
        elif name == 'Offset':
            self.handle.channelOffset(ch, value)
        elif name == 'Frequency':
            self.handle.channelFrequency(ch, value)
        elif name == 'Phase':
            self.phaseReset(ch)
            self.handle.channelPhase(ch, value)
        elif name == 'WaveShape':
            options = dict(self.quantities[name])
            self.handle.channelWaveShape(ch, options[value])
        elif name == 'clockFrequency':
            mode = kw.get('mode', 1)
            self.handle.clockSetFrequency(value, mode)
        elif name == 'clockIO':
            options = dict(self.quantities[name])
            self.handle.clockIOconfig(options[value])
        elif name == 'triggerIO':
            options = dict(self.quantities[name])
            self.handle.triggerIOconfigV5(options[value])
        elif name == 'Output':
            if value == 'Stop':
                self.handle.AWGstop(ch)
            elif value == 'Run':
                self.handle.AWGstart(ch)
            elif value == 'Pause':
                self.handle.AWGpause(ch)
            elif value == 'Resume':
                self.handle.AWGresume(ch)
            elif value == 'Close':
                self.closeCh(ch)
        elif name == 'clockSyncFrequency':
            raise Exception("clockSyncFrequency can't be set")
        elif name == 'Waveform':
            self.AWGrun(value, ch=ch)

        return value

    def read(self, name: str, **kw):
        if name == 'clockFrequency':
            return self.handle.clockGetFrequency()
        elif name == 'clockSyncFrequency':
            return self.handle.clockGetSyncFrequency()
        else:
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def _parse_addr(self, addr):
        re_addr = re.compile(
            r'^(PXI)[0-9]?::CHASSIS([0-9]*)::SLOT([0-9]*)::INDEX([0-9]*)::INSTR$')
        m = re_addr.search(addr)
        if m is None:
            raise Exception('Address error!')
        CHASSIS = int(m.group(2))
        SLOT = int(m.group(3))
        return dict(CHASSIS=CHASSIS, SLOT=SLOT)

    def closeCh(self, ch=1):
        self.handle.AWGstop(ch)
        self.handle.AWGflush(ch)
        self.config['SList'][ch]['value'] = []
        self.handle.channelWaveShape(ch, -1)
        self.config['WaveShape'][ch]['value'] = 'HIZ'
        self.config['Output'][ch]['value'] = 'Close'

    def phaseReset(self, ch=1):
        self.handle.channelPhaseReset(ch)

    def clockResetPhase(self):
        # self.handle.clockResetPhase(triggerBehavior, triggerSource, skew = 0.0)
        pass

    def newWaveform(self, file_arrayA, arrayB=None, waveformType=0):
        '''Memory usage: Waveforms created with New are stored in the PC RAM,
        not in the module onboard RAM. Therefore, the limitation in the number
        of waveforms and their sizes is given by the amount of PC RAM.'''
        # waveformType 0: Analog 16Bits, Analog normalized waveforms (-1..1) defined with doubles
        # please refer AWG Waveform types about others
        wave = keysightSD1.SD_Wave()
        if isinstance(file_arrayA, str):
            wave.newFromFile(file_arrayA)
            return wave
        else:
            # 5: DigitalType, Digital waveforms defined with integers
            if waveformType == 5:
                wave.newFromArrayInteger(waveformType, file_arrayA, arrayB)
            else:
                wave.newFromArrayDouble(waveformType, file_arrayA, arrayB)
            return wave

    def waveformLoad(self, waveform, num, paddingMode=0):
        '''num: waveform_num, 在板上内存的波形编号'''
        if num in self.config['WList']['global']['value']:
            self.handle.waveformReLoad(waveform, num, paddingMode)
        else:
            # This function replaces a waveform located in the module onboard RAM.
            # The size of the newwaveform must be smaller than or equal to the existing waveform.
            self.handle.waveformLoad(waveform, num, paddingMode)
            self.config['WList']['global']['value'].append(num)

    # def waveformReLoad(self, waveform, num, paddingMode = 0):
    #     '''This function replaces a waveform located in the module onboard RAM.
    #     The size of the newwaveform must be smaller than or equal to the existing waveform.'''
    #     self.handle.waveformReLoad(waveform, num, paddingMode)

    def waveformFlush(self):
        '''This function deletes all the waveforms from the module onboard RAM
        and flushes all the AWG queues'''
        self.handle.waveformFlush()
        self.config['WList']['global']['value'] = []
        for ch in self.CHs:
            self.config['SList'][ch]['value'] = []

    def AWGflush(self, ch=1):
        '''This function empties the queue of the selected Arbitrary Waveform Generator,
        Waveforms are not removed from the module onboard RAM.'''
        self.handle.AWGflush(ch)
        self.config['SList'][ch]['value'] = []

    def _getParams(self, ch):
        triggerModeIndex = self.getValue('triggerMode', ch=ch)
        triggerModeOptions = self.quantities['triggerMode'].options
        triggerMode = dict(triggerModeOptions)[triggerModeIndex]

        if triggerModeIndex in ['EXTTRIG', 'EXTTRIG_CYCLE']:

            triExtSourceIndex = self.getValue('triExtSource', ch=ch)
            triExtSourceOptions = self.quantities['triExtSource'].options
            triExtSource = dict(triExtSourceOptions)[triExtSourceIndex]
            if triExtSourceIndex in ['EXTERN']:
                # 若未设置过，则从config读取默认配置；若已设置，则结果不变
                triggerIO = self.getValue('triggerIO')
                self.setValue('triggerIO', triggerIO)

            triggerBehaviorIndex = self.getValue('triggerBehavior', ch=ch)
            triggerBehaviorOptions = self.quantities['triggerBehavior'].options
            triggerBehavior = dict(triggerBehaviorOptions)[
                triggerBehaviorIndex]

            self.handle.AWGtriggerExternalConfig(
                ch, triExtSource, triggerBehavior)

        startDelay = self.getValue('startDelay', ch=ch)
        cycles = self.getValue('cycles', ch=ch)
        prescaler = self.getValue('prescaler', ch=ch)

        return triggerMode, startDelay, cycles, prescaler

    def AWGqueueWaveform(self, ch=1, waveform_num=0):
        self.setValue('WaveShape', 'AWG', ch=ch)
        Amplitude = self.getValue('Amplitude', ch=ch)
        self.setValue('Amplitude', Amplitude, ch=ch)

        triggerMode, startDelay, cycles, prescaler = self._getParams(ch)

        self.handle.AWGqueueWaveform(
            ch, waveform_num, triggerMode, startDelay, cycles, prescaler)
        self.config['SList'][ch]['value'].append(waveform_num)

    def AWGrun(self, file_arrayA, arrayB=None, ch=1, waveformType=0, paddingMode=0):
        '''从文件或序列快速产生波形'''
        self.setValue('WaveShape', 'AWG', ch=ch)
        Amplitude = self.getValue('Amplitude', ch=ch)
        self.setValue('Amplitude', Amplitude, ch=ch)

        triggerMode, startDelay, cycles, prescaler = self._getParams(ch)

        if isinstance(file_arrayA, str):
            # AWGFromFile 有bug
            r = self.handle.AWGFromFile(
                ch, file_arrayA, triggerMode, startDelay, cycles, prescaler, paddingMode)
        else:
            r = self.handle.AWGfromArray(
                ch, triggerMode, startDelay, cycles, prescaler, waveformType, file_arrayA, arrayB, paddingMode)
        self.config['Output'][ch]['value'] = 'Run'
        return r
