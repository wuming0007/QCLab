# -*- coding: utf-8 -*-
"""
通道相关常量定义
"""

# 通道和限制常量
CHANNEL_CONSTANTS = {
    'MAX_DAC_CHANNELS': 24,  # 最大DAC通道数
    'MAX_ADC_CHANNELS': 12,  # 最大ADC通道数
    'MAX_MUL_MODULES': 16,  # 最大乘法模块数
    'MAX_MUL_FREQUENCIES': 16,  # 最大乘法频率数
    'Z_PULSE_CHANNEL_START': 8,  # Z-PULSE通道起始
    'Z_PULSE_CHANNEL_END': 15,  # Z-PULSE通道结束

    # DC偏移相关常量
    'DC_OFFSET_CHANNELS': 8,  # DC偏移通道数量
    'Z_PULSE_TO_DC_OFFSET': 8,  # Z-PULSE通道到DC偏移通道的偏移量
    'DC_OFFSET_BASE_ADDR': 32,  # DC偏移寄存器基地址
    'DC_OFFSET_LAST_INDEX': 7,  # DC偏移数组最后一个索引
    'DC_CMD_REG_ADDR': 17,  # DC命令寄存器地址
    'DC_STATUS_REG_ADDR': 0x0,  # DC状态寄存器地址
    'DC_CMD_OFFSET': 2,  # DC命令寄存器偏移
    'DC_PASSWORD_SHIFT': 3,  # DC密码左移位数
    'DC_CMD_SHIFT': 1,  # DC命令左移位数
    'DC_CMD_EXECUTE': 1,  # DC命令执行标志

    # ADC解调相关常量
    'ADC_MUL_MAX_FREQUENCIES': 16,  # ADC解调最大频率数
    'ADC_MUL_MAX_LENGTH': 2**32,  # ADC解调最大长度
    'ADC_MUL_MAX_TIMES': 163840,  # ADC解调最大次数
    'ADC_MUL_MAX_MODULE_NUM': 16,  # ADC解调最大模块数
    'ADC_MUL_BASE_ADDR': 0x6000,  # ADC解调基地址
    'ADC_MUL_CHANNEL_OFFSET': 0x400,  # ADC解调通道偏移
    'ADC_MUL_DMA_BASE_ADDR': 0x500000000,  # ADC解调DMA基地址
    'ADC_MUL_DMA_CHANNEL_OFFSET': 0x8000000,  # ADC解调DMA通道偏移
    'ADC_MUL_DMA_MODULE_OFFSET': 0x400000,  # ADC解调DMA模块偏移
    'DDS_PHASE_AMP': 2**25,  # DDS相位幅度
    'ADC_FS': 2.5e9,  # ADC采样频率

    # ADC解调决策相关常量
    'ADC_DECISION_MAX_COUNT': 16,  # ADC决策最大数量
    'ADC_DECISION_BASE_OFFSET': 36,  # ADC决策基地址偏移
    'ADC_DECISION_REG_OFFSET': 4,  # ADC决策寄存器偏移
    'REVOLVE_VECTOR_SCALE': 2**17-1,  # 旋转向量缩放因子
    'DECISION_VALUE_SCALE': 2**43-1,  # 决策值缩放因子

    # RF DAC相关常量
    'RF_DAC_NYQUIST_CMD_REG': 1,  # RF DAC Nyquist命令寄存器
    'RF_DAC_SAMPLING_CMD_REG': 8,  # RF DAC采样命令寄存器
    'RF_DAC_CMD_OFFSET': 2,  # RF DAC命令偏移
    'RF_DAC_STATUS_REG': 0x0,  # RF DAC状态寄存器
    'RF_DAC_SAMPLING_STATUS_REG': 11,  # RF DAC采样状态寄存器
    'RF_DAC_SAMPLING_MODULO': 200,  # RF DAC采样模数

    # 每块板卡的通道数
    'DA_CHANNELS_PER_BOARD': 12,  # 每块板卡的DA通道数
    'AD_CHANNELS_PER_BOARD': 6,   # 每块板卡的AD通道数

    # 通道控制常量
    'DEFAULT_SLOT': 'slot0',  # 默认槽位
    'DC_OFFSET_SLOT': 'slot1',  # DC偏移专用槽位
    'DEFAULT_CHANNEL': 0,  # 默认通道号
    'SUCCESS_CODE': 0,  # 成功状态码
    'ERROR_INVALID_CHANNEL': -1,  # 无效通道错误码
    'ERROR_OPERATION_FAILED': -2,  # 操作失败错误码

    # 数据类型常量
    'DATA_TYPE_UINT32': 'uint32',  # 32位无符号整数类型
    'DATA_TYPE_INT16': 'int16',  # 16位有符号整数类型
    'DATA_TYPE_INT32': 'int32',  # 32位有符号整数类型
}
