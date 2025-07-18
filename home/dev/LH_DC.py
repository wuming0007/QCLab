
from dev.common import BaseDriver, QOption, QReal, QVector
from dev.common.UNIVI_LH import xdma


class Driver(BaseDriver):
    support_models = ['DC']

    CHs = [1, 3, 5, 7, 9, 11, 13, 15, 16, 18, 20, 22, 24, 26, 28, 30]

    quants = [
        QReal('Offset', unit='V', ch=1,),
        QReal('Amplitude', unit='VPP', ch=1,),
        QOption('Output', ch=1),
        QVector('Waveform', value=[], ch=1),
    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'LHDC'
        self.datalist = [[], [], [], [], [], []]

    def open(self):
        xdma.StructPointer()
        xdma.dma_data()
        xdma.dma_data_sum()
        xdma.fpgadevdll()
        self.handle = xdma.fpgadev()
        # self.handle.settrigT(200)
        self.handle.reset_channel(1, 1, self.addr)  # reset DC
        self.handle.initial_channel(1, 1, self.addr)  # 初始化DC
        self.set_ldac_value(0, 0, 1)

    def close(self, **kw):
        return super().close(**kw)

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 1)
        if name in ['Offset']:
            self.set_ldac_value(value, ch=ch)
        elif name in ['Amplitude']:
            pass
        elif name in ['Output']:
            pass
        elif name in ['Waveform']:
            self.writeWaveform(value, ch=ch, continuous=False)
        else:
            super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def set_ldac_value(self, value, ch=1, aa=0):
        self.handle.set_ldac_value(ch, value, aa, self.addr)
        self.handle.LDAC_load(ch, aa, self.addr)

    def set_clear_value(self, ch=1, value=0, aa=0):
        self.handle.set_clr_value(ch, value, aa, self.addr)
        self.handle.CLR_load(ch, aa, self.addr)

    def on(self, slot):  # 关闭所有通道
        self.handle.open_dac_board(slot)

    def off(self, slot):  # 打开所有通道
        self.handle.close_dac_board(slot)

    def offset(self, ch, value):
        self.handle.dac_set_offset(ch, value, self.addr)

    # 目前的连续波模式下data必须是寄存器的整数倍的情况下波形收尾连续
    def writeWaveform(self, data, ch=1, continuous=False, sequence=True, settingall=False):
        # import pickle
        # import time

        # with open(f"{time.strftime('%Y%m%d%H%M%S')}.pickle", 'wb') as f:
        #     pickle.dump((data, slot, ch, continuous), f)
        if ch in [1, 2, 3, 4, 5, 6]:
            self.datalist[ch - 1] = data * (2**15 - 1)
        else:
            print('wrong data type or wrong ch number, must be in [1-6].')
        if sequence:
            if self.addr == 'slot7' or self.addr == 'slot8':  # 20200723 78 2ad2da
                numm = 2
            else:
                numm = 6
            data_temp = [{}] * numm  # 6Da
            data_temp[ch - 1] = {0: self.datalist[ch - 1],
                                 1: self.datalist[ch - 1]}
            temp_setting = {'wave_id': 0, 'amp': 1,
                            'repeat_num': 0, 'continuous': 0}
            setting_temp = [{}] * numm  # 6Da
            setting_temp[ch - 1] = {0: temp_setting, 1: temp_setting}
            if settingall:
                setting_save00 = self.handle.wr_dac_data(
                    [data_temp[ch - 1]] * numm, self.addr)
                setting_save10 = self.handle.wr_dac_setting(
                    [setting_temp[ch - 1]] * numm, setting_save00, self.addr)
            else:
                setting_save00 = self.handle.wr_dac_data(data_temp, self.addr)
                setting_save10 = self.handle.wr_dac_setting(
                    setting_temp, setting_save00, self.addr)
        else:
            self.handle.wr_dac_data(self.datalist, continuous, self.addr)
        print(self.datalist)
