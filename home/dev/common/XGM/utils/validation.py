# -*- coding: utf-8 -*-
"""
参数验证工具
"""

import numpy as np
from typing import Union, List, Optional


class ValidationUtils:
    """参数验证工具类"""

    @staticmethod
    def validate_slot(slot: str) -> bool:
        """验证槽位参数

        Args:
            slot: 槽位字符串

        Returns:
            bool: 是否有效
        """
        if not isinstance(slot, str):
            return False

        if not slot.startswith('slot'):
            return False

        try:
            slot_num = int(slot[4:])
            return 0 <= slot_num <= 3
        except ValueError:
            return False

    @staticmethod
    def validate_data_size(size: Optional[int]) -> bool:
        """验证数据大小

        Args:
            size: 数据大小

        Returns:
            bool: 是否有效
        """
        if size is None:
            return True

        if not isinstance(size, int):
            return False

        return 0 < size <= 1024 * 1024  # 最大1MB

    @staticmethod
    def validate_channel_number(channel: int, max_channels: int) -> bool:
        """验证通道号

        Args:
            channel: 通道号
            max_channels: 最大通道数

        Returns:
            bool: 是否有效
        """
        if not isinstance(channel, int):
            return False

        return 0 <= channel < max_channels

    @staticmethod
    def validate_data_array(data: Union[List, np.ndarray]) -> bool:
        """验证数据数组

        Args:
            data: 数据数组

        Returns:
            bool: 是否有效
        """
        if isinstance(data, list):
            return len(data) > 0
        elif isinstance(data, np.ndarray):
            return data.size > 0
        else:
            return False

    @staticmethod
    def validate_register_address(addr: int) -> bool:
        """验证寄存器地址

        Args:
            addr: 寄存器地址

        Returns:
            bool: 是否有效
        """
        if not isinstance(addr, int):
            return False

        return 0 <= addr <= 0xFFFF  # 16位地址空间

    @staticmethod
    def validate_trigger_source(trigger_source: int) -> bool:
        """验证触发源

        Args:
            trigger_source: 触发源

        Returns:
            bool: 是否有效
        """
        if not isinstance(trigger_source, int):
            return False

        # 使用常量定义的范围进行验证
        from constants import TRIGGER_CONSTANTS
        return 0 <= trigger_source < TRIGGER_CONSTANTS['MAX_TRIGGER_SOURCES']

    @staticmethod
    def validate_trigger_period(trigger_us: Union[int, float]) -> bool:
        """验证触发周期

        Args:
            trigger_us: 触发周期（微秒）

        Returns:
            bool: 是否有效
        """
        if not isinstance(trigger_us, (int, float)):
            return False

        # 触发周期范围：1微秒到1秒
        return 1.0 <= trigger_us <= 1_000_000.0

    @staticmethod
    def validate_trigger_count(trigger_num: int) -> bool:
        """验证触发次数

        Args:
            trigger_num: 触发次数

        Returns:
            bool: 是否有效
        """
        if not isinstance(trigger_num, int):
            return False

        # 触发次数范围：1到65535
        return 1 <= trigger_num <= 65535

    @staticmethod
    def validate_trigger_number(trigger_num: int) -> bool:
        """验证触发次数（别名方法）

        Args:
            trigger_num: 触发次数

        Returns:
            bool: 是否有效
        """
        return ValidationUtils.validate_trigger_count(trigger_num)

    @staticmethod
    def validate_trigger_mode(trigger_continue: int) -> bool:
        """验证触发模式

        Args:
            trigger_continue: 触发连续模式

        Returns:
            bool: 是否有效
        """
        if not isinstance(trigger_continue, int):
            return False

        # 使用常量定义的值进行验证
        from constants import TRIGGER_CONSTANTS
        valid_modes = [TRIGGER_CONSTANTS['SINGLE_MODE'],
                       TRIGGER_CONSTANTS['CONTINUOUS_MODE']]
        return trigger_continue in valid_modes

    @staticmethod
    def validate_serial_data(data: Union[List, np.ndarray]) -> bool:
        """验证串行数据

        Args:
            data: 串行数据

        Returns:
            bool: 是否有效
        """
        if isinstance(data, list):
            return len(data) > 0 and all(isinstance(x, int) for x in data)
        elif isinstance(data, np.ndarray):
            return data.size > 0 and data.dtype.kind in 'iu'
        else:
            return False

    @staticmethod
    def validate_timeout(timeout: Union[int, float]) -> bool:
        """验证超时时间

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 是否有效
        """
        if not isinstance(timeout, (int, float)):
            return False

        # 超时时间范围：0.1秒到60秒
        return 0.1 <= timeout <= 60.0

    @staticmethod
    def validate_dma_data(data: Union[List, np.ndarray]) -> bool:
        """验证DMA数据

        Args:
            data: DMA数据

        Returns:
            bool: 是否有效
        """
        if isinstance(data, list):
            return len(data) > 0 and all(isinstance(x, (int, float)) for x in data)
        elif isinstance(data, np.ndarray):
            return data.size > 0 and data.dtype.kind in 'iuf'
        else:
            return False

    @staticmethod
    def validate_dma_size(size: int) -> bool:
        """验证DMA大小

        Args:
            size: DMA大小

        Returns:
            bool: 是否有效
        """
        if not isinstance(size, int):
            return False

        # DMA大小范围：1到1MB
        return 1 <= size <= 1024 * 1024

    @staticmethod
    def validate_channel_number(channel: int) -> bool:
        """验证通道号

        Args:
            channel: 通道号

        Returns:
            bool: 是否有效
        """
        if not isinstance(channel, int):
            return False

        return channel >= 0

    @staticmethod
    def validate_dac_channel(channel: int) -> bool:
        """验证DAC通道号

        Args:
            channel: DAC通道号

        Returns:
            bool: 是否有效
        """
        if not isinstance(channel, int):
            return False

        from constants import CHANNEL_CONSTANTS
        return 0 <= channel < CHANNEL_CONSTANTS['MAX_DAC_CHANNELS']

    @staticmethod
    def validate_z_pulse_channel(channel: int) -> bool:
        """验证Z-PULSE通道号

        Args:
            channel: Z-PULSE通道号

        Returns:
            bool: 是否有效
        """
        if not isinstance(channel, int):
            return False

        from constants import CHANNEL_CONSTANTS
        return (CHANNEL_CONSTANTS['Z_PULSE_CHANNEL_START'] <=
                channel <= CHANNEL_CONSTANTS['Z_PULSE_CHANNEL_END'])

    @staticmethod
    def validate_adc_channel(channel: int) -> bool:
        """验证ADC通道号

        Args:
            channel: ADC通道号

        Returns:
            bool: 是否有效
        """
        if not isinstance(channel, int):
            return False

        from constants import CHANNEL_CONSTANTS
        return 0 <= channel < CHANNEL_CONSTANTS['MAX_ADC_CHANNELS']

    @staticmethod
    def validate_trigger_delay(delay: int) -> bool:
        """验证触发延迟

        Args:
            delay: 触发延迟

        Returns:
            bool: 是否有效
        """
        if not isinstance(delay, int):
            return False

        return delay >= 0

    @staticmethod
    def validate_replay_times(times: int) -> bool:
        """验证重放次数

        Args:
            times: 重放次数

        Returns:
            bool: 是否有效
        """
        if not isinstance(times, int):
            return False

        return times > 0

    @staticmethod
    def validate_save_length(length: int) -> bool:
        """验证保存长度

        Args:
            length: 保存长度

        Returns:
            bool: 是否有效
        """
        if not isinstance(length, int):
            return False

        return length > 0

    @staticmethod
    def validate_channel_offset(offset: float) -> bool:
        """验证通道偏移

        Args:
            offset: 通道偏移值

        Returns:
            bool: 是否有效
        """
        if not isinstance(offset, (int, float)):
            return False

        # 可以根据实际需求设置偏移范围
        return -1000.0 <= offset <= 1000.0
