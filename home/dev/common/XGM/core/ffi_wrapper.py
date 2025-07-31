# -*- coding: utf-8 -*-
"""
FFI包装器模块

统一管理所有DLL函数调用，提供类型安全的接口。
"""

import ctypes
import logging
import numpy as np

logger = logging.getLogger(__name__)


class FFIWrapper:
    """FFI函数包装器

    统一管理所有DLL函数调用，确保类型安全和一致性。
    """

    def __init__(self, fpga_dll):
        """初始化FFI包装器

        Args:
            fpga_dll: FPGA DLL对象
        """
        self.fpga_dll = fpga_dll
        self._setup_function_signatures()

    def _setup_function_signatures(self):
        """设置所有DLL函数的签名"""
        self._setup_dma_functions()
        self._setup_register_functions()
        self._setup_board_functions()

    def _setup_dma_functions(self):
        """设置DMA相关函数的签名"""
        # sys_dma_read: int sys_dma_read(int bus_id, long long int address, int size)
        self.fpga_dll.sys_dma_read.argtypes = [
            ctypes.c_int, ctypes.c_longlong, ctypes.c_int
        ]
        self.fpga_dll.sys_dma_read.restype = ctypes.c_int

        # sys_dma_write: int sys_dma_write(int bus_id, long long int address, int *data, int size)
        self.fpga_dll.sys_dma_write.argtypes = [
            ctypes.c_int, ctypes.c_longlong, ctypes.POINTER(
                ctypes.c_int), ctypes.c_int
        ]
        self.fpga_dll.sys_dma_write.restype = ctypes.c_int

        # dma_return_data: int dma_return_data(struct Data * data,int bus_id, long long int address, int size)
        # 注意：这里使用ctypes.c_void_p作为结构体指针，实际调用时会传递具体的结构体引用
        self.fpga_dll.dma_return_data.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_longlong, ctypes.c_int
        ]
        self.fpga_dll.dma_return_data.restype = ctypes.c_int

        # dma_return_data_by_size: int dma_return_data_by_size(unsigned char* data, int bus_id, long long int address, unsigned int size, unsigned int rd_len)
        self.fpga_dll.dma_return_data_by_size.argtypes = [
            ctypes.POINTER(
                ctypes.c_ubyte), ctypes.c_int, ctypes.c_longlong, ctypes.c_uint, ctypes.c_uint
        ]
        self.fpga_dll.dma_return_data_by_size.restype = ctypes.c_int

    def _setup_register_functions(self):
        """设置寄存器操作函数的签名"""
        # sys_read32: void sys_read32(int bar, long long int addr, unsigned int *data, int bus_id)
        self.fpga_dll.sys_read32.argtypes = [
            ctypes.c_int, ctypes.c_longlong, ctypes.POINTER(
                ctypes.c_uint), ctypes.c_int
        ]
        self.fpga_dll.sys_read32.restype = None

        # sys_write32: void sys_write32(int bar, long long int addr, unsigned int data, int bus_id)
        self.fpga_dll.sys_write32.argtypes = [
            ctypes.c_int, ctypes.c_longlong, ctypes.c_uint, ctypes.c_int
        ]
        self.fpga_dll.sys_write32.restype = None

    def _setup_board_functions(self):
        """设置板卡管理函数的签名"""
        # sys_init: int sys_init()
        self.fpga_dll.sys_init.argtypes = []
        self.fpga_dll.sys_init.restype = ctypes.c_int

        # ALL_Sys_Init: int ALL_Sys_Init(struct Init *Init_Struct)
        self.fpga_dll.ALL_Sys_Init.argtypes = [ctypes.c_void_p]
        self.fpga_dll.ALL_Sys_Init.restype = ctypes.c_int

        # sys_open: int sys_open(int DeviceId)
        self.fpga_dll.sys_open.argtypes = [ctypes.c_int]
        self.fpga_dll.sys_open.restype = ctypes.c_int

        # sys_close: int sys_close(int DeviceId)
        self.fpga_dll.sys_close.argtypes = [ctypes.c_int]
        self.fpga_dll.sys_close.restype = ctypes.c_int

        # VENDOR_ID: char *VENDOR_ID(int openDeviceId)
        self.fpga_dll.VENDOR_ID.argtypes = [ctypes.c_int]
        self.fpga_dll.VENDOR_ID.restype = ctypes.c_char_p

        # DEVICE_ID: char *DEVICE_ID(int openDeviceId)
        self.fpga_dll.DEVICE_ID.argtypes = [ctypes.c_int]
        self.fpga_dll.DEVICE_ID.restype = ctypes.c_char_p

    # DMA操作接口
    def dma_read(self, bus_id: int, address: int, size: int) -> int:
        """DMA读取

        Args:
            bus_id: 板卡ID
            address: 源地址
            size: 读取大小

        Returns:
            操作结果
        """
        return self.fpga_dll.sys_dma_read(bus_id, address, size)

    def dma_write(self, bus_id: int, address: int, data: np.ndarray, size: int) -> int:
        """DMA写入

        Args:
            bus_id: 板卡ID
            address: 目标地址
            data: 数据数组
            size: 数据大小

        Returns:
            操作结果
        """
        # 确保数据是int32类型
        if data.dtype != np.int32:
            data = data.astype(np.int32)

        return self.fpga_dll.sys_dma_write(
            bus_id, address, data.ctypes.data_as(
                ctypes.POINTER(ctypes.c_int)), size
        )

    def dma_return_data(self, data_struct, bus_id: int, address: int, size: int) -> int:
        """DMA返回数据

        Args:
            data_struct: 数据结构体
            bus_id: 板卡ID
            address: 地址
            size: 大小

        Returns:
            操作结果
        """
        return self.fpga_dll.dma_return_data(data_struct, bus_id, address, size)

    def dma_return_data_by_size(self, data_buffer, bus_id: int, address: int, size: int, rd_len: int) -> int:
        """按大小DMA返回数据

        Args:
            data_buffer: 数据缓冲区
            bus_id: 板卡ID
            address: 地址
            size: 大小
            rd_len: 读取长度

        Returns:
            操作结果
        """
        return self.fpga_dll.dma_return_data_by_size(data_buffer, bus_id, address, size, rd_len)

    # 寄存器操作接口
    def read_register(self, bar: int, addr: int, data_ref, bus_id: int) -> None:
        """读取寄存器

        Args:
            bar: BAR寄存器
            addr: 寄存器地址
            data_ref: 数据引用
            bus_id: 板卡ID
        """
        self.fpga_dll.sys_read32(bar, addr, data_ref, bus_id)

    def write_register(self, bar: int, addr: int, data: int, bus_id: int) -> None:
        """写入寄存器

        Args:
            bar: BAR寄存器
            addr: 寄存器地址
            data: 要写入的数据
            bus_id: 板卡ID
        """
        self.fpga_dll.sys_write32(bar, addr, data, bus_id)

    # 板卡管理接口
    def sys_init(self) -> int:
        """系统初始化

        Returns:
            操作结果
        """
        return self.fpga_dll.sys_init()

    def system_init(self, struct_info_ref) -> int:
        """系统初始化（带结构体）

        Args:
            struct_info_ref: 结构体信息引用

        Returns:
            操作结果
        """
        return self.fpga_dll.ALL_Sys_Init(struct_info_ref)

    def open_board(self, board_id: int) -> int:
        """打开板卡

        Args:
            board_id: 板卡ID

        Returns:
            操作结果
        """
        return self.fpga_dll.sys_open(board_id)

    def close_board(self, board_id: int) -> int:
        """关闭板卡

        Args:
            board_id: 板卡ID

        Returns:
            操作结果
        """
        return self.fpga_dll.sys_close(board_id)

    def get_vendor_id(self, open_device_id: int) -> str:
        """获取厂商ID

        Args:
            open_device_id: 已打开的设备ID

        Returns:
            厂商ID字符串
        """
        result = self.fpga_dll.VENDOR_ID(open_device_id)
        return result.decode('utf-8') if result else ""

    def get_device_id(self, open_device_id: int) -> str:
        """获取设备ID

        Args:
            open_device_id: 已打开的设备ID

        Returns:
            设备ID字符串
        """
        result = self.fpga_dll.DEVICE_ID(open_device_id)
        return result.decode('utf-8') if result else ""
