# -*- coding: utf-8 -*-
"""
触发相关常量定义
"""

# 触发相关常量
TRIGGER_CONSTANTS = {
    'INTERNAL_TRIGGER': 0,  # 内部触发
    'EXTERNAL_TRIGGER': 1,  # 外部触发
    'MAX_TRIGGER_SOURCES': 8,  # 最大触发源数量 (0-7)
    'CONTINUOUS_MODE': 1,  # 连续模式
    'SINGLE_MODE': 0,  # 单次模式
    'TRIGGER_PERIOD_SCALE': 0.160,  # 触发周期缩放因子
    'CMD_HEADER': [0xaa, 0x55, 0xaa],  # 命令头
    'CMD_FOOTER': [0x55, 0xaa],  # 命令尾
    'TRIGGER_CMD': 0x02,  # 触发命令
    'TRIGGER_ENABLE': 0x01,  # 触发使能
    'TRIGGER_DISABLE': 0x00,  # 触发禁用

    # 数据包长度常量
    'PACKET_TOTAL_SIZE': 36,  # 数据包总长度（字节）
    'TRIGGER_CONTROL_PADDING_SIZE': 18,  # 触发控制命令填充字节数
    'TRIGGER_CLOSE_PADDING_SIZE': 28,  # 触发关闭命令填充字节数

    # 默认触发参数
    'DEFAULT_TRIGGER_US': 200,  # 默认触发周期（微秒）
    'DEFAULT_TRIGGER_NUM': 1,  # 默认触发次数
    'DEFAULT_TRIGGER_SOURCE': 1,  # 默认触发源（外部）
    'DEFAULT_TRIGGER_CONTINUE': 0,  # 默认触发模式（单次）

    # 触发周期计算常量
    'PERIOD_TIME_NS': 160,  # 周期时间（纳秒）

    # 成功状态码
    'SUCCESS_CODE': 'ok',  # 成功状态码
}
