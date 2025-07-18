from dev.common import VisaDriver, QReal, QOption


class Driver(VisaDriver):

    support_models = ['DG1062Z']
    CHs = [1, 2]

    quants = [

        # Set the waveform of the specified channel to DC with the specified offset.
        QReal('Offset',
              value=0,
              unit='VDC',
              ch=1,
              set_cmd=':SOUR%(ch)d:APPL:DC 1,1, %(value).8e%(unit)s',
              get_cmd=''),

        QOption('Output',
                value="ON",
                unit='',
                ch=1,
                set_cmd='OUTP%(ch)d %(value)s',
                options=[('OFF', 'OFF'), ('ON', 'ON')],
                get_cmd='OUTP?%(ch)d')

    ]

    segment = ('ot', '199')

    def open(self, **kw):
        self.addr = f'TCPIP0::{self.addr}'
        return super().open(**kw)
        self.handle.query_delay = 0.2
