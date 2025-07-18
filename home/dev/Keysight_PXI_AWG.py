import re

import numpy as np

from dev.common import BaseDriver, QInteger, QList, QOption, QReal, QVector
from dev.common.Keysight import keysightSD1


class Driver(BaseDriver):

    support_models = ['M3202A', ]
    # CHs : 仪器通道
    CHs = [1, 2, 3, 4]

    quants = [
        # 经测试，M3202A板卡最大Amplitude约1.5V左右
        QReal('Amplitude', value=1.5, unit='V', ch=1),
        QReal('Offset', value=0, unit='V', ch=1),  # 经测试，M3202A板卡最大offset约1.4左右
        QReal('OffsetDC', value=0, unit='V', ch=1),
        QOption('Output', ch=1, value='ON',
                options=[
                    ('ON', 1),
                    ('OFF', 0),
                ]),
        QVector('Waveform', value=[], ch=1),
        # Defines the delay between the trigger and the waveform launch in tens of ns
        QInteger('startDelay', value=0, unit='ns', ch=1, ),
        # Number of times the waveform is repeated once launched (negative means infinite)
        QInteger('Shot', value=0, ch=1,),  # NOTE: cycles

        # Function Generators(FGs) mode
        QReal('Frequency', unit='Hz', ch=1),
        QReal('Phase', value=0, unit='deg', ch=1),

        QOption('Run State', ch=1, value='Close',
                options=[
                    ('Stop', 0), ('Run', 1),
                    ('Pause', 2), ('Resume', 3),
                    ('Close', -1)
                ]),
        QOption('WaveShape', ch=1, value='AWG',
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
        # QOption('triggerIO', value='SyncIN',
        #                     options = [('noSyncOUT', (0,0)),
        #                                ('SyncOUT',   (0,1)),
        #                                ('noSyncIN',  (1,0)),
        #                                ('SyncIN',    (1,1))]),
        QOption('triggerIO', value='OUT',
                options=[  # 0:output, 1: input
                    ('OUT', keysightSD1.SD_TriggerDirections.AOU_TRG_OUT),
                    ('IN', keysightSD1.SD_TriggerDirections.AOU_TRG_IN),
                ]),

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
        QOption('Ext triggerSource', value='PXI0', ch=1,
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

        # Waveform prescaler value, to reduce the effective sampling rate
        QInteger('prescaler', value=0, ch=1,),
        QList('WList', value=[]),
        QList('SList', value=[], ch=1),
    ]

    # 设备网段
    segment = ('na', '103')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.timeout = 10
        self.srate = 1e9
        self.addr = '192.168.103.2'
        self._addr = addr

    def open(self):
        self.addr = self._addr
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

        self.open_init()

    def close(self):
        """Perform the close instrument connection operation"""
        # refer labber driver keysight_pxi_awg.py
        # do not check for error if close was called with an error
        try:
            self.handle.close()
        except Exception:
            # never return error here
            pass

    # def close(self):
    #     """Perform the close instrument connection operation"""
    #     # refer labber driver keysight_pxi_awg.py
    #     # do not check for error if close was called with an error
    #     try:
    #         super().close()
    #         # self.setValue('clockIO','OFF')
    #         # clear old waveforms and stop awg
    #         # self.waveformFlush()
    #         # for ch in self.CHs:
    #         #     self.closeCh(ch)
    #         # close instrument
    #         # self.handle.close()
    #         pass
    #     except:
    #         pass

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name == 'Amplitude':
            self.handle.channelAmplitude(ch, value)
        elif name == 'Offset':
            self.handle.channelOffset(ch, value)
        elif name == 'OffsetDC':
            v = np.ones(1000) * value
            self.setValue('triggerMode', 'AUTOTRIG', ch=ch)
            self.setWaveform(v, ch)
        elif name == 'Frequency':
            self.handle.channelFrequency(ch, value)
        elif name == 'Phase':
            self.phaseReset(ch)
            self.handle.channelPhase(ch, value)
        elif name == 'WaveShape':
            options = dict(self.quantities[name].options)
            self.handle.channelWaveShape(ch, options[value])
        elif name == 'clockFrequency':
            mode = kw.get('mode', 1)
            self.handle.clockSetFrequency(value, mode)
        elif name == 'clockIO':
            options = dict(self.quantities[name].options)
            self.handle.clockIOconfig(options[value])
        elif name == 'triggerIO':
            options = dict(self.quantities[name].options)
            self.handle.triggerIOconfigV5(options[value], syncMode=0)
        elif name == 'Run State':
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
            # path = self.createWaveformFile(value, ch)
            # self.AWGrun(path, ch=ch)
            # self.AWGrun(value, ch=ch)
            self.setWaveform(value, ch)
            # pass
        elif name in ['Ext triggerSource', 'triggerBehavior']:
            Ext_triSourceIndex = self.config['Ext triggerSource'][ch]['value']
            Ext_triSource = self.quantities['Ext triggerSource'].options[Ext_triSourceIndex]
            triggerBehaviorIndex = self.config['triggerBehavior'][ch]['value']
            triggerBehavior = self.quantities['triggerBehavior'].options[triggerBehaviorIndex]
            self.handle.AWGtriggerExternalConfig(
                ch, Ext_triSource, triggerBehavior)
        else:
            super().write(name, value, **kw)

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

    def open_init(self):
        self.waveformFlush()
        for ch in self.CHs:
            WaveShape = self.config['WaveShape'][ch]['value']
            self.setValue('WaveShape', WaveShape, ch=ch)
            Amplitude = self.config['Amplitude'][ch]['value']
            self.setValue('Amplitude', Amplitude, ch=ch)
            Offset = self.config['Offset'][ch]['value']
            self.setValue('Offset', Offset, ch=ch)
            Offset = self.config['Phase'][ch]['value']
            self.setValue('Phase', Offset, ch=ch)

            triggerIO = self.config['triggerIO'][ch]['value']
            self.setValue('triggerIO', triggerIO)
            triggerMode = self.config['triggerMode'][ch]['value']
            self.setValue('triggerMode', triggerMode, ch=ch)

            Ext_triSourceIndex = self.config['Ext triggerSource'][ch]['value']
            Ext_triSource = self.quantities['Ext triggerSource'].options[Ext_triSourceIndex]
            triggerBehaviorIndex = self.config['triggerBehavior'][ch]['value']
            triggerBehavior = self.quantities['triggerBehavior'].options[triggerBehaviorIndex]
            self.handle.AWGtriggerExternalConfig(
                ch, Ext_triSource, triggerBehavior)

    def closeCh(self, ch=1):
        self.AWGflush(ch)
        self.setValue('Run State', 'Close', ch=ch)
        self.setValue('WaveShape', 'HIZ', ch=ch)

    def phaseReset(self, ch=1):
        self.handle.channelPhaseReset(ch)

    def clockResetPhase(self):
        # self.handle.clockResetPhase(triggerBehavior, triggerSource, skew = 0.0)
        pass

    # def afterSet(self):
    #     self.waveformFlush()
    #     # mask = 0
    #     for ch in self.CHs:
    #         value = self.config['Waveform'][ch]['value']
    #         if value is None:
    #             continue
    #         # mask |= 1 << (ch-1)
    #         self.handle.AWGflush(ch)
    #         waveform = self.newWaveform(value)
    #         self.waveformLoad(waveform, num=ch)
    #         self.AWGqueueWaveform(ch, waveform_num=ch)
    #     self.handle.AWGstartMultiple(0xf)
    #     # self.handle.AWGstartMultiple(mask)

    def setWaveform(self, value, ch):
        self.handle.AWGflush(ch)
        waveform = self.newWaveform(value)
        self.waveformLoad(waveform, num=ch)
        self.AWGqueueWaveform(ch, waveform_num=ch)
        self.handle.AWGstart(ch)

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
                if np.max(file_arrayA) > 1 or np.min(file_arrayA) < -1:
                    import warnings
                    warnings.warn('waveform overflow.')
                file_arrayA = np.clip(file_arrayA, -1, 1)
                wave.newFromArrayDouble(waveformType, file_arrayA, arrayB)
            return wave

    def waveformLoad(self, waveform, num, paddingMode=0):
        '''num: waveform_num, 在板上内存的波形编号'''
        if num in self.config['WList']['global']['value']:
            error = self.handle.waveformReLoad(waveform, num, paddingMode)
            if error < 0:
                raise Exception(
                    f'waveformReLoad(input_waveform, {num}, {paddingMode}) returned error: {error}')
        else:
            # This function replaces a waveform located in the module onboard RAM.
            # The size of the newwaveform must be smaller than or equal to the existing waveform.
            error = self.handle.waveformLoad(waveform, num, paddingMode)
            if error < 0:
                raise Exception(
                    f'waveformLoad(input_waveform, {num}, {paddingMode}) returned error: {error}')
            self.config['WList']['global']['value'].append(num)

    def createWaveformFile(self, value, ch):
        fname = f'SLOT{self.SLOT}CH{ch}.csv'
        from pathlib import Path
        path = Path(r'C:\ProgramData\QuLab\cache\keysight') / fname

        header = [f"waveformName,{fname}",
                  f"waveformPoints,{len(value)}",
                  "waveformType,WAVE_ANALOG_16"]
        body = [str(v) for v in value]
        header.extend(body)
        path.write_text('\n'.join(header))
        return str(path)

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
        triggerModeIndex = self.config['triggerMode'][ch]['value']
        triggerMode = self.quantities['triggerMode'].options[triggerModeIndex]
        startDelay = self.config['startDelay'][ch]['value']
        shots = self.config['Shot'][ch]['value']
        prescaler = self.config['prescaler'][ch]['value']
        return triggerMode, startDelay, shots, prescaler

    def AWGqueueWaveform(self, ch=1, waveform_num=0):
        self.setValue('WaveShape', 'AWG', ch=ch)
        triggerMode, startDelay, shots, prescaler = self._getParams(ch)

        self.handle.AWGqueueWaveform(
            ch, waveform_num, triggerMode, startDelay, shots, prescaler)
        self.config['SList'][ch]['value'].append(waveform_num)

    def AWGrun(self, file_arrayA, arrayB=None, ch=1, waveformType=0, paddingMode=0):
        '''从文件或序列快速产生波形'''
        self.setValue('WaveShape', 'AWG', ch=ch)
        triggerMode, startDelay, shots, prescaler = self._getParams(ch)

        if isinstance(file_arrayA, str):
            # AWGFromFile 有bug
            error = self.handle.AWGFromFile(
                ch, file_arrayA, triggerMode, startDelay, shots, prescaler, paddingMode)
            if error < 0:
                print(f"AWG (slot{self.SLOT} ch{ch}) from File error:", error)
            else:
                # print("AWG from File started successfully")
                pass
        else:
            error = self.handle.AWGfromArray(
                ch, triggerMode, startDelay, shots, prescaler, waveformType, file_arrayA, arrayB, paddingMode)
            if error < 0:
                print(f"AWG (slot{self.SLOT} ch{ch}) from array error:", error)
            else:
                # print("AWG from array started successfully")
                pass
        self.config['Run State'][ch]['value'] = 'Run'
        return error
