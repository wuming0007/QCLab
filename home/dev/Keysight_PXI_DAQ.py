
import re

import numpy as np

from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,
                        QVector, get_coef)
from dev.common.Keysight import keysightSD1


class Driver(BaseDriver):

    support_models = ['M3102A', ]

    CHs = [1, 2, 3, 4]

    quants = [
        QInteger('PointNumber', value=1024, ch=1, unit='point',),
        QInteger('TriggerDelay', value=0, ch=1, unit='point',),
        QReal('Shot', value=512, ch=1),  # Number of times read repeated
        QBool('avg', value=False, ch=1),
        QVector('TraceIQ', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QList('FrequencyList', value=[], ch=1),
        QList('Coefficient', value=None, ch=1),

        QInteger('StartCapture', value=1, ch=1,),  # 采集模式：0连续，1触发
        QOption('CaptureMode', value=1, ch=1, options=[
                # 采集模式：0连续，1触发
                ('raw', 'raw'), ('alg', 'alg'), ('raw_alg', 'raw_alg')]),

        QVector('Trace', value=[], ch=1),
        QReal('fullScale', value=1, unit='V', ch=1),
        QOption('Coupling', value='DC', ch=1,
                options=[('DC', keysightSD1.AIN_Coupling.AIN_COUPLING_DC),
                         ('AC', keysightSD1.AIN_Coupling.AIN_COUPLING_AC)]),
        QOption('Impedance', value='50', ch=1,
                options=[('HZ', keysightSD1.AIN_Impedance.AIN_IMPEDANCE_HZ),
                         ('50', keysightSD1.AIN_Impedance.AIN_IMPEDANCE_50)]),

        # 板卡向外输出的时钟，默认状态关闭
        QOption('clockIO', value='OFF', options=[('OFF', 0), ('ON', 1)]),
        #     QOption('triggerIO', value='SyncIN',
        #                         options = [('noSyncOUT', (0,0)),
        #                                    ('SyncOUT',   (0,1)),
        #                                    ('noSyncIN',  (1,0)),
        #                                    ('SyncIN',    (1,1))]),
        QOption('triggerIO', value='IN',
                options=[  # 0:output, 1: input
                    ('OUT', keysightSD1.SD_TriggerDirections.AOU_TRG_OUT),
                    ('IN', keysightSD1.SD_TriggerDirections.AOU_TRG_IN),
                ]),
        # Analog Trigger Mode
        # NOTE: The analog trigger block processes the input data and generates a digital trigger that can be used by any Data Acquisition Block
        QOption('Analog triggerMode', value='RISING_EDGE', ch=1,
                options=[
                    ('RISING_EDGE', keysightSD1.SD_AIN_TriggerMode.RISING_EDGE),
                    ('FALLING_EDGE',
                     keysightSD1.SD_AIN_TriggerMode.FALLING_EDGE),
                    ('BOTH_EDGES', keysightSD1.SD_AIN_TriggerMode.BOTH_EDGES),
                ]),
        QReal('Analog Threshold', value=0.5, unit='V', ch=1),


        # DAQ Trigger Mode
        # NOTE: M3102A 不支持 analog trigger (HWANATRIG)
        # NOTE: analog trigger block 和 analog hardware trigger (HWANATRIG) 不同
        QOption('DAQ triggerMode', value='HWDIGTRIG', ch=1,  # 常规模式下，使用HWDIGTRIG模式
                options=[
                    ('AUTOTRIG', 0),  # start after DAQstart function
                    # ('SWtri',        1),   #start after DAQtrigger function or HVI programm
                    ('SWHVITRIG1', 1),
                    ('HWDIGTRIG', 2),  # ('HWDIGtri',     2),   #external trigger
                    # ('HWANAtri',     3)    #M3102A不支持这种模式
                    ('HWANATRIG', 3),
                ]),
        # DAQ Hardware Digital Trigger Source
        # 说明书中触发源编号
        # QOption('HWDIG triggerSource', value='EXTERNAL', ch=1,  # only used when trigger mode in HWIDGtri
        #                      options = [('EXTERNAL', 0),
        #                                 ('PXI', 1)]),
        # 经测试可以执行的触发源编号
        QOption('HWDIG triggerSource', value='PXI0', ch=1,
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
        # DAQ Hardware Digital Trigger Behaviour
        QOption('HWDIG triggerBehavior', value='RISE', ch=1,  # only used when trigger mode in HWIDGtri
                options=[
                    ('HIGH', 1),
                    ('LOW', 2),
                    ('RISE', 3),
                    ('FALL', 4),
                ]),

        # NOTE: The prescaler is used to reduce the effective input sampling rate, capturing 1 out of n samples and
        # discarding the rest. The resulting sampling rate is as follows:
        # fs = fCLKsys/(1+prescaler)
        QInteger('prescaler', value=0, ch=1,),
    ]

    # 设备网段
    segment = ('na', '103')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.timeout = 10
        self.srate = 500e6
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
        return super().close()

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        self.config[name][ch]['value'] = value  # 更新到config

        if name in ['PointNumber', 'Shot', 'TriggerDelay', 'DAQ triggerMode']:
            pointNum = self.config['PointNumber'][ch]['value']
            shots = self.config['Shot'][ch]['value']
            triggerDelay = round(
                self.config['TriggerDelay'][ch]['value'] * self.srate)
            triggerModeIndex = self.config['DAQ triggerMode'][ch]['value']
            triggerMode = self.quantities['DAQ triggerMode'].options.get(
                triggerModeIndex)
            for _ch in [ch, ch + 1]:
                self.config[name][_ch]['value'] = value  # 更新到config
                self.handle.DAQconfig(
                    _ch, pointNum, shots, triggerDelay, triggerMode)
        elif name in ['HWDIG triggerSource', 'HWDIG triggerBehavior',]:
            triggerSourceIndex = self.config['HWDIG triggerSource'][ch]['value']
            triggerSource = self.quantities['HWDIG triggerSource'].options.get(
                triggerSourceIndex)
            triggerBehaviourIndex = self.config['HWDIG triggerBehavior'][ch]['value']
            triggerBehaviour = self.quantities['HWDIG triggerBehavior'].options.get(
                triggerBehaviourIndex)
            for _ch in [ch, ch + 1]:
                self.config[name][_ch]['value'] = value  # 更新到config
                self.handle.DAQdigitalTriggerConfig(
                    _ch, triggerSource, triggerBehaviour)
        elif name in ['Analog triggerMode', 'Analog Threshold',]:
            atriggerModeIndex = self.config['Analog triggerMode'][ch]['value']
            atriggerMode = self.quantities['Analog triggerMode'].options.get(
                atriggerModeIndex)
            Threshold = self.config['Analog Threshold'][ch]['value']
            for _ch in [ch, ch + 1]:
                self.config[name][_ch]['value'] = value  # 更新到config
                self.handle.channelTriggerConfig(_ch, atriggerMode, Threshold)
        elif name in ['fullScale', 'Coupling', 'Impedance']:
            fullScale = self.config['fullScale'][ch]['value']
            ImpedanceIndex = self.config['Impedance'][ch]['value']
            Impedance = self.quantities['Impedance'].options.get(
                ImpedanceIndex)
            CouplingIndex = self.config['Coupling'][ch]['value']
            Coupling = self.quantities['Coupling'].options.get(CouplingIndex)
            for _ch in [ch, ch + 1]:
                self.config[name][_ch]['value'] = value  # 更新到config
                self.handle.channelInputConfig(
                    _ch, fullScale, Impedance, Coupling)
        elif name in ['prescaler',]:
            for _ch in [ch, ch + 1]:
                self.config[name][_ch]['value'] = value  # 更新到config
                self.handle.channelPrescalerConfig(_ch, value)
        elif name in ['triggerIO',]:
            options = dict(self.quantities[name])
            self.handle.triggerIOconfig(options[value])
        elif name == 'clockIO':
            options = dict(self.quantities[name])
            self.handle.clockIOconfig(options[value])
        elif name in ['Coefficient',]:
            data, f_list, numberOfPoints, phases = get_coef(value, self.srate)
            for _ch in [ch, ch + 1]:
                self.config[name][_ch]['value'] = data  # 更新到config
            self.write('PointNumber', numberOfPoints)
            return data
        elif name in ['StartCapture', 'CaptureMode']:
            pass
        else:
            super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        ch = kw.get('ch', 1)
        avg = self.config['avg'][ch]['value']
        if name == 'Trace':
            return self.getTraces(ch=ch, avg=avg, timeout=None)
        # elif name == 'TraceIQ':
        #     return self.dataRead(ch=ch), self.dataRead(ch=ch+1)
        if name in ['TraceIQ']:
            A = self.getTraces(ch=ch, avg=avg, timeout=None, capture=True)
            B = self.getTraces(ch=ch + 1, avg=avg, timeout=None, capture=False)
            return A, B
        elif name in ['IQ']:
            A = self.getIQ(ch=ch, avg=avg, timeout=None, capture=True)
            B = self.getIQ(ch=ch + 1, avg=avg, timeout=None, capture=False)
            return A, B
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
        for ch in self.CHs:
            pointNum = self.config['PointNumber'][ch]['value']
            shots = self.config['Shot'][ch]['value']
            triggerDelay = self.config['TriggerDelay'][ch]['value']
            triggerModeIndex = self.config['DAQ triggerMode'][ch]['value']
            triggerMode = self.quantities['DAQ triggerMode'].options.get(
                triggerModeIndex)
            self.handle.DAQconfig(ch, pointNum, shots,
                                  triggerDelay, triggerMode)

            triggerSourceIndex = self.config['HWDIG triggerSource'][ch]['value']
            triggerSource = self.quantities['HWDIG triggerSource'].options.get(
                triggerSourceIndex)
            triggerBehaviourIndex = self.config['HWDIG triggerBehavior'][ch]['value']
            triggerBehaviour = self.quantities['HWDIG triggerBehavior'].options.get(
                triggerBehaviourIndex)
            self.handle.DAQdigitalTriggerConfig(
                ch, triggerSource, triggerBehaviour)

            atriggerModeIndex = self.config['Analog triggerMode'][ch]['value']
            atriggerMode = self.quantities['Analog triggerMode'].options.get(
                atriggerModeIndex)
            Threshold = self.config['Analog Threshold'][ch]['value']
            self.handle.channelTriggerConfig(ch, atriggerMode, Threshold)

            fullScale = self.config['fullScale'][ch]['value']
            ImpedanceIndex = self.config['Impedance'][ch]['value']
            Impedance = self.quantities['Impedance'].options.get(
                ImpedanceIndex)
            CouplingIndex = self.config['Coupling'][ch]['value']
            Coupling = self.quantities['Coupling'].options.get(CouplingIndex)
            self.handle.channelInputConfig(ch, fullScale, Impedance, Coupling)

            prescaler = self.config['prescaler'][ch]['value']
            self.handle.channelPrescalerConfig(ch, prescaler)

            triggerIOIndex = self.config['triggerIO'][ch]['value']
            triggerIO = self.quantities['triggerIO'].options.get(
                triggerIOIndex)
            self.handle.triggerIOconfig(triggerIO)

    def start(self):
        '''4个通道一起启动，DAQmask: 0xf 15'''
        self.handle.DAQflushMultiple(0xf)
        self.handle.DAQstartMultiple(0xf)

    def getData(self, ch=1, fft=False, avg=False, timeout=None, capture=True):
        if capture:
            self.start()
        if timeout is None:
            timeout = self.timeout
        timeout_ms = int(1000 * timeout)
        pointNum = self.config['PointNumber'][ch]['value']
        shots = self.config['Shot'][ch]['value']

        dataRead_raw = self.handle.DAQread(ch, pointNum * shots, timeout_ms)
        if len(dataRead_raw) != pointNum * shots:
            msg = f"CH {ch} Readout {len(dataRead_raw)} (but {pointNum}*{shots}={pointNum * shots} required) from channel {ch} of {self.handle.getProductName()} at Chassis{self.handle.getChassis()}::Slot{self.handle.getSlot()}."
            raise Exception(msg)

        data = np.asarray(dataRead_raw).reshape(shots, pointNum) / 2**15
        if fft:
            coeff = self.config['Coefficient'][ch]['value']
            data = data.dot(coeff.T) / pointNum
        if avg:
            data = data.mean(axis=0)
        return data

    def getIQ(self, ch=1, avg=False, timeout=None, capture=True):
        return self.getData(ch, True, avg, timeout=timeout, capture=capture)

    def getTraces(self, ch=1, avg=True, timeout=None, capture=True):
        return self.getData(ch, False, avg, timeout=timeout, capture=capture)
