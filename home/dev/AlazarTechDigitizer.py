import re
import time
from itertools import count

import numpy as np

from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,
                        QVector, get_coef)
from dev.common.AlazarTechDigitizer import (AlazarTechDigitizer,
                                            AlazarTechError, AutoDMA,
                                            DMABufferArray, configure,
                                            initialize)


def getSamplesPerRecord(pointNum):
    samplesPerRecord = (pointNum // 64) * 64
    if samplesPerRecord < pointNum:
        samplesPerRecord += 64
    return samplesPerRecord


class Driver(BaseDriver):

    CHs = [1]

    quants = [
        QInteger('n', value=1024, ch=1, unit='point',),
        QInteger('PointNumber', value=1024, ch=1, unit='point',),
        QReal('TriggerDelay', value=100E-9, ch=1, unit='S',),
        QReal('Shot', value=512, ch=1),
        QBool('avg', value=False, ch=1),
        QVector('TraceIQ', value=[], ch=1),
        QVector('IQ', value=[], ch=1),
        QList('FrequencyList', value=[], ch=1),
        QList('Coefficient', value=None, ch=1),

        QReal('sampleRate', value=1e9, ch=1, unit='Hz',),

        QInteger('StartCapture', value=1, ch=1,),  # 采集模式：0连续，1触发
        QOption('CaptureMode', value=1, ch=1, options=[
                # 采集模式：0连续，1触发
                ('raw', 'raw'), ('alg', 'alg'), ('raw_alg', 'raw_alg')]),

        QReal('ARange', value=1.0, ch=1),
        QReal('BRange', value=1.0, ch=1),
        QReal('trigLevel', value=0.1, ch=1),
        QReal('triggerTimeout', value=0, ch=1),
        QInteger('samplesPerRecord', value=1024, ch=1),
        QInteger('recordsPerBuffer', value=64, ch=1),
        QInteger('bufferCount', value=512, ch=1),
        QInteger('repeats', value=512, ch=1),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.srate = 1e9

    def open(self):
        if self.addr is not None:
            dict_parse = self._parse_addr(self.addr)
        else:
            dict_parse = {}
        self.model = dict_parse.get('model', None)
        systemID = dict_parse.get('systemID', 1)  # default 1
        boardID = dict_parse.get('boardID', 1)  # default 1
        self.handle = AlazarTechDigitizer(systemID, boardID)
        self.auto_dma = None
        initialize(self.handle)

        self.timeout = 50000000000

        ch = 1
        pointNum = self.config['PointNumber'][ch]['value']
        samplesPerRecord = getSamplesPerRecord(pointNum)
        self.config['samplesPerRecord'][ch]['value'] = samplesPerRecord

        _kw = {
            'ARange': self.config['ARange'][ch]['value'],
            'BRange': self.config['BRange'][ch]['value'],
            'trigLevel': self.config['trigLevel'][ch]['value'],
            'TriggerDelay': int(self.config['TriggerDelay'][ch]['value'] * self.config['sampleRate'][ch]['value']),
            'triggerTimeout': self.config['triggerTimeout'][ch]['value'],
            'bufferCount': self.config['bufferCount'][ch]['value'],
        }
        configure(self.handle, **_kw)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = 1
        self.config[name][ch]['value'] = value  # 更新到config

        if name in ['PointNumber', 'n']:
            self.config['PointNumber'][ch]['value'] = value
            samplesPerRecord = getSamplesPerRecord(value)
            self.config['samplesPerRecord'][ch]['value'] = samplesPerRecord
        elif name in ['Shot']:
            self.setValue('repeats', value)
        elif name in ['ARange', 'BRange', 'trigLevel', 'TriggerDelay',
                      'triggerTimeout', 'bufferCount',]:
            if name == 'TriggerDelay':
                self.config['TriggerDelay'][ch]['value'] = value
                _kw = {'triggerDelay': int(
                    self.config['TriggerDelay'][ch]['value'] * self.config['sampleRate'][ch]['value'])}
            else:
                _kw = {name: value}
            configure(self.handle, **_kw)
        elif name in ['FrequencyList', 'Coefficient']:
            # _kw={
            #     'freq': self.config['FrequencyList'][ch]['value'],
            #     'sRate': self.config['sampleRate'][ch]['value'],
            #     'pointNum': self.config['PointNumber'][ch]['value'],
            # }
            # coef = u_getExp(**_kw)
            if isinstance(value, dict):
                value, f_list, numberOfPoints, phases = get_coef(
                    value, self.srate)
                self.setValue('PointNumber', numberOfPoints)

        elif name in ['repeats', 'recordsPerBuffer']:
            repeats = self.config['repeats'][ch]['value']
            recordsPerBuffer = self.config['recordsPerBuffer'][ch]['value']
            if repeats % recordsPerBuffer != 0:
                repeats = (repeats // recordsPerBuffer + 1) * recordsPerBuffer
                self.config['repeats'][ch]['value'] = repeats
        elif name == 'StartCapture':
            # fft = self.config['CaptureMode'][ch]['value'] == 'alg'
            # self.config['IQ'][ch]['value'] = None
            # self.config['TraceIQ'][ch]['value'] = None
            # data = self.getData(fft=fft, avg=False, timeout=None)
            # if fft:
            #     self.config['IQ'][ch]['value'] = data
            # else:
            #     self.config['TraceIQ'][ch]['value'] = data
            self.start_capture()

        return value

    def read(self, name: str, **kw):
        if name in ['TraceIQ']:
            avg = self.config['avg'][1]['value']
            # return  self.config['TraceIQ'][1]['value']
            return self.getTraces(avg=avg, timeout=None)
        elif name in ['IQ']:
            avg = self.config['avg'][1]['value']
            # return self.config['IQ'][1]['value']
            return self.getIQ(avg=avg, timeout=None)
        else:
            kw.update(ch=1)
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def _parse_addr(self, addr):
        ats_addr = re.compile(
            r'^ATS(9360|9850|9870)::SYSTEM([0-9]+)::([0-9]+)(|::INSTR)$')
        # example: ATS9870::SYSTEM1::1
        m = ats_addr.search(addr)
        if m is None:
            raise NameError('ATS address error!')
        model = 'ATS' + str(m.group(1))  # ATS 9360|9850|9870
        systemID = int(m.group(2))
        boardID = int(m.group(3))
        return dict(model=model, systemID=systemID, boardID=boardID)

    def _aquireData(self, samplesPerRecord, repeats, buffers, recordsPerBuffer,
                    timeout):
        with AutoDMA(self.handle,
                     samplesPerRecord,
                     repeats=repeats,
                     buffers=buffers,
                     recordsPerBuffer=recordsPerBuffer,
                     timeout=timeout) as h:
            yield from h.read()

    def yieldData(self):
        ch = 1
        samplesPerRecord = self.config['samplesPerRecord'][ch]['value']
        recordsPerBuffer = self.config['recordsPerBuffer'][ch]['value']
        repeats = self.config['repeats'][ch]['value']

        try:
            with AutoDMA(self.handle,
                         samplesPerRecord,
                         repeats=repeats,
                         buffers=None,
                         recordsPerBuffer=recordsPerBuffer,
                         timeout=1) as h:
                chA, chB = h.read()
                A_lst = chA.reshape((recordsPerBuffer, samplesPerRecord))
                B_lst = chB.reshape((recordsPerBuffer, samplesPerRecord))
                yield A_lst, B_lst
        except AlazarTechError as err:
            if err.code == 518:
                raise SystemExit(2)
            else:
                pass

    def start_capture(self, timeout=10):
        '''开始采数，将此步独立出来，便于一些特殊操作'''
        ch = 1
        samplesPerRecord = self.config['samplesPerRecord'][ch]['value']
        recordsPerBuffer = self.config['recordsPerBuffer'][ch]['value']
        repeats = self.config['repeats'][ch]['value']
        if timeout is None:
            timeout = self.timeout
        try:
            self.auto_dma.abord()
        except:
            pass
        self.auto_dma = AutoDMA(self.handle,
                                samplesPerRecord,
                                repeats=repeats,
                                buffers=None,
                                recordsPerBuffer=recordsPerBuffer,
                                timeout=timeout)
        self.auto_dma.before()
        self.auto_dma.start()

    def getData(self, fft=False, avg=False, timeout=None):
        ch = 1
        samplesPerRecord = self.config['samplesPerRecord'][ch]['value']
        recordsPerBuffer = self.config['recordsPerBuffer'][ch]['value']
        repeats = self.config['repeats'][ch]['value']
        pointNum = self.config['PointNumber'][ch]['value']
        shots = self.config['Shot'][ch]['value']
        if fft:
            coeff = self.config['Coefficient'][ch]['value']
        if timeout is None:
            timeout = self.timeout

        A, B = [], []

        retry = 0
        while retry < 2:
            try:
                self.start_capture(timeout=0.1)
                for index, (chA, chB) in zip(count(), self.auto_dma.read()):
                    A_lst = chA.reshape((recordsPerBuffer, samplesPerRecord))
                    B_lst = chB.reshape((recordsPerBuffer, samplesPerRecord))
                    if fft:
                        A_lst = (A_lst[:, :pointNum]).dot(coeff.T) / pointNum
                        B_lst = (B_lst[:, :pointNum]).dot(coeff.T) / pointNum
                    A.append(A_lst)
                    B.append(B_lst)
                    if repeats == 0 and (index + 1) * recordsPerBuffer >= shots:
                        break
                try:
                    self.auto_dma.abord()
                finally:
                    self.auto_dma = None

                A = np.asarray(A)
                B = np.asarray(B)

                A = A.flatten().reshape(A.shape[0] * A.shape[1], A.shape[2])
                B = B.flatten().reshape(B.shape[0] * B.shape[1], B.shape[2])

                if avg:
                    return A.mean(axis=0), B.mean(axis=0)
                else:
                    return A, B
            except AlazarTechError as err:
                if err.code == 518:
                    raise SystemExit(2)
                else:
                    pass
            time.sleep(0.1)
            retry += 1
            print(retry)
        else:
            print('ATS Timeout')
            raise SystemExit(1)

    def getIQ(self, avg=False, timeout=None):
        return self.getData(True, avg, timeout=timeout)

    def getTraces(self, avg=True, timeout=None):
        return self.getData(False, avg, timeout=timeout)
