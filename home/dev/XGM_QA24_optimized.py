"""
XGM_QA24 设备驱动优化版本
提供更现代、更健壮的量子测量设备驱动实现

可以进一步考虑将隐藏方法写到下层driver里去。
"""

import time
import logging
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from waveforms import Waveform, wave_eval

from .common import BaseDriver, QBool, QInteger, QReal, QVector
from .common.quantity import QString
from .common.XGM import qa24 as fpgadev # 导入FPGA设备接口，这句话我有点不太理解
from .update_ip import update_ip    #？？？干什么用的？似乎也没用

# 配置日志
logger = logging.getLogger(__name__)

# 版本信息
QA_SYSTEMQ_VER = 'qa-systemq版本 : V1.1-20250523'

class TriggerSource(Enum):
    """触发源枚举"""
    INTERNAL = 0
    EXTERNAL = 1

class CaptureMode(Enum):
    """采集模式枚举"""
    ALG = 'alg'      # 纯硬解调
    RAW = 'raw'      # 纯软解调
    RAW_ALG = 'raw_alg'  # 软硬皆有

@dataclass
class DeviceConfig:
    """设备配置数据类"""
    sampling_rate: float = 8e9
    adc_sampling_rate: float = 2.5e9
    channel_count: int = 24
    trigger_period_us: float = 200
    trigger_number: int = 1
    trigger_source: TriggerSource = TriggerSource.EXTERNAL
    trigger_continue: bool = False
    intrinsic_waveform_length: float = 65e-6

@dataclass
class ChannelConfig:
    """通道配置数据类"""
    use_algorithm: bool = True
    use_raw: bool = False
    algorithm_freq_count: int = 0
    nyquist_zone: Optional[str] = None
    trigger_delay_sub: float = 0.0

def new_round(_float: float, _len: int) -> float:
    """
    四舍五入保留小数位
    这个函数的目的是为了保证正确进位。系统内置的round函数在末位是5且保留小数位数小于原小数位数时，会向后进位。
    举例来说，1.2345，保留3位小数，正常应该四舍五入位1.235，但系统内置的round函数会四舍五入位1.234。
    为确保正确进位，当遇到这种情况时，本函数将最后一位替换为6，以确保能够正确进位。
    
    Args:
        _float: 输入浮点数
        _len: 保留的小数位
        
    Returns:
        四舍五入后的浮点数
    """
    _float = float(_float)
    if len(str(_float).split('.')[1]) <= _len:  #取出小数位的长度，如果小于等于_len，则直接四舍五入。
        return round(_float, _len)
    elif str(_float)[-1] == '5':    #如果小数最后一位是5，则将其改成6，以确保能够正确进位。
        return round(float(str(_float)[:-1] + '6'), _len)
    else:
        return round(_float, _len)

#这个get_coef函数在systemq中有，这里应该是为了适配多次读取而写的。在这里定义的new_round, get_coef等函数，应该放到我们自己的工具库中去。
def get_coef(coef_info: Dict[str, Any], sampleRate: float) -> Tuple[np.ndarray, np.ndarray, List, int, List, List, List]:
    """
    计算解调相关的系数和参数
    
    Args:
        coef_info: 系数信息字典
        sampleRate: 采样率
        
    Returns:
        波形列表、频率列表、相位等参数
    """
    start, stop = coef_info['start'], coef_info['stop'] #需解模的数据在时间轴上的起点和终点。
    numberOfPoints = int((stop - start) * sampleRate) #计算需解模的数据长度。
    if numberOfPoints % 1024 != 0: #如果长度不是1024的整数倍，则补齐到1024的整数倍。1024应该定义为一个常量，比如MIN_LENGTH。
        numberOfPoints = numberOfPoints + 1024 - numberOfPoints % 1024
    t = np.arange(numberOfPoints) / sampleRate + start #计算需解模的数据在时间轴上的时间点。

    fList = []  #解调频率列表
    wList = []  #权重列表
    phases = []  #相位列表
    steds = []  #起点-终点列表
    phi = []  #相位列表

    for kw in coef_info['wList']:
        #这里应该给出权重列表的格式和权重计算公式。
        Delta, t0, weight, w, phase, phase_s = kw['Delta'], kw['t0'], kw['weight'], kw['w'], kw['phase'], kw['phi']
        fList.append(Delta)
        phi.append(phase_s)
        
        if w is not None:
            w = np.zeros(numberOfPoints, dtype=complex)
            w[:len(w)] = w
            # w = shift(w, t0 - start)  # 注释掉未使用的导入
            phases.append(np.mod(phase + 2 * np.pi * Delta * start, 2*np.pi))
        else:
            weight = weight
            if isinstance(weight, np.ndarray):
                pass
            else:
                if isinstance(weight, str):
                    fun = wave_eval(weight) >> t0
                elif isinstance(weight, Waveform):
                    fun = weight >> t0
                else:
                    raise TypeError(f'Unsupported type {weight}')
                weight = fun(t)
            steds.append([fun.bounds[0], fun.bounds[-2]])
            phase += 2 * np.pi * Delta * start
            phases.append(np.mod(phase, 2*np.pi))
        wList.append(w)
    
    ffs = np.unique(fList)
    phis = [[] for f in ffs]
    ffs_num = 0
    
    ffs[0] = fList[0]
    phis[0] = phi[0]
    f_now = fList[0]
    phi_now = phi[0]
    
    for i in range(len(fList)):
        if f_now != fList[i]:
            f_now = fList[i]
            phi_now = phi[i]
            ffs_num += 1
            ffs[ffs_num] = f_now
            phis[ffs_num] = phi_now
        if ffs_num == len(ffs)-1:
            break
    
    new_fList, new_sted, rnks = [], [[] for f in ffs], [[] for f in ffs]
    for i, freq in enumerate(fList):
        for ind in range(len(ffs)):
            if ffs[ind] == freq:
                break
        new_sted[ind].append(np.round(np.array(steds[i])*sampleRate))
        rnks[ind].append(i)
    
    return np.asarray(wList), ffs, phis, numberOfPoints, phases, new_sted, rnks

class XGM_QA24Driver(BaseDriver):
    """
    XGM_QA24 量子测量设备驱动类
    
    提供完整的量子比特测量功能，包括：
    - 多通道数据采集
    - 硬解调和软解调
    - 波形生成和回放
    - 触发控制
    """
    
    # 支持的设备模型
    SUPPORTED_MODELS = ['XGM_MDS24']    #这里的设备model是不是可以列更多种？比如XGM_QA24？
    
    def __init__(self, addr: str, **kwargs):
        """
        初始化驱动实例
        
        Args:
            addr: 设备地址
            **kwargs: 额外配置参数
        """
        logger.info(f"初始化 XGM_QA24 驱动，版本: {QA_SYSTEMQ_VER}")
        print(QA_SYSTEMQ_VER)
        
        super().__init__(addr=addr, **kwargs)
        
        # 设备配置
        self.config = DeviceConfig()
        self.model = 'XGM_MDS24'
        self.handle = fpgadev()
        self._data_mixtype = 'normal'
        self.srate = 8e9    #srate应该是计算波形数据时用的采样率，不是设备的硬件采样率。
        self.adc_srate = 2.5e9
        self.system_net = update_ip()   #没找到这个函数的来源。update_ip()似乎是返回了一个handle。
        
        # 通道配置
        self.channels = list(range(1, self.config.channel_count + 1))
        self.channel_configs: Dict[int, ChannelConfig] = {
            ch: ChannelConfig() for ch in self.channels
        }
        
        # 设备状态
        self._is_connected = False
        
        # 通道状态
        self.alg_use = [True] * self.config.channel_count
        self.raw_use = [False] * self.config.channel_count
        self.alg_num = [0] * self.config.channel_count
        
        # 设备参数
        self._sampling_mode = None
        self._nyquist = [None] * self.config.channel_count
        self._trigger_us = 200
        self._trigger_num = 1
        self._trigger_source = 1
        self._trigger_continue = 0
        self._intrinsic_waveform_length = 65e-6
        self._trigger_delay_sub = [0] * self.config.channel_count
        
        # 定义设备属性
        self._define_quantities()
        
        logger.info("驱动初始化完成")
    
    def _define_quantities(self):
        """定义设备属性"""
        self.quants = [
            # 系统设置
            QVector('Set_dev_ip', ch=1, value=[]),
            QBool('dev_shutdown', ch=1, value=False),
            QBool('dev_reboot', ch=1, value=False),
            
            # 触发控制
            QString('TriggerSource', ch=1, value='External'),
            QReal('TriggerPeriod', ch=1, unit='s', value=200e-6),
            QInteger('TriggerNumber', ch=1, unit='', value=1),
            QBool('TriggerContinue', ch=1, value=False),
            QReal('TriggerDelay', value=0, unit='s', ch=1),
            QReal('StartDelay', value=0, unit='s', ch=1),
            QInteger('Trigger', value=0, ch=1),
            
            # 采样率设置
            QInteger('SamplingRate', ch=1, value=8000),
            QInteger('XY-SamplingRate', ch=1, value=8000),
            QInteger('Z-SamplingRate', ch=1, value=8000),
            QInteger('RO-SamplingRate', ch=1, value=8000),
            
            # DA输出设置
            QInteger('Output', value=1, ch=1),
            QVector('Waveform', value=[], ch=1),
            QVector('Pulse', value=[], ch=1),
            QBool('WaveformContinue', value=False, ch=1),
            QString('Nyquist', value='mix', ch=1),
            QString('Data_mixtype', value='normal', ch=1),
            
            # AD采集设置
            QReal('FrequencyList', value=[], unit='Hz', ch=1),
            QReal('PhaseList', value=[], unit='1', ch=1),
            QReal('Delta_PhaseList', value=[], unit='1', ch=1),
            QInteger('Shot', value=2048, ch=1),
            QInteger('PointNumber', value=2048, ch=1),
            QBool('avg', value=False, ch=1),
            QInteger('Coefficient', value=None, ch=1),
            QVector('TraceIQ', value=[], ch=1),
            QVector('IQ', value=[], ch=1),
            QVector('Sample_time', value=[], ch=1),
            QVector('rnks', value=[], ch=1),
            QInteger('StartCapture', value=1, ch=1),
            QString('CaptureMode', value='alg', ch=1),
        ]
    
    def open(self) -> bool:
        """
        打开设备并初始化设置
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("正在连接设备...")
            
            # 设置采样率
            self.setValue('SamplingRate', 8000) #采样率应该与self.srate一致
            
            # 设置Nyquist区 - 使用实际板卡数量而不是硬编码
            for i in range(self.handle.board_number):
                self.handle.rfdac_SetNyquistZone(NyquistZone=1, board_num=i)
            
            self._is_connected = True
            logger.info("设备连接成功")
            return True
            
        except Exception as e:
            logger.error(f"设备连接失败: {e}")
            self._is_connected = False
            return False
    
    def close(self, **kwargs) -> None:
        """关闭设备连接"""
        try:
            logger.info("正在关闭设备连接...")
            result = super().close(**kwargs)
            self._is_connected = False
            logger.info("设备连接已关闭")
            return result
        except Exception as e:
            logger.error(f"关闭设备连接时出错: {e}")
    
    def write(self, name: str, value: Any, **kwargs) -> Any:
        """
        向设备写入数据
        
        Args:
            name: 属性名称
            value: 属性值
            **kwargs: 额外参数
            
        Returns:
            写入的值
        """
        try:
            ch = int(kwargs.get('ch', 1))    # 获取通道号，如果不指定，则默认通道1，确保为整数类型
        except (ValueError, TypeError):
            raise ValueError(f"通道号必须是整数，当前值: {kwargs.get('ch', 1)}")
        
        try:
            logger.debug(f"写入属性 {name} = {value} (通道 {ch})")
            
            # 触发相关设置
            if name.startswith('Trigger'):
                self._set_trigger(name, value)
            
            # AD通道设置 (通道13-24)
            elif name in ['Coefficient', 'CaptureMode', 'StartCapture', 'TriggerDelay', 'PointNumber', 'Shot', 'avg']:
                if 12 < ch < 25:    #这里要考虑结合通道映射表，因为不同设备通道排列不同。
                    self._set_ad(name, value, ch)
                else:
                    raise ValueError('AD channel number error!!!')
            
            # 脉冲设置
            elif name in ['Pulse']: #这个功能尚未实现，后续可以逐步实现。
                logger.info(f"Qiskit pulse test: {value}")
            
            # DA通道设置 (通道1-12)
            elif name in ['Waveform', 'Output', 'Nyquist', 'WaveformContinue']:
                if 0 < ch < 13: #这里要考虑结合通道映射表，因为不同设备通道排列不同。
                    self._set_da(name, value, ch)
                else:
                    raise ValueError('DA channel number error!!!')
            
            # 采样率设置
            elif name in ['SamplingRate']:
                # 200M应该设置为一个常量。
                new_sr = round(value/200) * 200     # 采样率必须为200的整数倍。这里规则应该进一步细化，因为rfsoc芯片对某些区段的采样率是不支持的
                for i in range(self.handle.board_number):
                    self.handle.rfdac_sampling(new_sr, i)
                
                if self._data_mixtype == 'normal':
                    self.srate = new_sr * 1e6   #1e6也应该设置为一个常量
                else:
                    self.srate = new_sr * 1e6 / 2   #对数据进行了插值。
                logger.info(f"采样率设置为: {self.srate}")
            
            # 数据混合类型设置
            elif name in ['Data_mixtype']:
                self._set_data_mixtype(value)
            
            # 设备IP设置
            elif name in ['Set_dev_ip']:
                logger.info(f"设置设备IP: {value}")
                self.system_net.set_ip(value[0], value[1], value[2])
            
            # 设备关机
            elif name in ['dev_shutdown']:
                if value:
                    self.system_net.shutdown()
            
            # 设备重启
            elif name in ['dev_reboot']:
                if value:
                    self.system_net.reboot()
            
            return value
            
        except Exception as e:
            logger.error(f"写入属性 {name} 失败: {e}")
            raise
    
    def read(self, name: str, **kwargs) -> Any:
        """
        从设备读取数据
        
        Args:
            name: 属性名称
            **kwargs: 额外参数
            
        Returns:
            读取的值
        """
        try:
            ch = int(kwargs.get('ch', 1))    # 确保通道号为整数类型
        except (ValueError, TypeError):
            raise ValueError(f"通道号必须是整数，当前值: {kwargs.get('ch', 1)}")
        
        try:
            logger.debug(f"读取属性 {name} (通道 {ch})")
            #后面要做内嵌的判决和统计的话，这里还应该返回states和计数信息。
            if name in ['TraceIQ', 'IQ']:
                if name == 'TraceIQ':
                    assert self.raw_use[ch-1], 'Trace is not collected. Please check settings.'
                    avg = self.config['avg'][ch]['value']
                    return self.getTraces(avg=avg, timeout=None, ch=ch)
                elif name == 'IQ':
                    assert self.alg_use[ch-1], 'IQ is not collected. Please check settings.'
                    avg = self.config['avg'][ch]['value']
                    return self.get_IQ_alg(avg=avg, timeout=None, ch=ch)
            else:
                return super().read(name, ch=ch, **kwargs)
                
        except Exception as e:
            logger.error(f"读取属性 {name} 失败: {e}")
            raise
    
    def _set_trigger(self, name: str, value: Any) -> None:
        """设置触发相关参数"""
        if name == 'TriggerPeriod':
            periodTime = 160    #160ns应该设置为一个常量。160ns对应触发采样周期（6.25MHz）。trigger周期必须为160ns的整数倍。
            times = new_round(value * 1e9 / periodTime, 0)    #1e9应该设置为一个常量。
            assert periodTime * times == value * 1e9, 'Sampling mode does not match triggerTime! Please change trigger_us via setValue() function'
            self._trigger_us = value * 1e6    #1e6应该设置为一个常量。
        elif name == 'TriggerSource':   #可以做成一个枚举。
            assert value in ['Internal', 'External'], 'Trigger source is not supported.'
            self._trigger_source = int(value == 'External')
        elif name == 'TriggerNumber':   #triggernumber应该也要做个类型检查，比如必须是整数，不能是负数。等等
            self._trigger_num = value
        elif name == 'TriggerContinue':
            self._trigger_continue = int(value)
        elif name == 'Trigger':
            self._trigger_device()
    
    def _set_da(self, name: str, value: Any, ch: int) -> None:
        """设置DA通道参数"""
        if name == 'Waveform':
            continuous = self.config['WaveformContinue'][ch]['value']
            delay = 0   #初始化delay为0，后续会根据波形数据计算实际delay。
            ch_srate = self.srate
            
            if isinstance(value, Waveform):
                if np.isinf(value.bounds[0]):
                    delay = 0
                    length = 1e-6
                else:
                    delay = new_round(value.bounds[0] * ch_srate, 0) / ch_srate
                    length = new_round((value.bounds[-2] - value.bounds[0]) * ch_srate, 0) / ch_srate
                value <<= delay
                value.start, value.stop = 0, length
                value = value.sample(ch_srate)
            
            if self._data_mixtype == 'normal':
                ch_srate = ch_srate
            else:
                ch_srate = ch_srate * 2
            
            trigger_delay = new_round(delay * ch_srate, 0)
            self._write_waveform(value, ch=ch, trigger_delay=trigger_delay, continuous=continuous)
            
        elif name == 'Output':
            if value:
                self._enable_channel(ch)
            else:
                self._disable_channel(ch)
                
        elif name == 'Nyquist':
            if value == 'normal':
                if self._nyquist[ch-1] in ['mix', None]:
                    self.handle.rfdac_SetNyquistZone(NyquistZone=0, board_num=int((ch-1)//8))   #通道号和board_num的对应关系应该建立一个映射字典。
                    self._nyquist[ch-1] = 'normal'
                    time.sleep(0.1)
            elif value == 'mix':
                if self._nyquist[ch-1] in ['normal', None]:
                    self.handle.rfdac_SetNyquistZone(NyquistZone=1, board_num=int((ch-1)//8))
                    self._nyquist[ch-1] = 'mix'
                    time.sleep(0.1)
                    
        elif name == 'WaveformContinue':
            self.config['WaveformContinue'][ch]['value'] = value
    
    def _set_ad(self, name: str, value: Any, ch: int) -> None:
        """设置AD通道参数"""
        if name == 'Coefficient':
            self.config['StartDelay'][ch]['value'] = value['start']
            for i in range(len(value['wList'])):
                value['wList'][i]['t0'] -= value['start']
            value['stop'] -= value['start']
            value['start'] = 0

            wList, f_list, phi, numberOfPoints, phases, new_sted, rnks = get_coef(value, self.adc_srate)
            
            assert len(f_list) in range(1, 17), f'Invalid coefficient number of frequencies.'   #可解调的模式数最大为16，这个应该设置为常量！
            self.config['PointNumber'][ch]['value'] = numberOfPoints
            self.config['FrequencyList'][ch]['value'] = f_list
            self.config['PhaseList'][ch]['value'] = phases
            self.config['Delta_PhaseList'][ch]['value'] = phi
            self.config['Sample_time'][ch]['value'] = new_sted
            self.config['rnks'][ch]['value'] = rnks
            
        elif name == 'CaptureMode':
            assert value in ['alg', 'raw', 'raw_alg'], f'Other mode is not supported.'
            self.alg_use[ch-1] = (value != 'raw')
            self.raw_use[ch-1] = (value != 'alg')
            
        elif name == 'StartCapture':
            self.start_capture(ch=ch)
            
        elif name == 'TriggerDelay':
            self.config['TriggerDelay'][ch]['value'] = value
            
        elif name == 'PointNumber':
            self.config['PointNumber'][ch]['value'] = value
            
        elif name == 'Shot':
            self.config['Shot'][ch]['value'] = value
            
        elif name == 'avg':
            self.config['avg'][ch]['value'] = value
    
    def _set_data_mixtype(self, value: str) -> None:    #4种mixtype：normal,mix_p1,mix_0,mix_n1 分别是什么意思？这要问下于海
        """设置数据混合类型"""
        if value == 'normal':
            if self._data_mixtype in ['mix_p1', 'mix_0', 'mix_n1', None]:
                for i in range(12):
                    self.handle.dac_replay_type(chennel_num=i, replay_type=0)
                self._data_mixtype = 'normal'
        elif value == 'mix_p1':
            if self._data_mixtype in ['normal', 'mix_0', 'mix_n1', None]:
                for i in range(12):
                    self.handle.dac_replay_type(chennel_num=i, replay_type=1)
                self._data_mixtype = 'mix_p1'
        elif value == 'mix_0':
            if self._data_mixtype in ['normal', 'mix_p1', 'mix_n1', None]:
                for i in range(12):
                    self.handle.dac_replay_type(chennel_num=i, replay_type=2)
                self._data_mixtype = 'mix_0'
        elif value == 'mix_n1':
            if self._data_mixtype in ['normal', 'mix_p1', 'mix_0', None]:
                for i in range(12):
                    self.handle.dac_replay_type(chennel_num=i, replay_type=3)
                self._data_mixtype = 'mix_n1'
        else:
            raise ValueError('Data_mixtype error!!!')
    
    def _trigger_device(self) -> None:
        """触发设备"""
        try:
            logger.info("触发设备")
            ret = self.handle.trigger_ctrl(
                trigger_source=self._trigger_source,
                trigger_us=self._trigger_us,
                trigger_num=self._trigger_num,
                trigger_continue=self._trigger_continue
            )
            assert ret == 'ok', 'Error in `Trig()`'
        except Exception as e:
            logger.error(f"触发设备失败: {e}")
            raise
    
    def _write_waveform(self, data: np.ndarray, ch: int, trigger_delay: float = 0, continuous: bool = False) -> None:
        """
        向指定通道写入波形数据
        
        Args:
            data: 波形数据
            ch: 通道号
            trigger_delay: 触发延迟
            continuous: 是否连续播放
        """
        try:
            data = np.asarray(data).clip(-1, 1)
            data_len = len(data)
            
            if data_len > 2**19:    #2**19为波形最大深度，这个应该设置为常量。
                logger.error('write dac data too long !!!')
                return 'write dac data too long !!!'

            replay_cnt = 100000000    #100000000应该设置为常量。
            replay_continue_flag = int(continuous)
            
            logger.info(f"向通道 {ch} 写入波形数据，长度: {len(data)}")
            self.handle.dac_updata(ch-1, trigger_delay, replay_cnt, replay_continue_flag, data)
            
        except Exception as e:
            logger.error(f"写入波形数据失败: {e}")
            raise
    
    def _enable_channel(self, ch: int) -> None:
        """启用通道"""
        try:
            logger.info(f"启用通道 {ch}")
            ret = self.handle.dac_open(ch-1)
            assert ret == 'ok', 'Error in `on()`'
        except Exception as e:
            logger.error(f"启用通道 {ch} 失败: {e}")
            raise
    
    def _disable_channel(self, ch: int) -> None:
        """禁用通道"""
        try:
            logger.info(f"禁用通道 {ch}")
            ret = self.handle.dac_close(ch-1)
            assert ret == 'ok', 'Error in `off()`'
        except Exception as e:
            logger.error(f"禁用通道 {ch} 失败: {e}")
            raise
    
    def start_capture(self, ch: int = 1) -> None:
        """
        开始指定通道的采集
        
        Args:
            ch: 通道号
        """
        try:
            logger.info(f"开始通道 {ch} 的数据采集")
            self._adc_control(ch=ch, enable=1)
        except Exception as e:
            logger.error(f"启动数据采集失败: {e}")
            raise
    
    def _adc_control(self, ch: int = 1, enable: int = 1) -> None:
        """
        控制ADC采集
        
        Args:
            ch: 通道号
            enable: 启用标志
        """
        try:
            trigger_delay_point = new_round((self.config['TriggerDelay'][ch]['value']) * 1e12, 0) / int(400)    #这句有点奇怪。400应该设置为常量。
            trigger_delay = new_round(trigger_delay_point, 0)
            self._trigger_delay_sub[ch-1] = trigger_delay / self.adc_srate
            
            save_len = self.config['PointNumber'][ch]['value']
            times = self.config['Shot'][ch]['value']

            if self.raw_use[ch-1]:
                ret = self.handle.rd_adc_data_ctrl(ch-13, trigger_delay, times, save_len)   #ch-13的写法不规范。应该建立一个通道映射表。
            elif self.alg_use[ch-1]:
                f_list = self.config['FrequencyList'][ch]['value']
                phase_list = self.config['PhaseList'][ch]['value']
                Sample_time_list = self.config['Sample_time'][ch]['value']

                self.alg_num[ch-1] = len(f_list)
                mul_f = []
                for i in range(len(f_list)):
                    mul_f_i = []
                    mul_f_i.append(phase_list[i])
                    mul_f_i.append(f_list[i])
                    mul_f_i.append(Sample_time_list[i])
                    mul_f.append(mul_f_i)
                
                ret = self.handle.rd_adc_mul_data_ctrl(ch-13, trigger_delay, times, save_len, mul_f)

            assert ret == 'ok', f'Error in `_adc_control({ch}) all`'
            
        except Exception as e:
            logger.error(f"ADC控制失败: {e}")
            raise
    
    def get_data(self, ch: int = 1, timeout: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取原始数据
        
        Args:
            ch: 通道号
            timeout: 超时时间
            
        Returns:
            I和Q数据
        """
        try:
            time0 = time.time()
            save_len = self.config['PointNumber'][ch]['value']
            times = self.config['Shot'][ch]['value']
            
            if save_len > 2**17:    #2**17为最大采集长度（128k），这个应该设置为常量。
                return 'adc save data too long !!!'

            while True:
                adc_data_buf, adc_data_save_len = self.handle.rd_adc_data(ch-13, times, save_len)
                if adc_data_save_len != -1:
                    break
                else:
                    time1 = time.time()
                    if time1 - time0 > (self.timeout if timeout is None else timeout):
                        raise Exception('rd_adc_data_return timeout!')

            return adc_data_buf, np.zeros_like(adc_data_buf)
            
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            raise
    
    def getTraces(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取轨迹数据
        
        Args:
            avg: 是否平均
            ch: 通道号
            timeout: 超时时间
            
        Returns:
            I和Q轨迹
        """
        try:
            cha, chb = self.get_data(ch=ch, timeout=timeout)
            if avg:
                times = self.config['Shot'][ch]['value']
                return cha/times, chb/times
            else:
                return cha, chb
        except Exception as e:
            logger.error(f"获取轨迹数据失败: {e}")
            raise
    
    def get_data_alg(self, ch: int = 1, timeout: Optional[float] = None) -> np.ndarray:
        """
        获取算法处理后的数据
        
        Args:
            ch: 通道号
            timeout: 超时时间
            
        Returns:
            处理后的数据
        """
        try:
            times = self.config['Shot'][ch]['value']
            assert self.alg_num[ch-1] > 0, 'Hard demod coefficient is not set.'
            
            rnks = np.array(self.config['rnks'][ch]['value'], dtype=object)
            
            adc_data = []
            for i in range(len(rnks)):
                for j in range(len(rnks[i])):
                    adc_data.append([])
            
            trig_point_sub = []
            for modle_num in range(len(self.config['Sample_time'][ch]['value'])):
                trig_point_sub_sub = []
                for samp_n in range(len(self.config['Sample_time'][ch]['value'][modle_num])):
                    trig_point_sub_sub.append(
                        self._trigger_delay_sub[ch-1] + 
                        self.config['Sample_time'][ch]['value'][modle_num][samp_n][0] / 2.5e9
                    )
                trig_point_sub.append(trig_point_sub_sub)

            f_list = self.config['FrequencyList'][ch]['value']
            for modle_num in range(self.alg_num[ch-1]):
                while True:
                    mul_data_bufe, read_data_len = self.handle.rd_adc_mul_data(ch-13, modle_num, times)
                    if read_data_len != -1:
                        break
                
                sample_times = len(self.config['Sample_time'][ch]['value'][modle_num])
                mul_data_bufe = np.reshape(mul_data_bufe, (sample_times, -1), order='f')
                
                for i in range(len(trig_point_sub[modle_num])):
                    mul_data_bufe[i] = mul_data_bufe[i] * np.exp(1j * 2 * np.pi * f_list[modle_num] * trig_point_sub[modle_num][i])
                
                for i in range(len(rnks[modle_num])):
                    adc_data[rnks[modle_num][i]] = mul_data_bufe[i]
            
            adc_data = np.array(adc_data).T
            return adc_data
            
        except Exception as e:
            logger.error(f"获取算法数据失败: {e}")
            raise
    
    def get_IQ_alg(self, avg: bool = False, ch: int = 1, timeout: Optional[float] = None) -> np.ndarray:
        """
        获取IQ算法数据
        
        Args:
            avg: 是否平均
            ch: 通道号
            timeout: 超时时间
            
        Returns:
            IQ数据
        """
        try:
            data_alg = self.get_data_alg(ch=ch, timeout=timeout)
            if avg:
                return np.mean(data_alg, axis=1)
            else:
                return data_alg
        except Exception as e:
            logger.error(f"获取IQ算法数据失败: {e}")
            raise
    
    def triggerClose(self) -> None:
        """关闭触发器"""
        try:
            ret = self.handle.trigger_close()
            assert ret == 'ok', 'Error in `triggerClose()`'
        except Exception as e:
            logger.error(f"关闭触发器失败: {e}")
            raise
    
    def channel_ip(self) -> str:
        """获取通道IP地址"""
        return self.handle.dev_id.da
    
    @property
    def is_connected(self) -> bool:
        """设备连接状态"""
        return self._is_connected
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取设备状态信息
        
        Returns:
            状态信息字典
        """
        return {
            'connected': self.is_connected,
            'model': self.model,
            'channels': len(self.channels),
            'sampling_rate': self.srate,
            'adc_sampling_rate': self.adc_srate,
            'data_mixtype': self._data_mixtype,
            'trigger_source': 'External' if self._trigger_source else 'Internal',
            'trigger_period_us': self._trigger_us,
        }


# 兼容性别名
Driver = XGM_QA24Driver