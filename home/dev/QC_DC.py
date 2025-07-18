from dev.common import BaseDriver, QReal
from dev.common.QC import DeviceInterface, all_ip

dev = DeviceInterface()


class Driver(BaseDriver):

    support_models = ['QC_DC']

    CHs = [1, 2, 3, 4]

    quants = [
        QReal('Offset', value=0, unit='V', ch=1),
    ]

    def __init__(self, addr, **kw):
        '''
        addr: ip, e.g. '192.168.1.6'
        '''
        super().__init__(addr, **kw)
        self.model = 'QC_DC'

        self.dc_id = self.addr
        self.dc_ip = all_ip['DC'][self.addr]['ip']
        self.dc_port = 5000

    def open(self, **kw):
        return super().open(**kw)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, ch=1, **kw):
        if name == 'Offset':
            # ch: 1,2,3,4 -> 0,1,2,3
            dev.dc_set(self.dc_id, self.dc_ip,
                       self.dc_port, ch, ('VOLT', value))

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)
