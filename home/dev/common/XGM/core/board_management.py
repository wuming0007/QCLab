# -*- coding: utf-8 -*-
"""
板卡管理模块 - FPGA板卡初始化、配置和管理功能
优化版本 - 基于真实硬件环境测试，使用FFI包装器
"""

import ctypes
import logging
from typing import Dict, List, Optional
from utils import BoardNotFoundError, ValidationError, ValidationUtils

logger = logging.getLogger(__name__)


class BoardManagement:
    """板卡管理类 - 使用FFI包装器优化版本"""

    def __init__(self, ffi_wrapper):
        """初始化板卡管理

        Args:
            ffi_wrapper: FFI包装器实例
        """
        self.ffi = ffi_wrapper
        self.board_info = {}
        self.struct_info = None
        self._initialized = False

    def initialize_boards(self) -> bool:
        """初始化所有板卡

        Returns:
            初始化是否成功
        """
        try:
            if self._initialized:
                logger.warning("板卡已经初始化，跳过重复初始化")
                return True

            # 创建板卡信息结构体
            self.struct_info = self._create_board_info_struct()

            # 使用FFI包装器调用设备初始化函数
            logger.info("开始调用底层ALL_Sys_Init进行硬件检测...")
            init_result = self.ffi.system_init(ctypes.byref(self.struct_info))

            # 检查初始化结果
            if init_result == -1:
                logger.warning("FPGA设备初始化返回-1，可能已经初始化，继续处理...")
            elif init_result == 0:
                logger.info("FPGA设备初始化成功")
            else:
                logger.error(f"FPGA设备初始化失败，错误码: {init_result}")
                return False

            # 解析板卡信息
            self._parse_board_info()

            # 验证板卡信息
            if not self._validate_board_info():
                logger.warning("板卡信息验证失败，但继续初始化流程")

            self._initialized = True
            logger.info(f"板卡初始化完成，检测到 {self.get_board_number()} 块板卡")
            return True

        except Exception as e:
            logger.error(f"板卡初始化失败: {e}")
            self._initialized = False
            return False

    def open_all_boards(self) -> bool:
        """打开所有有效板卡

        Returns:
            操作是否成功
        """
        try:
            if not self._initialized:
                logger.error("板卡管理未初始化，无法打开板卡")
                return False

            success_count = 0
            total_boards = len(self.board_info)

            logger.info(f"开始打开 {total_boards} 块板卡...")

            for board_id, board_data in self.board_info.items():
                if not board_data.get('is_valid', False):
                    logger.debug(f"跳过无效板卡: {board_id}")
                    continue

                slot = board_data['slot']
                if self.open_board(slot):
                    success_count += 1
                    logger.debug(f"板卡打开成功: {slot}")
                else:
                    logger.warning(f"板卡打开失败: {slot}")

            logger.info(f"板卡打开完成: {success_count}/{total_boards} 块板卡成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"打开所有板卡失败: {e}")
            return False

    def get_board_info(self) -> Dict:
        """获取板卡信息

        Returns:
            板卡信息字典
        """
        return self.board_info.copy()

    def get_board_number(self) -> int:
        """获取板卡数量

        Returns:
            板卡数量
        """
        if self.struct_info:
            return self.struct_info.BoardNum
        return 0

    def get_board_slots(self) -> List[int]:
        """获取板卡槽位列表

        Returns:
            板卡槽位列表
        """
        if self.struct_info:
            return list(self.struct_info.BoardSlot[:self.get_board_number()])
        return []

    def get_board_types(self) -> List[int]:
        """获取板卡类型列表

        Returns:
            板卡类型列表
        """
        if self.struct_info:
            return list(self.struct_info.BoardType[:self.get_board_number()])
        return []

    def get_valid_boards(self) -> List[Dict]:
        """获取有效的板卡列表（类型不为0x00的板卡）

        Returns:
            有效板卡信息列表
        """
        valid_boards = []
        board_num = self.get_board_number()

        for i in range(board_num):
            board_type = self.struct_info.BoardType[i]
            if board_type != 0x00:  # 过滤掉类型为0x00的板卡
                board_info = {
                    'board_id': i,
                    'slot': f"slot{self.struct_info.BoardSlot[i]}",
                    'type': f'0x{board_type:02X}',
                    'slot_num': self.struct_info.BoardSlot[i]
                }
                valid_boards.append(board_info)

        return valid_boards

    def open_board(self, slot: str) -> bool:
        """打开指定槽位的板卡

        Args:
            slot: 板卡槽位

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 查找板卡ID
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 检查板卡类型是否有效
            if self.struct_info.BoardType[board_id] == 0x00:
                logger.warning(f"板卡 {slot} 类型为0x00，可能未正确初始化")

            # 使用FFI包装器打开板卡
            logger.info(f"正在打开板卡 {slot} (ID: {board_id})...")
            result = self.ffi.open_board(board_id)

            if result != 0:
                logger.error(f"打开板卡 {slot} 失败，错误码: {result}")
                return False

            # 更新板卡状态
            if str(board_id) in self.board_info:
                self.board_info[str(board_id)]['is_open'] = True

            logger.info(f"板卡 {slot} 打开成功")
            return True

        except Exception as e:
            logger.error(f"打开板卡 {slot} 失败: {e}")
            return False

    def close_board(self, slot: str) -> bool:
        """关闭指定槽位的板卡

        Args:
            slot: 板卡槽位

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 查找板卡ID
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 使用FFI包装器关闭板卡
            logger.info(f"正在关闭板卡 {slot} (ID: {board_id})...")
            result = self.ffi.close_board(board_id)

            if result != 0:
                logger.error(f"关闭板卡 {slot} 失败，错误码: {result}")
                return False

            # 更新板卡状态
            if str(board_id) in self.board_info:
                self.board_info[str(board_id)]['is_open'] = False

            logger.info(f"板卡 {slot} 关闭成功")
            return True

        except Exception as e:
            logger.error(f"关闭板卡 {slot} 失败: {e}")
            return False

    def get_board_status(self, slot: str) -> Optional[Dict]:
        """获取板卡状态

        Args:
            slot: 板卡槽位

        Returns:
            板卡状态信息，失败时返回None
        """
        # 参数验证
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 查找板卡ID
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 获取板卡信息
            board_info = self.board_info.get(str(board_id), {})
            board_type = self.struct_info.BoardType[board_id]

            status = {
                'slot': slot,
                'board_id': board_id,
                'board_type': f'0x{board_type:02X}',
                'is_valid': board_type != 0x00,
                'is_open': board_info.get('is_open', False),
                'channels': board_info.get('channels', {}),
                'firmware_version': board_info.get('firmware_version', 'Unknown')
            }

            return status

        except Exception as e:
            logger.error(f"获取板卡 {slot} 状态失败: {e}")
            return None

    def get_all_board_status(self) -> List[Dict]:
        """获取所有板卡状态

        Returns:
            所有板卡状态列表
        """
        status_list = []
        board_num = self.get_board_number()

        for i in range(board_num):
            slot = f"slot{self.struct_info.BoardSlot[i]}"
            status = self.get_board_status(slot)
            if status:
                status_list.append(status)

        return status_list

    def configure_board(self, slot: str, config: Dict) -> bool:
        """配置板卡

        Args:
            slot: 板卡槽位
            config: 配置参数

        Returns:
            配置是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 查找板卡ID
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 检查板卡是否有效
            if self.struct_info.BoardType[board_id] == 0x00:
                logger.warning(f"板卡 {slot} 类型为0x00，配置可能无效")

            # 应用配置
            success = self._apply_board_config(board_id, config)

            if success:
                logger.info(f"板卡 {slot} 配置成功")
            else:
                logger.error(f"板卡 {slot} 配置失败")

            return success

        except Exception as e:
            logger.error(f"配置板卡 {slot} 失败: {e}")
            return False

    def reset_boards(self) -> bool:
        """重置所有板卡状态

        Returns:
            重置是否成功
        """
        try:
            logger.info("开始重置板卡状态...")

            # 关闭所有打开的板卡
            board_num = self.get_board_number()
            for i in range(board_num):
                slot = f"slot{self.struct_info.BoardSlot[i]}"
                if self.board_info.get(str(i), {}).get('is_open', False):
                    self.close_board(slot)

            # 重置初始化状态
            self._initialized = False
            self.board_info = {}

            logger.info("板卡状态重置完成")
            return True

        except Exception as e:
            logger.error(f"重置板卡状态失败: {e}")
            return False

    def get_vendor_id(self, slot: str) -> Optional[str]:
        """获取板卡厂商ID

        Args:
            slot: 板卡槽位

        Returns:
            厂商ID字符串，失败时返回None
        """
        try:
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 使用FFI包装器获取厂商ID
            return self.ffi.get_vendor_id(board_id)

        except Exception as e:
            logger.error(f"获取板卡 {slot} 厂商ID失败: {e}")
            return None

    def get_device_id(self, slot: str) -> Optional[str]:
        """获取板卡设备ID

        Args:
            slot: 板卡槽位

        Returns:
            设备ID字符串，失败时返回None
        """
        try:
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 使用FFI包装器获取设备ID
            return self.ffi.get_device_id(board_id)

        except Exception as e:
            logger.error(f"获取板卡 {slot} 设备ID失败: {e}")
            return None

    def return_data_by_size(self, dma_addr: int, size: int, pcie_dma_rd_len: int, slot: str) -> tuple:
        """按大小返回DMA数据

        Args:
            dma_addr: DMA地址
            size: 数据大小
            pcie_dma_rd_len: PCIe DMA读取长度
            slot: 板卡槽位

        Returns:
            (数据缓冲区, 状态码) 元组
        """
        try:
            # 查找板卡ID
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 创建数据缓冲区
            data_buffer = (ctypes.c_ubyte * size)()

            # 使用FFI包装器执行DMA读取
            state = self.ffi.dma_return_data_by_size(
                data_buffer, board_id, dma_addr, size, pcie_dma_rd_len)

            logger.debug(
                f"DMA数据读取完成 (槽位: {slot}, 地址: 0x{dma_addr:X}, 大小: {size})")
            return data_buffer, state

        except Exception as e:
            logger.error(f"DMA数据读取失败 (槽位: {slot}, 地址: 0x{dma_addr:X}): {e}")
            return None, -1

    def return_data(self, addr: int, slot: str) -> Optional[ctypes.Array]:
        """返回DMA数据

        Args:
            addr: DMA地址
            slot: 板卡槽位

        Returns:
            DMA数据数组，失败时返回None
        """
        try:
            # 查找板卡ID
            board_id = self.find_board_id_by_slot(slot)
            if board_id is None:
                raise BoardNotFoundError(slot)

            # 使用已定义的DmaData结构体
            from structures import DmaData
            data_test = DmaData()

            # 使用FFI包装器执行DMA读取
            self.ffi.dma_return_data(
                ctypes.byref(data_test), board_id, ctypes.c_longlong(addr), 8192)

            logger.debug(f"DMA数据读取完成 (槽位: {slot}, 地址: 0x{addr:X})")
            return data_test.data

        except Exception as e:
            logger.error(f"DMA数据读取失败 (槽位: {slot}, 地址: 0x{addr:X}): {e}")
            return None

    def _create_board_info_struct(self):
        """创建板卡信息结构体"""
        class StructInfo(ctypes.Structure):
            """板卡信息结构体"""
            _fields_ = [
                ("BoardNum", ctypes.c_int),
                ("BoardSlot", ctypes.c_int * 10),
                ("BoardType", ctypes.c_int * 10),
            ]
        return StructInfo()

    def _parse_board_info(self):
        """解析板卡信息"""
        # 检查板卡信息是否已初始化，如果未初始化，则返回
        if not self.struct_info:
            return

        board_num = self.struct_info.BoardNum
        logger.info(f"解析 {board_num} 块板卡信息...")

        for i in range(board_num):
            slot_num = self.struct_info.BoardSlot[i]
            board_type = self.struct_info.BoardType[i]

            # 检查板卡类型有效性
            is_valid = board_type != 0x00
            type_str = f'0x{board_type:02X}'

            if not is_valid:
                logger.warning(
                    f"板卡 {i} (槽位: slot{slot_num}) 类型为 {type_str}，可能未正确初始化")

            self.board_info[str(i)] = {
                'slot': f'slot{slot_num}',
                'type': type_str,
                'is_valid': is_valid,
                'is_open': False,
                'channels': {},
                'firmware_version': 'Unknown'
            }

        # 统计有效板卡
        valid_count = sum(
            1 for info in self.board_info.values() if info['is_valid'])
        logger.info(f"板卡解析完成: {valid_count}/{board_num} 块板卡有效")

    def _validate_board_info(self) -> bool:
        """验证板卡信息

        Returns:
            验证是否通过
        """
        if not self.struct_info:
            return False

        board_num = self.struct_info.BoardNum

        # 检查板卡数量合理性
        if board_num < 0 or board_num > 8:
            logger.error(f"板卡数量异常: {board_num}")
            return False

        # 检查槽位和类型的合理性
        for i in range(board_num):
            slot = self.struct_info.BoardSlot[i]
            board_type = self.struct_info.BoardType[i]

            # 检查槽位范围
            if slot < 0 or slot > 7:
                logger.error(f"板卡 {i} 槽位异常: {slot}")
                return False

            # 检查类型是否为0x00（可能表示未初始化）
            if board_type == 0x00:
                logger.warning(f"板卡 {i} 类型为0x00，可能未正确初始化")

        return True

    def find_board_id_by_slot(self, slot: str) -> Optional[int]:
        """根据槽位查找板卡ID

        Args:
            slot: 板卡槽位

        Returns:
            板卡ID，如果未找到返回None
        """
        try:
            slot_num = int(slot[4:])  # 假设格式为 "slotX"

            if self.struct_info:
                for i in range(self.struct_info.BoardNum):
                    if self.struct_info.BoardSlot[i] == slot_num:
                        return i

            return None

        except (ValueError, IndexError):
            logger.error(f"无效的槽位格式: {slot}")
            return None

    def _apply_board_config(self, board_id: int, config: Dict) -> bool:
        """应用板卡配置

        Args:
            board_id: 板卡ID
            config: 配置参数

        Returns:
            配置是否成功
        """
        try:
            # 更新板卡信息
            if str(board_id) in self.board_info:
                self.board_info[str(board_id)].update(config)
                return True
            return False

        except Exception as e:
            logger.error(f"应用板卡配置失败: {e}")
            return False

    def is_initialized(self) -> bool:
        """检查是否已初始化

        Returns:
            是否已初始化
        """
        return self._initialized
