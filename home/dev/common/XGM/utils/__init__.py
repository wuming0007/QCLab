# -*- coding: utf-8 -*-
"""
工具模块初始化文件
"""

from .logging_config import setup_logging
from .validation import ValidationUtils
from .compatibility import BackwardCompatibilityMixin
from .exceptions import (
    FpgaDevError, BoardNotFoundError, RegisterAccessError,
    ValidationError, HardwareError, ConfigurationError,
    CommunicationError, TimeoutError, get_error_description, handle_device_error
)

__all__ = [
    'setup_logging',
    'ValidationUtils',
    'BackwardCompatibilityMixin',
    # 错误处理
    'FpgaDevError',
    'BoardNotFoundError',
    'RegisterAccessError',
    'ValidationError',
    # 'FeatureError',  # 已移除
    'HardwareError',
    'ConfigurationError',
    'CommunicationError',
    'TimeoutError',
    'get_error_description',
    'handle_device_error',
]
