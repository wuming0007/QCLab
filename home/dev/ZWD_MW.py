import struct
from socket import socket, AF_INET, SOCK_STREAM
import serial
import numpy as np
from dev.common import BaseDriver, Quantity

# class Quantity(object):
#     def __init__(self, name: str, value=None, ch: int = None, unit: str = ''):
#         self.name = name
#         self.default = dict(value=value, ch=ch, unit=unit)


class Driver(BaseDriver):
    """设备驱动，类名统一为Driver，文件名为设备名称，如VirtualDevice

    Args:
        BaseDriver (class): 所有的驱动均继承自基类，要求实现
        open/close/read/write四个接口
    """
    # 设备可用通道数量
    CHs = [1, 2, 3, 4, 5, 6, 7, 8]

    # 设备常见读写属性，可自行增加，对应在read/write中实现不同的方法即可
    # 属性名中的单词均以大写开头，缩写全为大写，用于说明有哪些可读写设置
    # 应给每个属性加上注释，方便了解设置的作用
    quants = [
        # 微波源(MW)
        Quantity('Frequency', value=0, ch=1, unit='Hz'),  # 频率，float
        Quantity('Power', value=0, ch=1, unit='dBm'),  # 功率，float
    ]

    def __init__(self, addr: str = '', timeout: float = 3.0, **kw):
        super().__init__(addr=addr, timeout=timeout, **kw)
        """根据设备地址、超时时间实例化设备驱动
        """
        self.model = 'VirtualDevice'  # 默认为设备名字
        self.srate = 1e9  # 设备采样率

    def open(self, **kw):
        """打开并初始化仪器设置，获取仪器操作句柄，必须实现，可以为空(pass)但不能没有
        """
        self.handle = KU_PLY()

    def close(self, **kw):
        """关闭仪器，必须实现，可以为空(pass)但不能没有
        """
        self.handle.close()

    def write(self, name: str, value, **kw):
        """设置仪器，额外的参数(如通道指定)可通过kw传入。必须实现，如

        if name == '属性名':
            执行操作
        elif name == '属性名':
            执行操作
        """
        ch = kw.get('ch', 1)
        if name == 'Frequency':
            self.handle.bp_set_fs(fs=value, ch=ch)
            # 如，self.set_offset(value, ch=1)
        elif name == 'Power':
            self.handle.bp_set_gl(gl=value, ch=ch)
            # 如，self.set_shot(value, ch=2)

        return value

    def read(self, name: str, **kw):
        """读取仪器，额外的参数(如通道指定)可通过kw传入。必须实现，如

        if name == '属性名':
            return 执行操作
        elif name == '属性名':
            return 执行操作
        """
        if name == 'TraceIQ':
            return self.get_trace()
        elif name == 'IQ':
            return self.get_iq()

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
    def get_iq(self):
        shot = self.getValue('Shot')
        fnum = self.getValue('Coefficient')[0].shape[0]
        return np.ones((shot, fnum)), np.ones((shot, fnum))

    def get_trace(self):
        shot = self.getValue('Shot')
        point = self.getValue('PointNumber')
        test = 1 / 0
        return np.ones((shot, point))


class wby_set_cmd:
    list = [0xAA, 0x55, 0x01, 0x0a]
    hz = []
    gl = np.uint16(0)
    crc = np.uint8(0)

    def __init__(self):
        pass

    def create_pack(self):
        array = []
        array += self.list
        array += self.hz
        array += [self.gl >> 0, self.gl >> 8]
        for i in range(len(array)):
            self.crc ^= array[i]
        self.crc &= 0xFF
        array.append(self.crc)
        format_str = '!4s8sHB'
        send_str = struct.pack(format_str, np.asarray(self.list, np.uint8).tobytes(),
                               np.asarray(self.hz, np.uint8).tobytes(), self.gl, self.crc)
        return send_str


class wby_status_cmd:
    head = [0xAA, 0x55, 0x04, 0x04, 0x00]
    status = 0
    yuliu = 0
    ch = 1
    crc = 0

    def __init__(self):
        pass

    def create_pace(self):
        array = []
        array += self.head
        array += [self.status, self.yuliu, self.ch]
        for i in range(len(array)):
            self.crc ^= array[i]
        self.crc &= 0xFF
        format_str = "!5sBBBB"
        return struct.pack(format_str, np.asarray(self.head, dtype=np.uint8).tobytes(), self.status, self.yuliu,
                           self.ch, self.crc)


class bp_set_cmd:
    head = [0x55, 0x01, 0x11]
    ch = 1
    fsm = 0x00000000
    sjm = 0x0000
    yuliu = 0x00000000
    crc = 0x00
    end = 0xAA

    def __init__(self):
        pass

    def create_pace(self):
        array = []
        array += self.head
        array.append(self.ch)
        array += [self.fsm >> 0 & 0xFF, self.fsm >> 8 & 0xFF,
                  self.fsm >> 16 & 0xFF, self.fsm >> 24 & 0xFF]
        array += [self.sjm >> 0 & 0xFF, self.sjm >> 8 & 0xFF]
        array += np.zeros(4, dtype=np.uint8).tolist()
        for i in range(1, len(array) - 1, 1):
            self.crc ^= array[i]
        self.crc &= 0xFF
        format_str = '!3sBIHIBB'
        return struct.pack(format_str, np.asarray(self.head, dtype=np.uint8).tobytes(), self.ch, self.fsm, self.sjm,
                           self.yuliu, self.crc, self.end)


class KU_PLY(object):
    # 需要确定串口号并且更改此处的串口号‘COM5’, 'COM6'
    # dev_info_list = [
    #     ('192.168.1.8', 8899),
    #     ('192.168.1.7', 8899),
    #     ('COM7', 115200),
    #     ('COM10', 115200),
    # ]
    # 测试IP
    dev_info_list = [
        ('127.0.0.1', 9002),
        ('127.0.0.1', 9002),
        ('COM7', 115200),
        ('COM10', 115200),
    ]

    wby_ch = [1, 2, 3, 4]
    by_ch = [1, 2, 3, 4]
    dev_status_dic = {
        'wby_ch1': {'gl': 0, 'fs': 12000},
        'wby_ch2': {'gl': 0, 'fs': 12000},
        'wby_ch3': {'gl': 0, 'fs': 12000},
        'wby_ch4': {'gl': 0, 'fs': 12000},
        'bp_ch1': {'gl': 0, 'fs': 4000, 'zp': 600},
        'bp_ch2': {'gl': 0, 'fs': 4000, 'zp': 600},
        'bp_ch3': {'gl': 0, 'fs': 4000, 'zp': 600},
        'bp_ch4': {'gl': 0, 'fs': 4000, 'zp': 600},
    }

    def __init__(self):
        self.wby1 = socket(AF_INET, SOCK_STREAM)
        self.wby2 = socket(AF_INET, SOCK_STREAM)
        self.wby1.connect(self.dev_info_list[0])
        self.wby2.connect(self.dev_info_list[1])
        self.bp1 = serial.Serial(self.dev_info_list[2][0], self.dev_info_list[2][1], stopbits=1, bytesize=8, parity='N',
                                 timeout=10)
        self.bp2 = serial.Serial(self.dev_info_list[3][0], self.dev_info_list[3][1], stopbits=1, bytesize=8, parity='N',
                                 timeout=10)

    def wby_set(self, ch=1, gl=10, fs=12000):
        """
        12-16GHz微波源设置4个通道的功率值和频率
        :param ch:1-4
        :param gl:db[-40->15]
        :param fs:MHz
        :return:
        """
        self.dev_status_dic['wby' + str(ch)]['gl'] = gl
        self.dev_status_dic['wby' + str(ch)]['fs'] = fs

        switch_ch1 = [0xAA, 0x55, 0x81, 0x01, 0x81, 0xFE]
        switch_ch2 = [0xAA, 0x55, 0x82, 0x01, 0x82, 0xFE]
        data = wby_set_cmd()
        data.gl = gl * 10 + 1500
        f = fs * 1000 * 1000 * 10000
        data.hz = [f >> 56 & 0xFF, f >> 48 & 0xFF, f >> 40 & 0xFF, f >> 32 & 0xFF, f >> 24 & 0xFF,
                   f >> 16 & 0xFF, f >> 8 & 0xFF, f >> 0 & 0xFF]
        send_data = data.create_pack()
        if ch <= 2:
            self.wby1.send(np.asarray(switch_ch1, dtype=np.uint8).tobytes()) if ch <= 1 else self.wby1.send(
                np.asarray(switch_ch2, dtype=np.uint8).tobytes())
            self.wby1.send(send_data)
        else:
            self.wby2.send(np.asarray(switch_ch1, dtype=np.uint8).tobytes()) if ch <= 3 else self.wby2.send(
                np.asarray(switch_ch2, dtype=np.uint8).tobytes())
            self.wby2.send(send_data)

    def wby_set_gl(self, ch=1, gl=10):
        """
        单独设置12-16GHz微波源功率
        :param ch: 通道1-4
        :param gl: 功率【-40->15】db
        :return:
        """
        self.wby_set(ch, gl, self.dev_status_dic['wby' + str(ch)]['fs'])

    def wby_set_fs(self, ch=1, fs=12000):
        """
        单独设置12-16GHz微波源频率
        :param ch:通道1-4
        :param fs:频率,单位MHz
        :return:
        """
        self.wby_set(ch, gl, self.dev_status_dic['wby' + str(ch)]['gl'])

    def wby_open(self, ch=1):
        """
        打开12-16GHz微波源4个通道
        :param ch:1-4
        :return:
        """
        cmd = wby_status_cmd()
        cmd.status = 1
        if ch <= 2:
            cmd.ch = ch
        else:
            cmd.ch = ch - 2
        send_data = cmd.create_pace()
        self.wby1.send(send_data) if ch <= 2 else self.wby2.send(send_data)

    def wby_close(self, ch=1):
        """
        关闭12-16GHz微波源4个通道
        :param ch:1-4
        :return:
        """
        cmd = wby_status_cmd()
        cmd.status = 0
        if ch <= 2:
            cmd.ch = ch
        else:
            cmd.ch = ch - 2
        send_data = cmd.create_pace()
        self.wby1.send(send_data) if ch <= 2 else self.wby2.send(send_data)

    def bp_set(self, ch=1, zp=600, fs=4000, gl=-10):
        """
        4-8GH变频通道设置
        :param ch: 1-4
        :param zp:MHz
        :param fs: MHz
        :param gl: db[-40->-10]
        :return:
        """
        self.dev_status_dic['bp' + str(ch)]['gl'] = gl
        self.dev_status_dic['bp' + str(ch)]['fs'] = fs
        self.dev_status_dic['bp' + str(ch)]['zp'] = zp

        cmd = bp_set_cmd()
        if ch <= 2:
            cmd.ch = ch
        else:
            cmd.ch = ch - 2
        fs_m = (fs * 1000) - (zp * 1000) + 600000
        sj_m = ((gl + 10) * (-1)) * 10
        cmd.fsm = ((fs_m >> 24) & 0xff) << 0 | \
                  ((fs_m >> 16) & 0xff) << 8 | \
                  ((fs_m >> 8) & 0xff) << 16 | \
                  ((fs_m >> 0) & 0xff) << 24
        cmd.sjm = ((sj_m >> 8) & 0xFF) | ((sj_m & 0xFF) << 8)
        send_data = cmd.create_pace()
        self.bp1.write(send_data) if ch <= 2 else self.bp2.write(send_data)

    def bp_set_gl(self, ch=1, gl=-10):
        """
        单独设置4-8GHz变频通道功率
        :param ch: 通道1-4
        :param gl: db[-40->-10]
        :return:
        """
        self.bp_set(ch, self.dev_status_dic['bp' + str(ch)]['zp'],
                    self.dev_status_dic['bp' + str(ch)]['fs'], gl)

    def bp_set_fs(self, ch=1, zp=600, fs=4000):
        """
        单独设置4-8GHz变频通道频率
        :param ch: 通道1-4
        :param zp: 中频MHz
        :param fs: 频率MHz
        :return:
        """
        self.bp_set(ch, zp, fs, self.dev_status_dic['bp' + str(ch)]['gl'])
