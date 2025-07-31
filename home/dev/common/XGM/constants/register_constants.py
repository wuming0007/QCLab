# -*- coding: utf-8 -*-
"""
寄存器相关常量定义
"""

# 固件版本寄存器
FIRMWARE_REGISTERS = {
    'PL_VERSION_MAJOR': 0x100,  # PL固件主版本号
    'PL_VERSION_MINOR': 0x101,  # PL固件次版本号
    'PS_VERSION_MAJOR': 0x102,  # PS固件主版本号
    'PS_VERSION_MINOR': 0x103   # PS固件次版本号
}

# 寄存器地址常量
REGISTER_CONSTANTS = {
    # 串口相关寄存器
    'SERIAL_DATA_REG': 0x400,  # 串口数据寄存器
    'SERIAL_CTRL_REG': 0x401,  # 串口控制寄存器
    'SERIAL_STATUS_REG': 0x402,  # 串口状态寄存器

    # DAC相关寄存器
    'DAC_CTRL_BASE': 0x8000,  # DAC控制基础地址
    'DAC_CHANNEL_OFFSET': 0x400,  # DAC通道偏移
    'DAC_ENABLE_REG': 1,  # DAC使能寄存器偏移
    'DAC_REPLAY_LEN_REG': 2,  # DAC重放长度寄存器偏移
    'DAC_TRIGGER_DELAY_REG': 3,  # DAC触发延时寄存器偏移
    'DAC_REPLAY_TIMES_REG': 4,  # DAC重放次数寄存器偏移
    'DAC_OFFSET_REG': 5,  # DAC偏移寄存器偏移

    # ADC相关寄存器
    'ADC_CTRL_BASE': 0x4000,  # ADC控制基础地址
    'ADC_CHANNEL_OFFSET': 0x400,  # ADC通道偏移
    'ADC_ENABLE_REG': 0,  # ADC使能寄存器偏移
    'ADC_TRIGGER_DELAY_REG': 1,  # ADC触发延时寄存器偏移
    'ADC_SAVE_LEN_REG': 2,  # ADC保存长度寄存器偏移
    'ADC_TIMES_REG': 3,  # ADC次数寄存器偏移

    # 乘法解调相关寄存器
    'MUL_CTRL_BASE': 0x6000,  # 乘法控制基础地址
    'MUL_CHANNEL_OFFSET': 0x400,  # 乘法通道偏移
    'MUL_ENABLE_REG': 0,  # 乘法使能寄存器偏移
    'MUL_TRIGGER_DELAY_REG': 1,  # 乘法触发延时寄存器偏移
    'MUL_TIMES_REG': 2,  # 乘法次数寄存器偏移
    'MUL_LEN_REG': 3,  # 乘法长度寄存器偏移
    'MUL_PHASE_BASE': 4,  # 乘法相位基础寄存器偏移
    'MUL_DECISION_BASE': 36,  # 乘法判决基础寄存器偏移

    # RF DAC相关寄存器
    'RF_CMD_REG': 0,  # RF命令寄存器
    'RF_DATA_REG': 2,  # RF数据寄存器
    'RF_NYQUIST_REG': 2,  # RF奈奎斯特区域寄存器
    'RF_SAMPLING_REG': 8,  # RF采样率寄存器
    'RF_SAMPLING_STATUS_REG': 11,  # RF采样率状态寄存器

    # 风扇控制寄存器
    'FAN_SPEED_REG': 0,  # 风扇速度寄存器

    # ADC系数寄存器
    'ADC_COEF_CMD_REG': 16,  # ADC系数命令寄存器
    'ADC_COEF_DATA_REG': 32,  # ADC系数数据寄存器

    # DC偏移寄存器
    'DC_OFFSET_CMD_REG': 17,  # DC偏移命令寄存器
    'DC_OFFSET_DATA_BASE': 32,  # DC偏移数据基础地址

    # 通用寄存器
    'CMD_OFFSET': 2,  # 命令寄存器偏移
    'STATUS_REG': 0x0,  # 状态寄存器地址
}
