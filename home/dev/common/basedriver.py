import re
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from .. import URL
from .quantity import newcfg

PATTERN = r'^192\.168\.({seg})\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{{1,2}})'


class BaseDriver(ABC):
    """设备驱动基类，所有设备驱动均需继承此基类
    """
    # 设备网段,(设备种类缩写，指定ip段)
    segment = ('na', '103|104')

    # 设备通道数量
    CHs = [1]
    # CH_name = {'XY-01':1}

    # 设备读写属性列表
    quants = []

    def __init__(self, addr: str = '192.168.1.42', **kw):
        """初始化设备

        Args:
            addr (str, optional): 设备地址. Defaults to '192.168.1.42'.
        """
        self.addr = addr
        self.port = kw.get('port', 0)  # for remote device
        self.timeout = kw.get('timeout', 3.0)
        self.model = kw.get('model', 'None')
        self.srate = kw.get('srate', -1)

        self.config = newcfg(self.quants, self.CHs)
        self.quantities = {q.name: q for q in self.quants}

    def validate(self, iptable: dict = {}):
        return
        if URL == 'Not Found':
            return
        dev, seg = self.segment
        self.pattern = re.compile(PATTERN.format(seg=seg))
        if self.pattern.match(self.addr):
            if self.addr not in iptable[dev].values():
                raise LookupError(f'Address({self.addr}) not found!')
            # elif IPTABLE[dev].get(addr, ''):
            #     raise LookupError(f'Address({addr}) already used!')
        else:
            raise ValueError(f'Wrong IP address format: {self.addr}!')

    def __repr__(self):
        return self.info()

    def __del__(self):
        try:
            self.close()
        except Exception as e:
            print(f'Failed to close {self}: {e}')

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def info(self):
        return f'Driver(addr={self.addr}, model={self.model})'

    def dict_from_quantity(self):
        conn = {}
        channel = {}
        chx = {}
        for q in deepcopy(self.quants):
            ch = q.default['ch']
            if ch == 'global':
                chx[q.name] = q.default['value']
            else:
                channel[q.name] = q.default['value']
        for ch in self.CHs:
            conn[f'CH{ch}'] = channel
        conn['CHglobal'] = chx
        return conn

    @abstractmethod
    def open(self, **kw):
        """设备打开时的操作，必须由子类实现
        """
        pass

    @abstractmethod
    def close(self, **kw):
        """设备关闭时的操作，必须由子类实现
        """
        pass

    @abstractmethod
    def write(self, name: str, value, **kw):
        """设备写操作，必须由子类实现
        """
        pass

    @abstractmethod
    def read(self, name: str, **kw):
        """设备读操作，必须由子类实现
        """
        pass

    def check(self, name: str, channel: int):
        assert name in self.quantities, f'{self}: quantity({name}) not Found!'
        assert channel in self.CHs or channel == 'global', f"{self}: channel({channel}) not found!"

    def update(self, name: str, value: Any, channel: int = 1):
        self.config[name][channel]['value'] = value

    def setValue(self, name: str, value: Any, **kw):
        """Deprecation Warning: will be removed in the future!
        """
        channel = kw.get('ch')
        if channel is None:
            channel = 1
        else:
            channel = self.CHs[channel]
        self.check(name, channel)
        opc = self.write(name, value, **kw)
        self.update(name, opc, channel)
        if kw.get('sid', 0) in kw.get('track', [0]):
            return opc
        # return opc

    def getValue(self, name: str, **kw):
        """Deprecation Warning: will be removed in the future!
        """
        if name == 'quantity':
            return self.dict_from_quantity()
        elif hasattr(self, name):
            return getattr(self, name)

        channel = kw.get('ch', 1)
        channel = channel
        # channel = self.CH_name[channel]
        self.check(name, channel)
        value = self.read(name, **kw)
        if value is None:
            value = self.config[name][channel]['value']
        else:
            self.update(name, value, channel)
        return value
