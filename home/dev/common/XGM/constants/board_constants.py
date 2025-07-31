# -*- coding: utf-8 -*-
"""
板卡相关常量定义
"""

import logging

# 驱动版本
DRIVER_VERSION = 'V1.0-20250721'

# 板卡类型常量
BOARD_TYPE_DA = 0x22  # DA板卡类型

# 通道配置常量
MAX_DA_CHANNELS = 24
CHANNELS_PER_BOARD = 8
MAX_AD_CHANNELS = 12  # AD通道最大数量

# 固件版本计算常量
VERSION_SCALE_FACTOR = 10.0  # 版本号缩放因子

# 日志级别常量
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
