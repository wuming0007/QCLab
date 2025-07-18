import numpy as np

from dev.common import QInteger, QOption, QReal, QVector, VisaDriver


class Driver(VisaDriver):

    support_models = ['E8363B', 'E8363C', 'E5071C', 'E5080A', 'E5080B', 'E5063A', 'ZNB8-4Port',
                      'ZNB20-4Port', 'ZNB20-2Port', 'N5232A', 'N5222B', 'ZVL-13', 'ZNA26-2Port', 'M9802A', '3672B', '3672A', '3674C', '3674E']

    quants = [
        QReal('Power',
              value=-20,
              ch=1,
              unit='dBm',
              set_cmd='SOUR:POW %(value)e%(unit)s',
              get_cmd='SOUR:POW?'),
        # QOption('PowerMode',
        #         value='OFF',
        #         ch=1,
        #         set_cmd='SOUR%(ch)s:POW:MODE %(option)s',
        #         get_cmd='SOUR%(ch)s:POW:MODE?',
        #         options=[('OFF', 'OFF'), ('ON', 'ON')]),
        QReal('Bandwidth',
              value=1000,
              unit='Hz',
              ch=1,
              set_cmd='SENS%(ch)d:BAND %(value)e%(unit)s',
              get_cmd='SENS%(ch)d:BAND?'),
        QReal('FrequencyCenter',
              value=5e9,
              ch=1,
              unit='Hz',
              set_cmd='SENS%(ch)d:FREQ:CENT %(value)e%(unit)s',
              get_cmd='SENS%(ch)d:FREQ:CENT?'),
        QReal('FrequencySpan',
              value=2e9,
              ch=1,
              unit='Hz',
              set_cmd='SENS%(ch)d:FREQ:SPAN %(value)e%(unit)s',
              get_cmd='SENS%(ch)d:FREQ:SPAN?'),
        QReal('FrequencyStart',
              value=4e9,
              ch=1,
              unit='Hz',
              set_cmd='SENS%(ch)d:FREQ:STAR %(value)e%(unit)s',
              get_cmd='SENS%(ch)d:FREQ:STAR?'),
        QReal('FrequencyStop',
              value=6e9,
              ch=1,
              unit='Hz',
              set_cmd='SENS%(ch)d:FREQ:STOP %(value)e%(unit)s',
              get_cmd='SENS%(ch)d:FREQ:STOP?'),
        QVector('Frequency', unit='Hz', ch=1),
        QVector('Trace', ch=1),
        QVector('S', ch=1),
        QOption('Sweep',
                value='ON',
                ch=1,
                set_cmd='INIT:CONT %(option)s',
                options=[('OFF', 'OFF'), ('ON', 'ON')]),
        QInteger('NumberOfPoints',
                 value=201,
                 ch=1,
                 unit='',
                 set_cmd='SENS%(ch)d:SWE:POIN %(value)d',
                 get_cmd='SENS%(ch)d:SWE:POIN?'),
        QOption('Format',
                value='MLOG',
                ch=1,
                set_cmd='CALC:FORM %(option)s',
                get_cmd='CALC:FORM?',
                options=[('Mlinear', 'MLIN'), ('Mlog', 'MLOG'),
                         ('Phase', 'PHAS'), ('Unwrapped phase', 'UPH'),
                         ('Imag', 'IMAG'), ('Real', 'REAL'), ('Polar', 'POL'),
                         ('Smith', 'SMIT'), ('SWR', 'SWR'),
                         ('Group Delay', 'GDEL')]),
        QOption('SweepType',
                value='',
                ch=1,
                set_cmd='SENS%(ch)d:SWE:TYPE %(option)s',
                get_cmd='SENS%(ch)d:SWE:TYPE?',
                options=[('Linear', 'LIN'), ('Log', 'LOG'), ('Power', 'POW'),
                         ('CW', 'CW'), ('Segment', 'SEGM'), ('Phase', 'PHAS')])
    ]

    # 设备网段
    segment = ('na', '103')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)

    def open(self):
        if self.model in ['3672A', '3674C', '3674E']:
            self.addr = f'TCPIP::{self.addr}::5025::SOCKET'
        elif self.model in ['ZNA26-2Port', 'N5222B']:
            self.addr = f'TCPIP::{self.addr}'
        super().open()
        self.set_timeout(30)
        self.pna_select(ch=1)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        if self.model in ['E5063A']:
            kw.update(unit='')
        super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        get_vector_methods = {
            'Frequency': self.get_Frequency,
            'Trace': self.get_Trace,
            'S': self.get_S,
        }
        if name in get_vector_methods.keys():
            return get_vector_methods[name](ch=kw.get('ch', 1))
        else:
            if self.model in ['E5063A', 'ZNA26-2Port']:
                kw.update(unit='')
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def get_Trace(self, ch=1):
        '''Get trace'''
        return self.get_S(ch, formated=True)

    def get_S(self, ch=1, formated=False):
        '''Get the complex value of S paramenter or formated data'''
        # Select the measurement
        # self.pna_select(ch)

        # Stop the sweep
        self.setValue('Sweep', 'OFF')
        # Begin a measurement
        self.handle.write('INIT:IMM')
        self.handle.write('*WAI')
        # Get the data
        self.handle.write('FORMAT:BORD NORM')
        if self.model in ['E5071C', 'E5063A']:
            self.handle.write(':FORM:DATA ASC')
            cmd = ("CALC%d:DATA:FDATA?" %
                   ch) if formated else ("CALC%d:DATA:SDATA?" % ch)
            data = np.asarray(self.query_ascii_values(cmd))
        else:
            # self.handle.write('FORMAT ASCII')
            self.handle.write(':FORM:DATA REAL,32')
            cmd = ("CALC%d:DATA? FDATA" %
                   ch) if formated else ("CALC%d:DATA? SDATA" % ch)
            data = np.asarray(self.query_binary_values(
                cmd, is_big_endian=True))
        self.handle.write('FORMAT ASCII')
        if formated:
            if self.model in ['E5071C']:
                data = data[::2]
        else:
            data = data[::2] + 1j * data[1::2]
        # Start the sweep
        self.setValue('Sweep', 'ON')
        return data

    def SS(self, i=1, j=1, ch=1, mname="MyMeas"):
        self.create_measurement(name=mname, param=f"S{i}{j}", ch=ch)
        self.handle.write('CALC%d:PAR:SEL "%s"' % (ch, mname))
        # Stop the sweep
        self.setValue('Sweep', 'OFF')
        # Begin a measurement
        self.handle.write('INIT:IMM')
        self.handle.write('*WAI')
        # Get the data
        self.handle.write('FORMAT:BORD NORM')
        if self.model in ['E5071C']:
            self.handle.write(':FORM:DATA ASC')
            cmd = ("CALC%d:DATA:SDATA?" % ch)
        else:
            self.handle.write('FORMAT ASCII')
            cmd = ("CALC%d:DATA? SDATA" % ch)
        # Start the sweep
        self.setValue('Sweep', 'ON')

        data = np.asarray(self.query_ascii_values(cmd))
        data = data[::2] + 1j * data[1::2]
        return data

    def get_measurements(self, ch=1):
        if self.model in ['E5071C', 'ZNB20-4Port', 'E5063A', 'ZNB8-4Port']:
            return
        if self.model in ['E8363C', 'E8363B', 'E5080A', 'E5080B', 'N5232A', 'N5222B', 'M9802A', '3672B', '3672A', '3674C', '3674E']:
            quote = '" '
        elif self.model in ['ZNB20-2Port', 'ZVL-13', 'ZNA26-2Port']:
            quote = "' "
        else:
            raise NameError(f'{self.model} is not support!')
        msg = self.handle.query('CALC%d:PAR:CAT?' % ch).strip(quote)
        meas = msg.split(',')
        return meas[::2], meas[1::2]

    def create_measurement(self, name='MyMeas', param='S11', ch=1):
        mname, params = self.get_measurements(ch=ch)
        if name in mname:
            self.handle.write('CALC%d:PAR:DEL "%s"' % (ch, name))
        self.handle.write('CALC%d:PAR:DEF "%s",%s' % (ch, "MyMeas", param))

    def pna_select(self, ch=1):
        '''Select the measurement'''
        if self.model in ['E5071C', 'ZNB20-4Port', 'E5063A', 'ZNB8-4Port']:
            return
        mname, params = self.get_measurements(ch=ch)
        measname = mname[0]
        self.handle.write('CALC%d:PAR:SEL "%s"' % (ch, measname))

    def get_Frequency(self, ch=1):
        """Return the frequency of pna measurement"""

        # Select the measurement
        # self.pna_select(ch)
        if self.model in ['E8363C', 'E5080A', 'E5080B',]:
            cmd = 'CALC%d:X?' % ch
            self.handle.write(':FORM:DATA REAL,32')
            data = self.query_binary_values(cmd, is_big_endian=True)
            # self.handle.write('FORMAT ASCII')
            return np.asarray(data)
        if self.model in ['E8363B', 'N5232A', 'N5222B', 'E5063A', 'M9802A', '3672B', '3672A', '3674C', '3674E']:
            freq_star = self.getValue('FrequencyStart', ch=1)
            freq_stop = self.getValue('FrequencyStop', ch=1)
            num_of_point = self.getValue('NumberOfPoints', ch=1)
            return np.array(np.linspace(freq_star, freq_stop, num_of_point))
        elif self.model in ['ZNB20-4Port', 'ZNB20-2Port', 'ZNA26-2Port', 'ZVL-13', 'ZNB8-4Port']:
            cmd = 'CALC%d:DATA:STIM?' % ch
            return np.asarray(self.query_ascii_values(cmd))

    def set_segments(self, segments=[], form='Start Stop'):
        self.handle.write('SENS:SEGM:DEL:ALL')
        if form == 'Start Stop':
            cmd = ['SENS:SEGM:LIST SSTOP,%d' % len(segments)]
            for kw in segments:
                data = '1,%(num)d,%(start)g,%(stop)g,%(IFBW)g,0,%(power)g' % kw
                cmd.append(data)
        else:
            cmd = ['SENS:SEGM:LIST CSPAN,%d' % len(segments)]
            for kw in segments:
                data = '1,%(num)d,%(center)g,%(span)g,%(IFBW)g,0,%(power)g' % kw
                cmd.append(data)
        self.handle.write('FORMAT ASCII')
        self.handle.write(','.join(cmd))
