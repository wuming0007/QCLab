import pickle
import socket
import struct
import xmlrpc.client
from xmlrpc.client import Transport
from functools import wraps

import numpy as np
import waveforms

from dev.common import BaseDriver, Quantity, get_coef


def solve_rpc_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpc.client.Fault as e:
            print(f'************{args[0].__class__}************')
            print(f'远程函数报错: {e.faultString}')
            print(args[0].handle.get_all_status())
            print(f'远程函数报错: {e.faultString}')
            print('*****************************')

    return wrapper


class Driver(BaseDriver):
    CHs = list(range(1, 17))

    quants = [
        # 采集运行参数
        Quantity('Shot', value=1024, ch=1),  # set/get,运行次数
        Quantity('PointNumber', value=16384, unit='point'),  # set/get,AD采样点数
        Quantity('TriggerDelay', value=0, ch=1, unit='s'),  # set/get,AD采样延时
        # set/get,解调频率列表，list，单位Hz
        Quantity('FrequencyList', value=[], ch=1, unit='Hz'),
        # set/get,解调频率列表，list，单位Hz
        Quantity('PhaseList', value=[], ch=1, unit='Hz'),
        Quantity('Coefficient', value=None, ch=1),
        Quantity('DemodulationParam', value=None, ch=1),
        Quantity('CaptureMode'),
        Quantity('StartCapture'),  # set,开启采集（执行前复位）
        Quantity('TraceIQ', ch=1),  # get,获取原始时域数据
        # 返回：array(shot, point)
        Quantity('IQ', ch=1),  # get,获取解调后数据,默认复数返回
        # 系统参数，宏定义修改，open时下发
        # 复数返回：array(shot,frequency)
        # 实数返回：array(IQ,shot,frequency)

        # 任意波形发生器
        Quantity('Waveform', value=np.array([]), ch=1),  # set/get,下发原始波形数据
        Quantity('Delay', value=0, ch=1),  # set/get,播放延时
        # set/get, np.linspace函数，用于生成timeline
        Quantity('LinSpace', value=[0, 30e-6, 1000], ch=1),
        Quantity('Output', value=True, ch=1),  # set/get,播放通道开关设置
        # set/get, 设备接收waveform对象，根据waveform对象直接生成波形
        Quantity('GenWave', value=waveforms.Waveform(), ch=1),
        # set/get, 设备接收IQ分离的waveform对象列表，根据waveform对象列表直接生成波形
        Quantity('GenWaveIQ', value=[
                 waveforms.Waveform(), waveforms.Waveform()], ch=1),

        # 内触发
        # set/get,触发周期单位ns，触发数量=shot
        Quantity('GenerateTrig', value=1e7, unit='ns'),
    ]

    SystemParameter = {
        'MixMode': 2,  # Mix模式，1：第一奈奎斯特去； 2：第二奈奎斯特区
        'RefClock': 'out',  # 参考时钟选择： ‘out’：外参考时钟；‘in’：内参考时钟
        'ADrate': 4e9,  # AD采样率，单位Hz
        'DArate': 6e9,  # DA采样率，单位Hz
        'KeepAmp': 0,  # DA波形发射完毕后，保持最后一个值
        'DAC抽取倍数': 1,  # DA内插比例，1,2,4,8
        'DAC本振频率': 0,  # DUC本振频率，单位MHz
        'ADC抽取倍数': 1,  # AD抽取比例，1,2,4,8
        'ADC本振频率': 0  # DDC本振频率，单位MHz
    }

    def __init__(self, addr: str = '', **kw):  # , timeout: float = 10.0
        super().__init__(addr, **kw)
        self.fast_rpc = None
        self.handle = None
        self.model = 'NS_MCI'  # 默认为设备名字
        self.timeout = 10.0
        self.srate = 6e9

    @solve_rpc_exception
    def open(self, **kw):
        """
        输入IP打开设备，配置默认超时时间为5秒
        打开设备时配置RFSoC采样时钟，采样时钟以参数定义
        """
        tran = Transport(use_builtin_types=True)
        tran.accept_gzip_encoding = False
        self.handle = xmlrpc.client.ServerProxy(f'http://{self.addr}:10801', transport=tran, allow_none=True,
                                                use_builtin_types=True)

        self.fast_rpc = FastRPC(self.addr)

        # 判断是否更改ip
        rfs_ip = kw.get('rfs_ip', None)
        if rfs_ip is not None:
            self.handle.start_command(rfs_ip)
            # self.handle.change_rfs_addr(rfs_ip)
        else:
            # 此时会连接rfsoc的指令接收tcp server
            self.handle.start_command()

        # 配置系统初始值
        system_parameter = kw.get('system_parameter', {})
        values = self.SystemParameter.copy()
        values.update(system_parameter)
        for name, value in values.items():
            if value is not None:
                self.handle.rpc_set(name, value, 1, False)

        # 系统开启前必须进行过一次初始化
        result = self.__exec_command('初始化')
        result = self.__exec_command('DAC配置')
        result = self.__exec_command('ADC配置')
        self.handle.init_dma()
        if not result:
            print(self.handle.get_all_status())

    @solve_rpc_exception
    def close(self, **kw):
        """
        关闭设备
        """
        # self.handle.release_dma()
        # self.handle.close()
        pass

    def write(self, name: str, value, **kw):
        channel = kw.get('ch', 1)
        if name in ['Coefficient']:
            data, f_list, numberOfPoints, phases = get_coef(value, 4e9)
            self.set('PointNumber', int(numberOfPoints), channel)
            # self.set('FrequencyList', f_list, channel)
            self.set('DemodulationParam', data, channel)
            # self.setValue('PhaseList', phases)
        elif name in ['CaptureMode', 'PhaseList']:
            pass
        else:
            return self.set(name, value, channel)

    def read(self, name: str, **kw):
        channel = kw.get('ch', 1)
        result = self.get(name, channel)
        print(name, result.shape)
        return result

    @solve_rpc_exception
    def set(self, name, value=0, channel=1):
        """
        设置设备属性

        :param name: 属性名
                "Waveform"| "Amplitude" | "Offset"| "Output"
        :param value: 属性值
                "Waveform" --> 1d np.ndarray & -1 <= value <= 1
                "Amplitude"| "Offset"| "Phase" --> float    dB | dB | °
                “PRFNum”   采用内部PRF时，可以通过这个参数控制开启后prf的数量
                "Output" --> bool
        :param channel：通道号
        """
        value = RPCValueParser.dump(value)
        if name in {'Waveform', 'GenWave'}:
            func = self.fast_rpc.rpc_set
        else:
            func = self.handle.rpc_set

        if not func(name, value, channel):
            raise xmlrpc.client.Fault(400, '指令执行失败, 请重新open板卡')
            # pass

    @solve_rpc_exception
    def get(self, name, channel=1, value=0):
        """
        查询设备属性，获取数据

        """
        if name in {'TraceIQ', 'IQ'}:
            func = self.fast_rpc.rpc_get
        else:
            func = self.handle.rpc_get

        tmp = func(name, channel, value)
        # tmp = self.handle.rpc_get(name, channel, value)
        tmp = RPCValueParser.load(tmp)
        return tmp

    def __exec_command(self, button_name: str,
                       need_feedback=True, file_name=None, check_feedback=True,
                       callback=lambda *args: True, wait: int = 0):
        flag = self.handle.execute_command(
            button_name, need_feedback, file_name, check_feedback)
        if flag:
            print(f'指令{button_name}执行成功')
        else:
            print(f'指令{button_name}执行失败')
        return flag


class FastRPC:
    def __init__(self, address):
        self.addr = address

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.addr, 10800))
        sock.settimeout(10)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
        # sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60 * 1000, 30 * 1000))
        # sock.close()
        return sock

    def rpc_set(self, *param):
        sock = self.connect()
        a = pickle.dumps(param)
        head = struct.pack('=IIII', *[0x5F5F5F5F, 0x32000001, 0, 16 + len(a)])
        sock.sendall(head)
        sock.sendall(a)
        head = struct.unpack("=IIIII", sock.recv(20))
        # print(head)
        data = sock.recv(head[3] - 20)
        data = pickle.loads(data)
        if head[4]:
            print(data)
            return False
        sock.close()
        return data

    def rpc_get(self, *param):
        sock = self.connect()
        a = pickle.dumps(param)
        head = struct.pack('=IIII', *[0x5F5F5F5F, 0x32000002, 0, 16 + len(a)])
        sock.sendall(head)
        sock.sendall(a)
        head = struct.unpack("=IIIII", sock.recv(20))
        length = head[3] - 20
        data = []
        while length > 0:
            _data = sock.recv(length)
            length -= len(_data)
            data.append(_data)
        data = pickle.loads(b''.join(data))
        if head[4]:
            raise xmlrpc.client.Fault(400, data)
        sock.close()
        return data

    def debug_param(self, *param):
        sock = self.connect()
        a = pickle.dumps(param)
        head = struct.pack('=IIII', *[0x5F5F5F5F, 0x32000003, 0, 16 + len(a)])
        sock.sendall(head)
        sock.sendall(a)
        head = struct.unpack("=IIIII", sock.recv(20))
        length = head[3] - 20
        data = []
        while length > 0:
            _data = sock.recv(length)
            length -= len(_data)
            data.append(_data)
        data = pickle.loads(b''.join(data))
        if head[4]:
            print(data)
            return False
        sock.close()
        return data


class RPCValueParser:
    """
    rpc调用格式化工具集

    """

    @staticmethod
    def dump(value):
        if isinstance(value, np.ndarray):
            value = ['numpy.ndarray', value.tobytes(), str(value.dtype),
                     value.shape]
        elif isinstance(value, float):
            value = float(value)
        elif isinstance(value, int):
            value = int(value)
        elif isinstance(value, np.uint):
            value = int(value)
        elif isinstance(value, (np.complex, complex)):
            value = 'complex', value.real, value.imag
        elif isinstance(value, waveforms.Waveform):
            value = ['waveform.Waveforms', pickle.dumps(value)]
        elif isinstance(value, (list, tuple)):
            value = [RPCValueParser.dump(_v) for _v in value]

        return value

    @staticmethod
    def load(value):
        if isinstance(value, list) and len(value) >= 2:
            if value[0] == 'numpy.ndarray':
                data = np.frombuffer(value[1], dtype=value[2])
                value = data.reshape(value[3])
            # elif: value[0] == 'numpy.float'
            elif value[0] == 'waveform.Waveforms':
                value = pickle.loads(value[1])
            elif value[0] == 'complex':
                value = complex(value[1], value[2])
            else:
                value = [RPCValueParser.load(_v) for _v in value]
        elif isinstance(value, (list, tuple)):
            value = [RPCValueParser.load(_v) for _v in value]
        return value
