# -*- coding: utf-8 -*-
"""
板卡信息结构体定义
"""

import ctypes


class StructInfo(ctypes.Structure):
    """板卡信息结构体"""
    _fields_ = [
        ('BoardNum', ctypes.c_int),  # 板卡数量
        ('BoardSlot', ctypes.c_int * 4),  # 板卡槽位信息
        ('BoardType', ctypes.c_int * 4),  # 板卡类型信息
    ] 