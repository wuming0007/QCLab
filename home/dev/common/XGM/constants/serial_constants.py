# -*- coding: utf-8 -*-
"""
串口相关常量定义
"""

# 串口相关常量
SERIAL_CONSTANTS = {
    'MAX_RETRY_COUNT': 10,  # 最大重试次数
    'RETRY_DELAY': 0.01,  # 重试延时（秒）
    'DEFAULT_TIMEOUT': 0.5,  # 默认超时时间（秒）
    'MAX_RECV_SIZE': 32,  # 最大接收数据大小
    'TX_READY_MASK': 0x08,  # 发送就绪掩码
    'RX_READY_MASK': 0x01,  # 接收就绪掩码
    
    # 命令响应验证常量
    'CMD_RESPONSE_START_INDEX': 2,  # 命令响应起始索引
    'CMD_RESPONSE_END_INDEX': 33,   # 命令响应结束索引
    'CMD_RESPONSE_TAIL_INDEX': -1,  # 命令响应尾部索引
}
