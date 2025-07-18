from pathlib import Path

from dev.common import BaseDriver
from dev.common.PG import Trigboard as TB


class Driver(BaseDriver):

    CHs = [1, 2, 3, 4, 5, 6, 7, 8]

    quants = [
        # QReal('Offset',value=0,unit='V',ch=1,),
        # QReal('Amplitude',value=1,unit='V',ch=1,),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'PGTrig'

    def open(self):
        addr = self.addr if self.addr else '192.168.1.236'
        self.handle = TB.TrigBoard()
        self.handle.connect(addr)
        self.handle.trig_switch_ext()
        filepath = Path(__file__).parent  # os.path.abspath(__file__)
        # OUT_250M_path=os.path.dirname(filepath)+'\\'+'LMX2582(REF 10M_OUT 250M).txt'
        OUT_250M_path = filepath / 'common/PG/C10M_250M.txt'
        self.handle.config_clock(str(OUT_250M_path))
        super().open()

    def close(self):
        self.handle.disconnect()
        super().close()

    def write(self, name: str, value, **kw):
        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
