import time

import numpy as np

from dev.common import (IEEE_488_2_BinBlock, QInteger, QList, QOption, QReal,
                        QString, QVector, VisaDriver)


class Driver(VisaDriver):

    support_models = ['AWG5014C', 'AWG5208']
    CHs = [1, 2, 3, 4, 5, 6, 7, 8]
    default_waveform_length = 100e-6

    quants = [
        QInteger('Waveform Delay', value=0, ch=1, unit='Sample'),  # 从写入数据上延迟波形
        QInteger('Marker Delay', value=0, ch=1, unit='Sample'),   # 从写入数据上延迟波形
        QReal('Sample Rate',
              unit='S/s',
              set_cmd='SOUR:FREQ %(value)f',
              get_cmd='SOUR:FREQ?'),
        QOption('Run Mode',
                set_cmd='AWGC:RMOD %(option)s',
                get_cmd='AWGC:RMOD?',
                options=[('Continuous', 'CONT'), ('Triggered', 'TRIG'),
                         ('Gated', 'GAT'), ('Sequence', 'SEQ')]),
        QOption('Run State',
                set_cmd='AWGC:%(option)s;*WAI',
                get_cmd='',
                options=[('RUN', 'RUN'), ('STOP', 'STOP')]),
        QOption('Clock Source',
                set_cmd='AWGC:CLOC:SOUR %(option)s',
                get_cmd='AWGC:CLOC:SOUR?',
                options=[('Internal', 'INT'), ('External', 'EXT')]),
        QOption('Reference Source',
                set_cmd='SOUR:ROSC:SOUR %(option)s',
                get_cmd='SOUR:ROSC:SOUR?',
                options=[('Internal', 'INT'), ('External', 'EXT')]),
        QReal('Amplitude',
              unit='V',
              ch=1,
              set_cmd='SOUR%(ch)d:VOLT %(value)f',
              get_cmd='SOUR%(ch)d:VOLT?'),
        QReal('Vpp',
              unit='V',
              ch=1,
              set_cmd='SOUR%(ch)d:VOLT %(value)f',
              get_cmd='SOUR%(ch)d:VOLT?'),
        QReal('Offset',
              unit='V',
              ch=1,
              set_cmd='SOUR%(ch)d:VOLT:OFFS %(value)f',
              get_cmd='SOUR%(ch)d:VOLT:OFFS?'),
        QReal('OffsetDC',
              unit='a.u.',
              ch=1,),
        QReal('Volt Low',
              unit='V',
              ch=1,
              set_cmd='SOUR%(ch)d:VOLT:LOW %(value)f',
              get_cmd='SOUR%(ch)d:VOLT:LOW?'),
        QReal('Volt High',
              unit='V',
              ch=1,
              set_cmd='SOUR%(ch)d:VOLT:HIGH %(value)f',
              get_cmd='SOUR%(ch)d:VOLT:HIGH?'),
        # output delay in time
        QReal('timeDelay',
              unit='s',
              ch=1,
              set_cmd='SOUR%(ch)d:DEL:ADJ %(value)f%(unit)s',
              get_cmd='SOUR%(ch)d:DEL:ADJ?'),
        # output delay in point
        QReal('pointDelay',
              unit='point',
              ch=1,
              set_cmd='SOUR%(ch)d:DEL:POIN %(value)d',
              get_cmd='SOUR%(ch)d:DEL:POIN?'),
        QString('Command', value='*RST'),

        QReal('TriggerA', value=0),
        QReal('TriggerB', value=0),

        QList('Upload Sequence',
              value=[1, 2]),
        QList('WList'),
        QList('SList'),
        QVector('Waveform', ch=1),
        QVector('Marker1', ch=1),
        QVector('Marker2', ch=1),
        QVector('Marker3', ch=1),
        QVector('Marker4', ch=1),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.srate = 2.5e9

    def open(self):
        self.addr = f"TCPIP::{self.addr}"
        super().open()
        self.waveform_list = self.get_waveform_list()
        try:  # 没有sequence模块的仪器会产生一个错误
            self.sequence_list = self.get_sequence_list()
        except:
            self.sequence_list = None

        sr = self.getValue('Sample Rate')
        length_time = self.default_waveform_length
        length_point = round(sr * length_time)
        # self.init_CH_wfname(self.CHs, length_point)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name == 'TriggerA':
            # time.sleep(0.5)
            self.handle.write('TRIG ATR')
        elif name == 'TriggerB':
            self.handle.write('TRIG BTR')
        if name == 'Command':
            # self.handle.write(quant.value)
            super().write(name, value)
            return
        if name in ['Waveform']:
            channel = f'CH{ch}'
            self.update_waveform(value, channel)
        if name in ['OffsetDC']:
            channel = f'CH{ch}'
            sr = self.config['Sample Rate']['global']['value']
            length_time = self.default_waveform_length
            length_point = round(sr * length_time)
            _v = np.array([value] * length_point)
            self.update_waveform(_v, channel)
        elif name in ['Marker1', 'Marker2', 'Marker3', 'Marker4']:
            self.config[name][ch]['value'] = value
            channel = f'CH{ch}'
            mk_kw = {
                'name': channel,
                'mk1': self.config['Marker1'][ch]['value'],
                'mk2': self.config['Marker2'][ch]['value'],
                'mk3': self.config['Marker3'][ch]['value'],
                'mk4': self.config['Marker4'][ch]['value'],
            }
            self.update_marker(**mk_kw)
        elif name in ['Upload Sequence']:
            self.start(value)
        else:
            super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        if name == 'WList':
            # quant.value = self.waveform_list
            return self.waveform_list
        elif name == 'SList':
            # quant.value = self.sequence_list
            return self.sequence_list
        else:
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def init_CH_wfname(self, CHs=[], length=10000):
        # self.stop()
        # self.clear_waveform_list()
        for ch in CHs:
            name = f'CH{ch}'
            if name not in self.waveform_list:
                value = np.zeros(length)
                self.create_waveform(name, length)
                self.update_waveform(value, name)
            self.use_waveform(name, ch=ch)
            self.handle.query('*OPC?', delay=0.1)
        # self.run()

    def get_waveform_list(self):
        if self.model in ['AWG5208']:
            return self.handle.query('WLIS:LIST?').strip("\"\n' ").split(',')
        elif self.model in ['AWG5014C']:
            ret = []
            wlist_size = int(self.handle.query("WLIS:SIZE?"))
            for i in range(wlist_size):
                ret.append(self.handle.query(
                    "WLIS:NAME? %d" % i).strip("\"\n '"))
            return ret
        else:
            return []

    def get_sequence_list(self):
        if self.model in ['AWG5208']:
            ret = []
            slist_size = int(self.handle.query("SLIS:SIZE?"))
            for i in range(slist_size):
                ret.append(
                    self.handle.query("SLIS:NAME? %d" % (i + 1)).strip("\"\n '"))
            return ret
        else:
            return []

    def create_waveform(self, name, length, format=None):
        '''
        format: REAL, INT or IQ
        '''
        if name in self.waveform_list:
            return
        if format is None:
            if self.model in ['AWG5208']:
                format = 'REAL'
            else:
                format = 'INT'
        self.handle.write('WLIS:WAV:NEW "%s",%d,%s;' % (name, length, format))
        self.waveform_list.append(name)

    def remove_waveform(self, name):
        if name not in self.waveform_list:
            return
        self.handle.write(':WLIS:WAV:DEL "%s"; *CLS' % name)
        self.waveform_list.remove(name)

    def clear_waveform_list(self):
        wavs_to_delete = self.waveform_list.copy()
        for name in wavs_to_delete:
            self.remove_waveform(name)

    def use_waveform(self, name, ch=1):
        self.handle.write('SOURCE%d:WAVEFORM "%s"' % (ch, name))

    def run_state(self):
        return int(self.handle.query('AWGC:RST?'))

    def run(self):
        # self.handle.write('AWGC:RUN')
        # self.handle.write('*WAI')
        self.handle.write('AWGC:RUN:IMM')
        time.sleep(1.0)
        while True:
            ret = self.run_state()
            if ret != 0:
                break
        # print(ret, end=' ')
            time.sleep(1.0)

    def stop(self):
        # self.handle.write('AWGC:STOP')
        self.handle.write('AWGC:STOP')
        time.sleep(1.0)
        # self.handle.query('*OPC?')
        # self.handle.write('AWGC:RUN:IMM')
        while True:
            ret = int(self.run_state())
            if ret != 2:
                break
            time.sleep(1.0)

    def output_on(self, ch=1):
        self.handle.write('OUTP%d:STAT 1' % ch)

    def output_off(self, ch=1):
        self.handle.write('OUTP%d:STAT 0' % ch)

    def get_current_waveforms(self):
        current_waveforms = []
        current_waveform_size = 0
        for i in [1, 2, 3, 4]:
            wn = self.handle.query('SOUR%d:WAV?' % i)[1:-2]
            current_waveforms.append(wn)
            if wn != '' and current_waveform_size == 0:
                current_waveform_size = self.query_ascii_values(
                    'WLIS:WAV:LENGTH? "%s"' % wn, 'd')[0]
        return current_waveform_size, current_waveforms

    def update_waveform(self, points, name='ABS', IQ='I', start=0, size=None):
        delay = self.getValue('Waveform Delay', ch=1)
        if delay != 0:
            left_n = len(points) - delay
            shift_data = np.zeros(abs(delay))
            if delay > 0:
                points = np.append(shift_data, points[:left_n])
            else:
                points = np.append(points[-left_n:], shift_data)
        w_type = self.handle.query('WLISt:WAVeform:TYPE? "%s"' % name).strip()
        if w_type == 'REAL':
            self._update_waveform_float(points, name, IQ, start, size)
        elif w_type == 'IQ':
            self._update_waveform_float(points[0], name, 'I', start, size)
            self._update_waveform_float(points[1], name, 'Q', start, size)
        else:
            self._update_waveform_int(points, name, start, size)

    def _update_waveform_int(self, points, name='ABS', start=0, size=None):
        """
        points : a 1D numpy.array which values between -1 and 1.
        """
        message = 'WLIST:WAVEFORM:DATA "%s",%d,' % (name, start)
        if size is not None:
            message = message + ('%d,' % size)
        points = points.clip(-1, 1)
        values = (points * 0x1fff).astype(int) + 0x1fff
        self.write_binary_values(message,
                                 values,
                                 datatype=u'H',
                                 is_big_endian=False,
                                 termination=None,
                                 encoding=None)

    def _update_waveform_float(self,
                               points,
                               name='ABS',
                               IQ='I',
                               start=0,
                               size=None):
        if self.model == 'AWG5208':
            message = 'WLIST:WAVEFORM:DATA:%s "%s",%d,' % (IQ, name, start)
        else:
            message = 'WLIST:WAVEFORM:DATA "%s",%d,' % (name, start)
        if size is not None:
            message = message + ('%d,' % size)
        values = points.clip(-1, 1)
        self.write_binary_values(message,
                                 values,
                                 datatype=u'f',
                                 is_big_endian=False,
                                 termination=None,
                                 encoding=None)

    def update_marker(self,
                      name,
                      mk1=None,
                      mk2=None,
                      mk3=None,
                      mk4=None,
                      start=0,
                      size=None):
        if all([mk is None for mk in (mk1, mk2, mk3, mk4)]):
            return

        def format_marker_data(markers, bits):
            values = 0
            for i, v in enumerate(markers):
                v = 0 if v is None else np.asarray(v, dtype=int)
                values = values + (v << bits[i])
                ##########################################################################
                delay = self.getValue('Marker Delay', ch=1)
                if delay != 0:
                    left_n = len(values) - delay
                    shift_data = np.zeros(abs(delay), dtype=int)
                    if delay > 0:
                        values = np.append(shift_data, values[:left_n])
                    else:
                        values = np.append(values[-left_n:], shift_data)
                #########################################################################
            return values

        if self.model in ['AWG5014C']:
            values = format_marker_data([mk1, mk2], [6, 7])
        elif self.model in ['AWG5208']:
            values = format_marker_data([mk1, mk2, mk3, mk4], [7, 6, 5, 4])
        if size is None:
            message = 'WLIST:WAVEFORM:MARKER:DATA "%s",%d,' % (name, start)
        else:
            message = 'WLIST:WAVEFORM:MARKER:DATA "%s",%d,%d,' % (name, start,
                                                                  size)
        self.write_binary_values(message,
                                 values,
                                 datatype=u'B',
                                 is_big_endian=False,
                                 termination=None,
                                 encoding=None)

    def create_sequence(self, name, steps, tracks):
        if name in self.sequence_list:
            return
        self.handle.write('SLIS:SEQ:NEW "%s", %d, %d' % (name, steps, tracks))
        self.sequence_list.append(name)

    def remove_sequence(self, name):
        if name not in self.sequence_list:
            return
        self.handle.write('SLIS:SEQ:DEL "%s"' % name)
        self.sequence_list.remove(name)

    def clear_sequence_list(self):
        self.handle.write('SLIS:SEQ:DEL ALL')
        self.sequence_list.clear()

    def set_sequence_step(self,
                          name,
                          sub_name,
                          step,
                          wait='OFF',
                          goto='NEXT',
                          repeat=1,
                          jump=None):
        """set a step of sequence
        name: sequence name
        sub_name: subsequence name or list of waveforms for every tracks
        wait: ATRigger | BTRigger | ITRigger | OFF
        goto: <NR1> | LAST | FIRSt | NEXT | END
        repeat: ONCE | INFinite | <NR1>
        jump: a tuple (jump_input, jump_to)
            jump_input: ATRigger | BTRigger | OFF | ITRigger
            jump_to: <NR1> | NEXT | FIRSt | LAST | END
        """
        if isinstance(sub_name, str):
            self.handle.write('SLIS:SEQ:STEP%d:TASS:SEQ "%s","%s"' %
                              (step, name, sub_name))
        else:
            for i, wav in enumerate(sub_name):
                self.handle.write('SLIS:SEQ:STEP%d:TASS%d:WAV "%s","%s"' %
                                  (step, i + 1, name, wav))
        self.handle.write('SLIS:SEQ:STEP%d:WINP "%s", %s' % (step, name, wait))
        self.handle.write('SLIS:SEQ:STEP%d:GOTO "%s", %s' % (step, name, goto))
        self.handle.write('SLIS:SEQ:STEP%d:RCO "%s", %s' %
                          (step, name, repeat))
        if jump is not None:
            self.handle.write('SLIS:SEQ:STEP%d:EJIN "%s", %s' %
                              (step, name, jump[0]))
            self.handle.write('SLIS:SEQ:STEP%d:EJUM "%s", %s' %
                              (step, name, jump[1]))

    def uploadFile(self, fname, buff, chunk=None):
        if chunk is None:
            chunk = len(buff)
        pointer = 0
        while pointer < len(buff):
            if pointer + chunk <= len(buff):
                block = IEEE_488_2_BinBlock(buff[pointer:pointer + chunk])
            else:
                block = IEEE_488_2_BinBlock(buff[pointer:])
            msg = f'MMEM:DATA "{fname}",{pointer},'
            self.handle.write(msg.encode() + block)
            self.handle.query('*OPC?')
            pointer += chunk

    def openWfmFile(self, fname):
        self.handle.write(f'MMEM:OPEN "{fname}"')

    def openSeqFile(self, fname):
        self.handle.write(f'MMEM:OPEN:SASS:SEQ "{fname}"')

    def useSequence(self, name, channels=[1, 2]):
        for i, ch in enumerate(channels):
            self.handle.write('SOUR%d:CASS:SEQ "%s", %d' % (ch, name, i + 1))

    def newSequence(self, name, tracks):
        self.builder = SequenceBuilder(name, tracks)

    def addSequenceStep(self,
                        waveforms,
                        wait='None',
                        goto='Next',
                        repeatCount=1,
                        jumpInput='None',
                        jumpTo='Next'):
        self.builder.addStep(waveforms, wait, goto, repeatCount, jumpInput,
                             jumpTo)

    def start(self, channel=[1, 2]):
        self.remote_path = r'\\%s\\QuLabSeq\\' % self.addr.removeprefix(
            'TCPIP::')
        self.local_path = 'C:\\QuLabSeq\\'
        self.state = np.zeros(len(self.CHs)).astype(int)
        for ch in channel:
            self.state[ch - 1] = 1

        self.uploadSeq()

    def use_sequence(self, name, channels=[1, 2]):
        for i, ch in enumerate(channels):
            self.handle.write('SOUR%d:CASS:SEQ "%s", %d' % (ch, name, i + 1))

    def uploadSeq(self):
        for ch in self.CHs:
            if self.state[ch - 1]:
                self.handle.write(
                    f'MMEM:OPEN:SASS:SEQ "{self.local_path}SEQ_CH{ch}.seqx","SEQ_CH{ch}"')

        step_num = int(sum(self.state))
        time_per_step = 0.1  # 经验值
        tot_time = time_per_step * step_num
        time.sleep(tot_time)

        for ch in self.CHs:
            if self.state[ch - 1]:
                # self.handle.query("*OPC?")
                self.handle.write('*WAI')
                self.use_sequence(f"SEQ_CH{ch}", channels=[ch])

    def openSequence(self, name):
        fname = f"C:\\SequenceFiles\\{name}.seqx"
        self.handle.write(f'MMEM:OPEN:SASS:SEQ "{fname}"')

    def esayNewSequence(self, name, tracks):
        self.builder = EasyBuilder(name, tracks)

    def esaySetSequenceStepWaveform(self, waveform, step, track):
        self.builder.setStepWaveform(waveform, step, track)

    def esaySetSequenceStepMarker(self, marker, index, step, track):
        self.builder.setStepMarker(marker, index, step, track)

    def esaySetSequenceStepArgs(self,
                                step,
                                wait='None',
                                goto='Next',
                                repeatCount=1,
                                jumpInput='None',
                                jumpTo='Next'):
        self.builder.setStepArgs(step, wait, goto, repeatCount, jumpInput,
                                 jumpTo)
