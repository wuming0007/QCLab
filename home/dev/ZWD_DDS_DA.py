import time

from dev.common import BaseDriver, Quantity
from dev.common.ZWD_DDS import driver


class Driver(BaseDriver):

    support_models = ['ZWD_DDS_DA']

    CHs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    quants = [
        Quantity('Waveform', value=[], ch=1),
    ]

    def __init__(self, addr=None, **kw):
        super().__init__(addr=addr, **kw)
        self.model = 'ZWD_DDS_DA'
        self.srate = 5e9
        self.handle = driver.base_driver('192.168.1.100', 9003)
        # self.handle.set_ref('ext_ref')
        self.handle.close(self.CHs)

    def open(self):
        self.status = self.handle.open(self.CHs)
        while self.status == 0:
            pass

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name in ['Waveform']:
            self.handle.write_wave_form(value, ch=ch)

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def on(self, ch):  # 打开通道
        self.handle.open([ch])

    def off(self):  # 关闭通道
        self.handle.close(self.CHs)

    def reference_mode(self, mode='ext_ref'):
        self.handle.set_ref('ext_ref')  # 'ext_ref' 外参考：'in_ref' 内外参
        time.sleep(120)

    def change_ip(self, ip=' '):  # 关闭通道
        self.handle.set_ip(ip)

    def pulse_mode(self, mode):  # 0表示调制脉冲1表示调制脉冲
        self.handle.set_mode(mode)
