# -*- coding: utf-8 -*-
"""
核心模块初始化文件
"""

from .dll_wrapper import FpgaDevDll
from .ffi_wrapper import FFIWrapper
from .singleton import SingletonMixin
from .register_operations import RegisterOperations
from .dma_operations import DmaOperations
from .board_management import BoardManagement
from .channel_control import ChannelControl
from .serial_communications import SerialCommunications
from .trigger_control import TriggerControl
from .system_management import SystemManagement
from .trigger_management import TriggerManagement

__all__ = [
    'FpgaDevDll',
    'FFIWrapper',
    'SingletonMixin',
    'RegisterOperations',
    'DmaOperations',
    'BoardManagement',
    'ChannelControl',
    'SerialCommunications',
    'TriggerControl',
    'SystemManagement',
    'TriggerManagement'
]
