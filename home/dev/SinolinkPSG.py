import socket
from contextlib import contextmanager

from dev.common import QOption, QReal, VisaDriver


class SinolinkPSG():

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def write(self, cmd):
        if isinstance(cmd, str):
            cmd = cmd.encode()
        with self._socket() as s:
            s.send(cmd)

    def read(self, quant, **kw):
        return super().read(quant, **kw)

    def query(self, cmd):
        if isinstance(cmd, str):
            if cmd == "*IDN?\n":
                return "Sinolink, SLFS0218F, V1.0, 20210324"
            cmd = cmd.encode()
        with self._socket() as s:
            s.send(cmd)
            ret = s.recv(1024).decode()
            return ret

    @contextmanager
    def _socket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            yield s


class Driver(VisaDriver):

    support_models = ['SLFS0218F']

    quants = [
        QReal('Frequency',
              ch=1,
              unit='Hz',
              set_cmd='FREQ %(value).9e Hz',
              get_cmd='FREQ?'),
        QReal('Power',
              ch=1,
              unit='dBm',
              set_cmd='LEVEL %(value).5e dBm',
              get_cmd='LEVEL?'),
        QOption('Output',
                ch=1,
                set_cmd='LEVEL:STATE %(option)s',
                options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]

    CHs = [1]

    segment = ('mw', '126|127')

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.port = kw.get('port', 2000)

    def open(self, **kw):
        try:
            self.handle = SinolinkPSG(self.addr, self.port)
            IDN = self.handle.query("*IDN?\n").split(',')
            # company = IDN[0].strip()
            model = IDN[1].strip()
            # version = IDN[3].strip()
            self.model = model
        except:
            raise IOError('query IDN error!')

    def close(self, **kw):
        return super().close(**kw)
