import numpy as np

from dev.common import BaseDriver, Quantity
from dev.common.Ceyear.ceyear_1652AM_driver import Ceyear_1652AM_Driver


class Driver(BaseDriver):
    """设备驱动，类名统一为Driver，文件名为设备名称，如VirtualDevice

    Args:
        BaseDriver (class): 所有的驱动均继承自基类，要求实现
        open/close/read/write四个接口
    """
    # 设备通道

    CHs = [1, 2, 3, 4]

    # 设备常见读写属性，不同仪器实在read/write中实现不同的方法即可
    # 属性名中的单词均以大写开头，缩写全为大写
    #

    quants = [
        Quantity('Waveform', value=0, ch=1, unit='Vpp'),
        Quantity('Amplitude', value=0, ch=1, unit='Vpp'),
        Quantity('Offset', value=0, ch=1, unit='Vpp'),
        Quantity('Output', value=0, ch=1, unit='Vpp'),
        Quantity('WaveTypeSel', value=0, ch=1, unit='Vpp'),
        Quantity('TriggerType', value=0, ch=1, unit='Vpp'),
        Quantity('TriggerTime', value=0, ch=1, unit='Vpp'),
        Quantity('Impedence', value=0, ch=1, unit='Vpp'),
        Quantity('CoupleType', value=0, ch=1, unit='Vpp'),
        Quantity('ArbDelay', value=0, ch=1, unit='Vpp'),

        Quantity('ArbStartSet', value=0, ch=1, unit='Vpp'),
        Quantity('ArbEndSet', value=0, ch=1, unit='Vpp'),
        Quantity('light_shining', value=0, ch=1, unit='Vpp')]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        """根据设备地址、超时时间实例化设备驱动，并设置设备采样率、名称
        """
        self.model = 'Ceyear'
        self.srate = 1.2e9
        #

    def open(self, **kw):
        self.handle = Ceyear_1652AM_Driver()
        self.handle.openAWG()

        # 设置触发
        self.setValue('TriggerType', 'SINGLE_OR_USER',
                      board=0)            # 等间隔触发
        self.setValue('TriggerTime', 0.001, board=0,
                      triggerTimes=0)           # [触发间隔,无限循环]

        for slot in range(4):
            for channel in range(1, 5):
                self.setValue('Output', 1, board=slot, ch=channel)

    def close(self, **kw):
        # self.handle.closeAWG()
        pass

    def write(self, name, value, **kw):

        # print(name,value,kw)
        board = kw.get('board', 2)
        channel = kw.get('ch', 1)
        pretreat = kw.get('pretreat', 'ALL')
        downTimes = kw.get('downTimes', 1)

        if name == 'Waveform':
            print('wf', value, channel)
            self.handle.ArbStartSet(board=board, channel=channel)
            self.handle.setAWG("Waveform", value_ex=value,
                               board=board, pretreat=pretreat, downTimes=downTimes)
            self.handle.ArbEndSet(board=board, channel=channel)

        elif name == 'Amplitude':
            self.handle.setAWG("Amplitude", value_ex=value, board=board)

        elif name == 'Offset':
            self.handle.setAWG("Offset", value_ex=value,
                               board=board, channel=channel)

        elif name == 'Output':
            self.handle.setAWG("Output", value_ex=value,
                               board=board, channel=channel)

        elif name == 'WaveTypeSel':
            self.handle.setAWG("WaveTypeSel", value_ex=value,
                               board=board, channel=channel)

        elif name == 'TriggerType':
            self.handle.setAWG("TriggerType", value_ex=value,
                               board=board, channel=channel)

        elif name == 'TriggerTime':
            self.handle.setAWG("TriggerTime", value_ex=value,
                               board=board, triggerTimes=kw['triggerTimes'])

        elif name == 'Impedence':
            self.handle.setAWG("Impedence", value_ex=value, board=board)

        elif name == 'CoupleType':
            self.handle.setAWG("CoupleType", value_ex=value, board=board)

        elif name == 'ArbDelay':
            self.handle.setAWG("ArbDelay", value_ex=value,
                               board=board, channel=channel)

        elif name == 'ArbStartSet':
            self.handle.ArbStartSet(board=board, channel=channel)

        elif name == 'ArbEndSet':
            self.handle.ArbEndSet(board=board, channel=channel)

        elif name == 'light_shining':
            self.handle.light_shining(board=value)
        else:
            pass

        return value

    def read(self, quant, **kw):
        pass

    def get_iq(self):
        return np.ones(1024)

    def get_trace(self):
        return np.ones((1024, 2048))
