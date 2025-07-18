import atexit
import pickle
import socket
import struct
import xmlrpc.client
from functools import wraps
from multiprocessing import shared_memory
from xmlrpc.client import Transport

import numpy as np
import waveforms

from dev.common import BaseDriver, Quantity, get_coef

DEBUG_PRINT = True


def print_debug(*args, **kwargs):
    if DEBUG_PRINT:
        print(*args, **kwargs)


@atexit.register
def global_system_exit():
    """
    关闭共享内存

    :return:
    """
    SHARED_DEVICE_MEM.close()
    SHARED_DEVICE_MEM.unlink()


def solve_rpc_exception(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpc.client.Fault as e:
            print(
                f'************{args[0].__class__}: {args[0].addr}************')
            print(f'远程函数报错: {e.faultString}')
            print(args[0].handle.get_all_status())
            print(f'远程函数报错: {e.faultString}')
            print('*****************************')
        except TimeoutError as e:
            print(
                f'************{args[0].__class__}: {args[0].addr}************')
            print(f'Driver报错: 无法连接到 {args[0].addr}\n请检查网络、设备开机状态、设备是否正在程序更新等')
            print(f'{e}')
            print('*****************************')
            raise e
        except socket.timeout as e:
            print(
                f'************{args[0].__class__}: {args[0].addr}************')
            print(f'Driver报错: 获取数据超时 {e}')
            print(args[0].handle.get_all_status())
            print('*****************************')

    return wrapper


class Driver(BaseDriver):
    CHs = list(range(1, 25))

    quants = [
        Quantity('ReInit', value={}, ch=1),  # set/get, 设备重新初始化
        # 采集运行参数
        Quantity('Shot', value=1024, ch=1),  # set/get,运行次数
        Quantity('PointNumber', value=16384, unit='point'),  # set/get,AD采样点数
        Quantity('TriggerDelay', value=0, ch=1, unit='s'),  # set/get,AD采样延时
        Quantity('FrequencyList', value=[], ch=1,
                 unit='Hz'),  # set/get,解调频率列表，list，单位Hz
        Quantity('PhaseList', value=[], ch=1,
                 unit='Hz'),  # set/get,解调频率列表，list，单位Hz
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
        Quantity('KeepAmp', value=False),  # set, 电平是否维持在波形最后一个值
        Quantity('Biasing', value=0, ch=1),  # set, 播放延迟
        Quantity('LinSpace', value=[0, 30e-6, 1000],
                 ch=1),  # set/get, np.linspace函数，用于生成timeline
        Quantity('Output', value=True, ch=1),  # set/get,播放通道开关设置
        Quantity('GenWave', value=waveforms.Waveform(),
                 ch=1),  # set/get, 设备接收waveform对象，根据waveform对象直接生成波形
        # set/get, 设备接收IQ分离的waveform对象列表，根据waveform对象列表直接生成波形
        Quantity('GenWaveIQ',
                 value=[waveforms.Waveform(),
                        waveforms.Waveform()],
                 ch=1),
        Quantity('MultiGenWave', value={1: np.ndarray([])}),  # 多通道波形同时下发
        Quantity('EnableWaveCache', value=False),  # 是否开启waveform缓存
        Quantity('PushWaveCache'),  # 使waveform缓存中的波形数据生效

        # 内触发
        Quantity('GenerateTrig', value=1e7,
                 unit='ns'),  # set/get,触发周期单位ns，触发数量=shot
        Quantity('UpdateFirmware', value='', ch=1),  # qsync固件更新
        Quantity('RestartSystem', value=None),  # 重启系统
    ]

    segment = ('ns', '111|112|113|114|115')

    SystemParameter = {
        'MixMode': 2,  # Mix模式，1：第一奈奎斯特去； 2：第二奈奎斯特区
        'PLLFreq': 100e6,  # 参考时钟频率, 单位为Hz
        'RefClock': 'out',  # 参考时钟选择： ‘out’：外参考时钟；‘in’：内参考时钟
        'ADrate': 4e9,  # AD采样率，单位Hz
        'DArate': 6e9,  # DA采样率，单位Hz
        'KeepAmp': 0,  # DA波形发射完毕后，保持最后一个值
        'Delay': 0,  # 配置DA的原生Delay
    }

    def __init__(self, addr: str = '', timeout: float = 10.0, **kw):
        super().__init__(addr, timeout=timeout, **kw)
        self.fast_rpc = None
        self.handle = None
        self.model = 'NS_MCI'  # 默认为设备名字
        self.srate = 2e9
        self.device_online = True
        self.has_start_capture = False
        print_debug(f'Driver: 实例化成功{addr}')

    @solve_rpc_exception
    def open(self, **kw):
        """
        输入IP打开设备，配置默认超时时间为5秒
        打开设备时配置RFSoC采样时钟，采样时钟以参数定义
        """
        tran = Transport(use_builtin_types=True)
        tran.accept_gzip_encoding = False
        self.handle = xmlrpc.client.ServerProxy(f'http://{self.addr}:10801',
                                                transport=tran,
                                                allow_none=True,
                                                use_builtin_types=True)
        self.fast_rpc = FastRPC(self.addr, self.timeout)
        debug = kw.get('debug', False)
        if debug:
            return
        print_debug('Driver: RPC句柄建立成功')
        # 检查目标设备是否在位设备
        result = self.init_device(**kw)
        if result:
            # 在共享内存中注册本设备的ip
            SHARED_DEVICE_MEM.ip = self.addr
            print(f'{self.addr}开启成功')
        elif result is None:
            ...
        else:
            print(self.handle.get_all_status())

    def init_device(self, **kw):
        try:
            self._connect(self.addr, timeout=1).close()
        except:
            print(f'Driver: {self.addr}不在位')
            self.device_online = False
            return
        print(f'Driver{self.addr}: RPC句柄建立成功')
        # 此时会连接rfsoc的指令接收tcp server
        result = True
        result &= self.handle.start_command(self.timeout)
        print_debug('Driver: 后端rfs网络连接成功')
        print(f'Driver{self.addr}: 后端rfs网络连接成功')

        # 配置系统初始值
        system_parameter = kw.get('system_parameter', {})
        values = self.SystemParameter.copy()
        values.update(system_parameter)
        for name, value in values.items():
            if value is not None:
                self.handle.rpc_set(name, value, 0, False)
        print_debug('Driver: 后端参数配置成功')

        # 系统开启前必须进行过一次初始化
        result &= self.__exec_command('初始化')
        print_debug('Driver: 后端RF配置成功')
        result &= self.handle.rpc_set('Reset')
        print_debug('Driver: 后端缓存配置成功')
        return result

    @solve_rpc_exception
    def close(self, **kw):
        """
        关闭设备
        """
        if getattr(self, 'handle', None) is not None:
            self.handle.close()
            self.handle = None
        if getattr(self, 'fast_rpc', None) is not None:
            self.fast_rpc = None

    def write(self, name: str, value, **kw):
        channel = kw.get('ch', 1)
        if name in {'Coefficient'}:
            data, f_list, numberOfPoints, phases = get_coef(value, 4e9)
            self.set('DemodulationParam', data, channel)
        elif name in {
                'CaptureMode', 'SystemSync', 'ResetTrig', 'TrigPeriod',
                'TrigFrom'
        }:
            pass
        else:
            return self.set(name, value, channel)

    def read(self, name: str, **kw):
        channel = kw.get('ch', 1)
        result = self.get(name, channel)
        # print(name, result.shape)
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
        if not self.device_online:
            return
        print_debug(f'Driver: set操作被调用{name}')
        if name in {'UpdateFirmware'}:
            self.update_firmware(value)
            return
        elif name in {'ReInit'}:
            if not isinstance(value, dict):
                value = {}
            self.init_device(system_parameter=value)
            return
        elif name in {
                'CaptureMode', 'SystemSync', 'ResetTrig', 'TrigPeriod',
                'TrigFrom'
        }:
            return

        value = RPCValueParser.dump(value)
        if name in {
                'Waveform', 'GenWave', 'MultiGenWave', 'GenWaveIQ',
                'DemodulationParam', 'Coefficient', 'RestartSystem'
        }:
            func = self.fast_rpc.rpc_set
            name = 'GenWave' if name == 'Waveform' and value[
                0] == RPCValueParser.dump_tag_waveform else name
        else:
            func = self.handle.rpc_set

        if self.has_start_capture and name == 'StartCapture':
            return
        self.has_start_capture = name == 'StartCapture'

        if not func(name, value, channel):
            raise xmlrpc.client.Fault(400, f'指令{name}执行失败, 请重新open板卡')

    @solve_rpc_exception
    def get(self, name, channel=1, value=0):
        """
        查询设备属性，获取数据

        """
        if not self.device_online:
            return
        print_debug(f'Driver: get操作被调用{name}')
        if name in {'TraceIQ', 'IQ'}:
            func = self.fast_rpc.rpc_get
        else:
            func = self.handle.rpc_get

        self.has_start_capture = False

        tmp = func(name, channel, value)
        # tmp = self.handle.rpc_get(name, channel, value)
        tmp = RPCValueParser.load(tmp)
        return tmp

    def update_firmware(self, file_path):
        if not self.device_online:
            return
        import os
        if not os.path.exists(file_path):
            raise ValueError(f'文件路径: {file_path} 不存在')
        with open(file_path, 'rb') as fp:
            result = self.handle.update_rfs_firmware(fp.read())
        if result:
            print(f'设备{self.addr} 固件更新成功，3s后设备自动重启')
        else:
            print(f'设备{self.addr} 固件更新失败')
        return result

    def __exec_command(self,
                       button_name: str,
                       need_feedback=True,
                       file_name=None,
                       check_feedback=True,
                       callback=lambda *args: True,
                       wait: int = 0):
        flag = self.handle.execute_command(button_name, need_feedback,
                                           file_name, check_feedback)
        if not flag:
            print(f'指令{button_name}执行失败')
        return flag

    def _connect(self, addr=None, port=5001, timeout=None):
        """
        获取到指定ip的tcp连接

        :param addr:
        :param port:
        :return:
        """
        timeout = self.timeout if timeout is None else timeout
        addr = self.addr if addr is None else addr
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((addr, port))
        # sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
        # sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60 * 1000, 30 * 1000))
        # sock.close()
        return sock


class FastRPC:

    def __init__(self, address, timeout):
        self.addr = address
        self.timeout = timeout

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.addr, 10800))
        sock.settimeout(self.timeout)
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
    dump_tag_waveform = 'waveform.Waveforms'
    dump_tag_ndarray = 'numpy.ndarray'
    dump_tag_complex = 'complex'

    @staticmethod
    def dump(value):
        if isinstance(value, np.ndarray):
            value = [
                RPCValueParser.dump_tag_ndarray,
                value.tobytes(),
                str(value.dtype), value.shape
            ]
        elif isinstance(value, float):
            value = float(value)
        elif isinstance(value, int):
            value = int(value)
        elif isinstance(value, np.uint):
            value = int(value)
        elif isinstance(value, complex):
            value = [RPCValueParser.dump_tag_complex, value.real, value.imag]
        elif isinstance(value, waveforms.Waveform):
            value = [RPCValueParser.dump_tag_waveform, pickle.dumps(value)]
        elif isinstance(value, (list, tuple)):
            value = [RPCValueParser.dump(_v) for _v in value]

        return value

    @staticmethod
    def load(value):
        if isinstance(value, list) and len(value) >= 2:
            if value[0] == RPCValueParser.dump_tag_ndarray:
                data = np.frombuffer(value[1], dtype=value[2])
                value = data.reshape(value[3])
            # elif: value[0] == 'numpy.float'
            elif value[0] == RPCValueParser.dump_tag_waveform:
                value = pickle.loads(value[1])
            elif value[0] == RPCValueParser.dump_tag_complex:
                value = complex(value[1], value[2])
            else:
                value = [RPCValueParser.load(_v) for _v in value]
        elif isinstance(value, (list, tuple)):
            value = [RPCValueParser.load(_v) for _v in value]
        return value


class InfoSharedList:
    memory_name = 'NS_DEVICE_MEMORY'
    memory_size = 1024**2
    head_size = 32  # memory中前head_size的长度为头部预留信息

    def __init__(self):
        try:
            self._memory = shared_memory.SharedMemory(name=self.memory_name,
                                                      create=True,
                                                      size=self.memory_size)
        except FileExistsError:
            self._memory = shared_memory.SharedMemory(name=self.memory_name,
                                                      create=False,
                                                      size=self.memory_size)

    def clear_ip(self):
        _exit_pkl = pickle.dumps(self.ip)
        self._memory.buf[self.head_size:len(_exit_pkl) +
                         self.head_size] = b'\x00' * len(_exit_pkl)

    @property
    def ip(self):
        try:
            return pickle.loads(self._memory.buf[self.head_size:])
        except pickle.UnpicklingError:
            return []

    @ip.setter
    def ip(self, value):
        ips = self.ip
        ips.append(value)
        ips = list(set(ips))
        _pkl = pickle.dumps(ips)
        self._memory.buf[self.head_size:len(_pkl) + self.head_size] = _pkl

    def close(self):
        self._memory.close()

    def unlink(self):
        try:
            self._memory.unlink()
        except FileNotFoundError as e:
            pass


SHARED_DEVICE_MEM = InfoSharedList()
