# -*- coding: utf-8 -*-
"""
DMA数据结构体定义
"""

import ctypes


class DmaData(ctypes.Structure):
    """DMA数据传输结构体 - 16位数据"""
    _fields_ = [
        ('data', ctypes.c_short * 4096),  # 16位数据数组
    ]


class DmaDataSum(ctypes.Structure):
    """DMA数据传输结构体 - 32位数据"""
    _fields_ = [
        ('data', ctypes.c_int * 2048),  # 32位数据数组
    ]
