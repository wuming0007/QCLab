from dev.common import VisaDriver, QOption, QReal


class Driver(VisaDriver):

    support_models = ['E8257D', 'SMF100A', 'SMB100A', 'SGS100A']

    quants = [
        QReal('Frequency',
              ch=1,
              unit='Hz',
              set_cmd=':FREQ %(value).13e%(unit)s',
              get_cmd=':FREQ?'),
        QReal('Power',
              ch=1,
              unit='dBm',
              set_cmd=':POWER %(value).8e%(unit)s',
              get_cmd=':POWER?'),
        QOption('Output',
                ch=1,
                set_cmd=':OUTP %(option)s',
                get_cmd=':OUTP?',
                options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]

    segment = ('mw', '126|127')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)

    def open(self, **kw):
        self.addr = f'TCPIP::{self.addr}'
        return super().open(**kw)
