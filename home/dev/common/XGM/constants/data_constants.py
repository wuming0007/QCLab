# -*- coding: utf-8 -*-
"""
数据相关常量定义
"""

# 数据限制常量
DATA_LIMITS = {
    'MAX_DAC_DATA_LENGTH': 16384 * 32,  # 最大DAC数据长度
    'MAX_ADC_SAVE_LENGTH': 131072,  # 最大ADC保存长度 (52.4288us)
    'MAX_MUL_TIMES': 163840,  # 最大乘法次数
    'MAX_MUL_LENGTH': 16384,  # 最大乘法长度
    'DAC_SCALE_FACTOR': 2**13 - 1,  # DAC缩放因子
    'DDS_PHASE_AMP': 2**25,  # DDS相位幅度
    'ADC_FS': 2.5e9,  # ADC采样频率
    'DECISION_SCALE_FACTOR': 2**17 - 1,  # 判决缩放因子
    'DECISION_VALUE_SCALE': 2**43 - 1,  # 判决值缩放因子
}
