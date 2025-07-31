# -*- coding: utf-8 -*-
"""
系统管理相关常量定义
"""

# 系统管理相关常量
SYSTEM_CONSTANTS = {
    # 风扇控制相关常量
    'FAN_SPEED_SCALE': 2**24,  # 风扇速度缩放因子
    'FAN_CMD_HEADER_1': 0xaa,  # 风扇命令头1
    'FAN_CMD_HEADER_2': 0x55,  # 风扇命令头2
    'FAN_CMD_PADDING_COUNT': 25,  # 风扇命令填充字节数

    # 系统状态相关常量
    'MAX_TEMPERATURE': 85,  # 最大温度（摄氏度）
    'MIN_TEMPERATURE': -10,  # 最小温度（摄氏度）
    'MAX_FAN_SPEED': 100,  # 最大风扇转速（百分比）
    'MIN_FAN_SPEED': 0,  # 最小风扇转速（百分比）

    # 系统重置相关常量
    'RESET_TIMEOUT': 10.0,  # 系统重置超时时间（秒）
    'RESET_DELAY': 0.1,  # 系统重置延迟时间（秒）

    # 状态码常量
    'STATUS_NORMAL': 'normal',  # 正常状态
    'STATUS_WARNING': 'warning',  # 警告状态
    'STATUS_ERROR': 'error',  # 错误状态
    'STATUS_OFFLINE': 'offline',  # 离线状态
}
