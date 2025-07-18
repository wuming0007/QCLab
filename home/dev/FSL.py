import time

import numpy as np

from dev.common import QInteger, QOption, QReal, QVector, VisaDriver


class Driver(VisaDriver):

    error_command = 'SYST:ERR?'
    support_models = ['FSL18']
    # R&S FSL18

    quants = [
        QOption('Sweep',
                value='ON',
                set_cmd='INIT:CONT %(option)s',
                options=[('OFF', 'OFF'), ('ON', 'ON')]),
        QOption('Trace Mode',
                value='WRIT',
                ch=1,
                set_cmd='DISP:TRAC%(ch)d:MODE %(option)s',
                get_cmd='DISP:TRAC%(ch)d:MODE?',
                options=[('Write', 'WRIT'), ('Maxhold', 'MAXH'),
                         ('Minhold', 'MINH'), ('View', 'VIEW'),
                         ('Average', 'AVER')]),
        QReal('Frequency Start',
              unit='Hz',
              set_cmd='SENS:FREQ:STAR %(value)e%(unit)s',
              get_cmd='SENS:FREQ:STAR?'),
        QReal('Frequency Stop',
              unit='Hz',
              set_cmd='SENS:FREQ:STOP %(value)e%(unit)s',
              get_cmd='SENS:FREQ:STOP?'),
        QInteger('Sweep Points',
                 value=601,
                 set_cmd='SENS:SWE:POIN %(value)d',
                 get_cmd='SENS:SWE:POIN?'),


        QVector('Frequency', unit='Hz', ch=1),
        QVector('Trace', ch=1),
        QReal('SNR', ch=1, unit='dB'),
        QReal('AMP', ch=1, unit='dB'),


        QReal('signalfreq', ch=1),
        QReal('signalbandwidth', ch=1, value=10e6, unit='Hz'),
        QInteger('average', ch=1, value=1),
    ]

    def write(self, name: str, value, **kw):
        return value

    def read(self, name, **kw):
        get_vector_methods = {
            'Frequency': self.get_Frequency,
            'Trace': self.get_Trace,
        }
        ch = kw.get('ch', 1)
        if name in get_vector_methods.keys():
            return get_vector_methods[name](ch=ch)
        elif name in ['SNR']:
            get_snr_kw = {
                'signalfreq': self.getValue('signalfreq', ch=ch),
                'signalbandwidth': self.getValue('signalbandwidth', ch=ch),
                'average': self.getValue('average', ch=ch),
                'ch': ch,
            }
            snr = self.get_SNR(**get_snr_kw)
            return snr
        elif name in ['AMP']:
            get_amp_kw = {
                'signalfreq': self.getValue('signalfreq', ch=ch),
                'average': self.getValue('average', ch=ch),
                'ch': ch,
            }
            amp = self.get_AMP(**get_amp_kw)
            return amp
        else:
            return super().read(name, **kw)

    def get_Trace(self, ch=1, average=1, **kw):
        '''Get the Trace Data '''

        points = self.getValue('Sweep Points')
        # Stop the sweep
        self.setValue('Sweep', 'OFF')
        if average == 1:
            self.setValue('Trace Mode', 'Write', ch=ch)
            self.handle.write(':SWE:COUN 1')
        else:
            self.setValue('Trace Mode', 'Average', ch=ch)
            self.handle.write(':TRAC:AVER:COUN %d' % average)
            self.handle.write(':SWE:COUN %d' % average)
            self.handle.write(':TRAC:AVER:RES')
        # Begin a measurement
        self.handle.write('INIT:IMM')
        self.handle.write('*WAI')
        count = float(self.handle.query('SWE:COUN:CURR?'))
        while count < average:
            count = float(self.handle.query('SWE:COUN:CURR?'))
            time.sleep(0.01)
        # Get the data
        self.handle.write('FORMAT:BORD NORM')
        self.handle.write('FORMAT ASCII')
        data = self.handle.query_ascii_values("TRAC:DATA? TRACE%d" % ch)
        # data_raw = self.handle.query("TRAC:DATA? TRACE%d" % ch).strip('\n')
        # _data = re.split(r",",data_raw[11:])
        # data=[]
        # for d in _data[:points]:
        #     data.append(float(d))
        # Start the sweep
        self.setValue('Sweep', 'ON')
        return np.array(data)

    def get_Frequency(self, ch=1, **kw):
        """Return the frequency of DSA measurement"""

        freq_star = self.getValue('Frequency Start')
        freq_stop = self.getValue('Frequency Stop')
        sweep_point = self.getValue('Sweep Points')
        return np.array(np.linspace(freq_star, freq_stop, sweep_point))

    def get_SNR(self, signalfreq=7e9, signalbandwidth=10e6, average=1, ch=1, **kw):
        '''get SNR_dB '''

        Y_unit = self.handle.query(':UNIT:POW?;:UNIT:POW W').strip('\n')
        Frequency = self.get_Frequency()
        Spectrum = self.get_Trace(average=average, ch=ch)

        Total_power = sum(Spectrum)
        idxs, = np.where(np.abs(Frequency - signalfreq) < signalbandwidth / 2)
        Signal_power = sum(Spectrum[idxs])

        self.handle.write(':UNIT:POW %s' % Y_unit)
        _SNR = Signal_power / (Total_power - Signal_power)
        SNR = 10 * np.log10(_SNR)
        return SNR

    def get_AMP(self, signalfreq=7e9, average=1, ch=1, **kw):
        Frequency = self.get_Frequency()
        Spectrum = self.get_Trace(average=average, ch=ch)

        idx = np.argmin(np.abs(Frequency - signalfreq))
        return Spectrum[idx]
