# -*- coding: utf-8 -*-
"""
寄存器操作模块 - FPGA寄存器读写功能，使用FFI包装器
"""

import ctypes
import logging
from utils import RegisterAccessError, ValidationError, ValidationUtils

logger = logging.getLogger(__name__)


class RegisterOperations:
    """寄存器操作类 - 使用FFI包装器"""

    def __init__(self, board_mgmt):
        """初始化寄存器操作

        Args:
            board_mgmt: 板卡管理对象
        """
        self.board_mgmt = board_mgmt
        self.register_value_buffer = ctypes.c_uint(0)  # 寄存器值读取缓冲区

    def read_reg(self, addr: int, slot: str) -> int:
        """读取指定地址和槽位的寄存器值

        Args:
            addr: 寄存器地址
            slot: 板卡槽位

        Returns:
            寄存器值

        Raises:
            ValidationError: 参数验证失败
            RegisterAccessError: 寄存器访问失败
        """
        # 参数验证
        if not ValidationUtils.validate_register_address(addr):
            raise ValidationError(f"无效的寄存器地址: 0x{addr:X}")

        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 查找板卡ID
            board_id = self.board_mgmt.find_board_id_by_slot(slot)
            if board_id is None:
                raise RegisterAccessError(addr, slot, f"未找到槽位 {slot} 对应的板卡")

            # 读取寄存器
            # 注意：addr * 4 是硬件地址映射，将软件寄存器地址转换为硬件物理地址
            # 硬件寄存器是32位（4字节）宽度，需要4字节对齐
            # 例如：寄存器地址0x100 -> 硬件地址0x400 (0x100 * 4)
            self.board_mgmt.ffi.read_register(
                0, addr * 4, ctypes.byref(self.register_value_buffer), board_id)

            value = self.register_value_buffer.value
            logger.debug(f"读取寄存器 0x{addr:X} (槽位: {slot}) = 0x{value:X}")
            return value

        except Exception as e:
            if isinstance(e, (ValidationError, RegisterAccessError)):
                raise
            logger.error(f"读取寄存器 0x{addr:X} (槽位: {slot}) 失败: {e}")
            raise RegisterAccessError(addr, slot, f"读取寄存器异常: {e}")

    def write_reg(self, addr: int, data: int, slot: str = '') -> int:
        """写入指定地址和槽位的寄存器值

        Args:
            addr: 寄存器地址
            data: 要写入的数据
            slot: 板卡槽位，为空时使用第一个板卡

        Returns:
            操作结果

        Raises:
            ValidationError: 参数验证失败
            RegisterAccessError: 寄存器访问失败
        """
        # 参数验证
        if not ValidationUtils.validate_register_address(addr):
            raise ValidationError(f"无效的寄存器地址: 0x{addr:X}")

        if slot and not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 确定板卡ID
            if slot:
                board_id = self.board_mgmt.find_board_id_by_slot(slot)
                if board_id is None:
                    raise RegisterAccessError(
                        addr, slot, f"未找到槽位 {slot} 对应的板卡")
            else:
                # 使用第一个板卡
                board_id = 0

            # 写入寄存器
            # 注意：addr * 4 是硬件地址映射，将软件寄存器地址转换为硬件物理地址
            # 硬件寄存器是32位（4字节）宽度，需要4字节对齐
            # 例如：寄存器地址0x100 -> 硬件地址0x400 (0x100 * 4)
            self.board_mgmt.ffi.write_register(
                0, addr * 4, int(data), board_id)
            result = 0  # FFI包装器不返回错误码

            if result != 0:
                raise RegisterAccessError(
                    addr, slot or 'default', f"写入寄存器失败，错误码: {result}")

            logger.debug(
                f"写入寄存器 0x{addr:X} = 0x{data:X} (槽位: {slot or 'default'})")
            return result

        except Exception as e:
            if isinstance(e, (ValidationError, RegisterAccessError)):
                raise
            logger.error(f"写入寄存器 0x{addr:X} (槽位: {slot or 'default'}) 失败: {e}")
            raise RegisterAccessError(addr, slot or 'default', f"写入寄存器异常: {e}")
