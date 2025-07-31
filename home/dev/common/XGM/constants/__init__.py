# -*- coding: utf-8 -*-
"""
常量模块初始化文件
"""

from .board_constants import *
from .register_constants import *
from .dma_constants import *
from .channel_constants import *
from .serial_constants import *
from .trigger_constants import *
from .data_constants import *
from .time_constants import *
from .system_constants import *

__all__ = [
    # 板卡常量
    'BOARD_TYPE_DA', 'MAX_DA_CHANNELS', 'CHANNELS_PER_BOARD', 'MAX_AD_CHANNELS',
    'DRIVER_VERSION', 'VERSION_SCALE_FACTOR',

    # 寄存器常量
    'FIRMWARE_REGISTERS', 'REGISTER_CONSTANTS',

    # DMA常量
    'DMA_CONSTANTS', 'ADDRESS_CONSTANTS',

    # 通道常量
    'CHANNEL_CONSTANTS',

    # 串口常量
    'SERIAL_CONSTANTS',

    # 触发常量
    'TRIGGER_CONSTANTS',

    # 数据常量
    'DATA_LIMITS',

    # 时间常量
    'TIME_CONSTANTS',

    # 系统常量
    'SYSTEM_CONSTANTS',

    # 日志常量
    'LOG_LEVELS',
]
