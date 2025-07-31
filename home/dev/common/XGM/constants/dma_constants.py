# -*- coding: utf-8 -*-
"""
DMA相关常量定义
"""

# DMA相关常量
DMA_CONSTANTS = {
    'DEFAULT_DATA_SIZE': 8192,  # 默认DMA数据大小
    'MAX_DATA_SIZE': 1024 * 1024,  # 最大DMA数据大小 (1MB)
    'DEFAULT_PCIE_DMA_RD_LEN': 512 * 1024,  # 默认PCIe DMA读取长度 (与原版一致)
    'DEFAULT_DMA_WRITE_SIZE': 4096,  # 默认DMA写入大小
    'DEFAULT_PCIE_DMA_WR_LEN': 2048 * 16,  # 默认PCIe DMA写入长度
    'DEFAULT_PCIE_DMA_RD_LEN_64BIT': 2048 * 4,  # 64位数据默认读取长度
    'DEFAULT_PCIE_DMA_RD_LEN_8BIT': 2048 * 4,  # 8位数据默认读取长度

    # 数据类型常量
    'DATA_TYPE_INT32': 'int32',  # 32位整数数据类型
    'DATA_TYPE_INT16': 'int16',  # 16位整数数据类型
    'BYTES_PER_INT16': 2,  # 16位整数字节数
    'BYTES_PER_INT32': 4,  # 32位整数字节数

    # 错误码常量
    'SUCCESS_CODE': 0,  # 成功状态码
    'ERROR_INVALID_PARAM': -1,  # 无效参数错误码
    'ERROR_DMA_BUSY': -2,  # DMA忙错误码
    'ERROR_DMA_TIMEOUT': -3,  # DMA超时错误码
}

# 地址常量
ADDRESS_CONSTANTS = {
    'DMA_BASE_ADDR': 0xa0000000,  # DMA基础地址 (与原版一致)
    'DMA_FB_BASE_ADDR': 0xa2000000,  # DMA反馈基础地址
    'DMA_RD_BASE_ADDR': 0xa0000000,  # DMA读取基础地址
    'CHANNEL_OFFSET': 0x100000,  # 通道偏移
    'BLOCK_OFFSET': 0x10000,  # 块偏移
    'MUL_DATA_BASE_ADDR': 0x500000000,  # 乘法数据基础地址
    'MUL_DATA_CHANNEL_OFFSET': 0x8000000,  # 乘法数据通道偏移
    'MUL_DATA_MODULE_OFFSET': 0x400000,  # 乘法数据模块偏移
}
