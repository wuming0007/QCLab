# -*- coding: utf-8 -*-
"""
DMA操作模块 - FPGA DMA数据传输功能，使用FFI包装器
"""

import ctypes
import numpy as np
import logging
import time
from typing import Optional, Union, List, Dict
from utils import ValidationError, ValidationUtils
from constants import DMA_CONSTANTS, ADDRESS_CONSTANTS

logger = logging.getLogger(__name__)


class DmaOperations:
    """DMA操作类 - 使用FFI包装器"""

    def __init__(self, board_mgmt):
        """初始化DMA操作

        Args:
            board_mgmt: 板卡管理对象
        """
        self.board_mgmt = board_mgmt

    def dma_write(self, slot: str, addr: int, data: Union[List, np.ndarray], size: Optional[int] = None) -> int:
        """DMA写入数据（可指定自定义大小）

        Args:
            slot: 板卡槽位
            addr: 目标地址
            data: 要写入的数据
            size: 写入大小，None表示使用数据长度

        Returns:
            操作结果
        """
        # 参数验证
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dma_data(data):
            raise ValidationError("data", data, "数据必须是有效的列表或numpy数组")

        try:
            # 转换数据为numpy数组（使用int16类型，与原始实现保持一致）
            data = self._convert_to_numpy_array(data, dtype='int16')

            # 确定写入大小
            if size is None:
                size = len(data)
            elif size > len(data):
                raise ValidationError("size", size, "写入大小不能超过数据长度")

            # 查找板卡ID
            board_id = self._get_board_id(slot)

            # 使用FFI包装器
            result = self.board_mgmt.ffi.dma_write(board_id, addr, data, size)

            if result != DMA_CONSTANTS['SUCCESS_CODE']:
                logger.error(f"DMA写入失败，错误码: {result}")
                return result

            logger.debug(f"DMA写入成功: 槽位{slot}, 地址0x{addr:X}, 大小{size}")
            return result

        except Exception as e:
            logger.error(f"DMA写入失败: {e}")
            raise

    def dma_read(self, bus_id: int, addr: int, size: int) -> Optional[np.ndarray]:
        """DMA读取数据

        Args:
            bus_id: 总线ID
            addr: 源地址
            size: 读取大小

        Returns:
            读取的数据数组，失败时返回None
        """
        # 参数验证
        if not ValidationUtils.validate_dma_size(size):
            raise ValidationError("size", size, "读取大小必须大于0")

        try:
            # 创建数据缓冲区
            data_buffer = self._create_data_buffer(size)

            # 使用FFI包装器
            result = self.board_mgmt.ffi.dma_read(bus_id, addr, size)

            if result != DMA_CONSTANTS['SUCCESS_CODE']:
                logger.error(f"DMA读取失败，错误码: {result}")
                return None

            # 转换为numpy数组
            data = np.array(
                data_buffer, dtype=DMA_CONSTANTS['DATA_TYPE_INT32'])
            logger.debug(f"DMA读取成功: 总线{bus_id}, 地址0x{addr:X}, 大小{size}")
            return data

        except Exception as e:
            logger.error(f"DMA读取失败: {e}")
            return None

    def pcie_write_data(self, slot: str, channel_num: int, data: Union[List, np.ndarray]) -> int:
        """PCIe DMA写入数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            data: 要写入的数据数组

        Returns:
            int: 操作结果，0表示成功

        Raises:
            ValidationError: 当参数无效时
            RuntimeError: 当DMA写入失败时
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dma_data(data):
            raise ValidationError("数据必须是有效的列表或numpy数组")

        try:
            pcie_dma_wr_len = DMA_CONSTANTS['DEFAULT_PCIE_DMA_WR_LEN']

            # 计算需要的数据长度（向上取整到块大小的倍数）
            data_len = int(np.ceil(len(data) / pcie_dma_wr_len)
                           * pcie_dma_wr_len)

            # 创建数据缓冲区
            data_wr_bufe = np.zeros(data_len)
            data_wr_bufe[:len(data)] = data

            # 重塑数据为块格式
            data_wr_bufe = np.reshape(
                data_wr_bufe, (data_len // pcie_dma_wr_len, pcie_dma_wr_len))

            # 创建缓冲区
            pbuf = ctypes.create_string_buffer(
                pcie_dma_wr_len * DMA_CONSTANTS['BYTES_PER_INT16'])

            # 逐块写入数据
            for i in range(len(data_wr_bufe)):
                pbuf.raw = np.int16(data_wr_bufe[i])
                data_wr_bufe_i = ctypes.cast(ctypes.addressof(
                    pbuf), ctypes.POINTER(ctypes.c_short))

                # 计算目标地址
                # DMA地址计算：基地址 + 通道偏移 + 块偏移
                # 每个通道有独立的地址空间，每个数据块也有独立的偏移
                target_addr = (ADDRESS_CONSTANTS['DMA_BASE_ADDR'] +
                               ADDRESS_CONSTANTS['CHANNEL_OFFSET'] * channel_num +
                               ADDRESS_CONSTANTS['BLOCK_OFFSET'] * i)

                # 执行DMA写入，数据长度乘以2是因为数据是16位（2字节）
                data_block = np.int16(data_wr_bufe[i])
                self.dma_write(slot, target_addr, data_block,
                               pcie_dma_wr_len * DMA_CONSTANTS['BYTES_PER_INT16'])

            # 清理缓冲区
            pbuf = None

            logger.debug(
                f"PCIe DMA写入完成 (槽位: {slot}, 通道: {channel_num}, 数据长度: {len(data)})")
            return 0

        except Exception as e:
            logger.error(f"PCIe DMA写入失败 (槽位: {slot}, 通道: {channel_num}): {e}")
            raise RuntimeError(f"PCIe DMA写入失败: {e}")

    def pcie_read_data(self, slot: str, channel_num: int, data_len: int) -> Optional[np.ndarray]:
        """PCIe读取数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            data_len: 数据长度

        Returns:
            读取的数据数组，失败时返回None
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_channel_number(channel_num):
            raise ValidationError(
                "channel_num", channel_num, "通道号必须是非负整数且不超过硬件限制")

        if not ValidationUtils.validate_dma_size(data_len):
            raise ValidationError("data_len", data_len, "数据长度必须大于0")

        try:
            # 使用原版的DMA读取长度
            pcie_dma_rd_len = DMA_CONSTANTS['DEFAULT_PCIE_DMA_RD_LEN']

            # 计算基地址：0xa0000000 + 0x100000 * channel_num
            base_addr = ADDRESS_CONSTANTS['DMA_BASE_ADDR'] + \
                ADDRESS_CONSTANTS['CHANNEL_OFFSET'] * channel_num

            # 执行DMA读取
            data_test, state = self.board_mgmt.return_data_by_size(
                base_addr, pcie_dma_rd_len, pcie_dma_rd_len, slot)

            if data_test is None or state != 0:
                logger.error(f"PCIe读取失败，状态码: {state}")
                return None

            # 转换为正确的数据类型
            data_buf_i = ctypes.POINTER(ctypes.c_int)(data_test)

            # 返回指定长度的数据
            result_data = np.int32(data_buf_i[:data_len])

            logger.debug(
                f"PCIe读取成功 (槽位: {slot}, 通道: {channel_num}, 数据长度: {data_len})")
            return result_data

        except Exception as e:
            logger.error(f"PCIe读取失败 (槽位: {slot}, 通道: {channel_num}): {e}")
            return None

    def pcie_write_data_64bit(self, slot: str, channel_num: int, addr: int, data: Union[List, np.ndarray]) -> int:
        """PCIe写入64位数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            addr: 目标地址
            data: 要写入的64位数据

        Returns:
            操作结果，0表示成功
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dma_data(data):
            raise ValidationError("data", data, "数据必须是有效的列表或numpy数组")

        try:
            pcie_dma_wr_len = DMA_CONSTANTS['DEFAULT_PCIE_DMA_RD_LEN_64BIT']

            # 计算需要的数据长度（向上取整到块大小的倍数）
            data_len = int(
                np.ceil(len(data[0]) * 2 / pcie_dma_wr_len) * pcie_dma_wr_len)

            # 创建数据缓冲区
            data_wr_bufe = np.zeros(data_len)
            data_wr_bufe[:len(data[0]) * 2] = np.reshape(data,
                                                         (1, -1), order='F')

            # 重塑数据为块格式
            data_wr_bufe = np.reshape(
                data_wr_bufe, (data_len // pcie_dma_wr_len, pcie_dma_wr_len))

            # 创建缓冲区
            pbuf = ctypes.create_string_buffer(pcie_dma_wr_len * 8)

            # 逐块写入数据
            for i in range(len(data_wr_bufe)):
                pbuf.raw = np.int64(data_wr_bufe[i])
                data_wr_bufe_i = ctypes.cast(ctypes.addressof(
                    pbuf), ctypes.POINTER(ctypes.c_short))

                # 计算目标地址
                target_addr = addr + pcie_dma_wr_len * 4 * i

                # 执行DMA写入
                self.dma_write(slot, target_addr,
                               data_wr_bufe_i, pcie_dma_wr_len * 2)

            # 清理缓冲区
            pbuf = None

            logger.debug(
                f"PCIe 64位数据写入完成 (槽位: {slot}, 通道: {channel_num}, 地址: 0x{addr:X})")
            return 0

        except Exception as e:
            logger.error(
                f"PCIe 64位数据写入失败 (槽位: {slot}, 通道: {channel_num}): {e}")
            raise RuntimeError(f"PCIe 64位数据写入失败: {e}")

    def pcie_read_data_64bit(self, slot: str, channel_num: int, addr: int, data_len: int) -> Optional[List]:
        """PCIe读取64位数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            addr: 源地址
            data_len: 数据长度

        Returns:
            读取的64位数据列表，失败时返回None
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dma_size(data_len):
            raise ValidationError("data_len", data_len, "数据长度必须大于0")

        try:
            pcie_dma_rd_len = DMA_CONSTANTS['DEFAULT_PCIE_DMA_RD_LEN_64BIT']

            # 计算需要的数据长度（向上取整到块大小的倍数）
            data_len_rd = int(
                np.ceil((data_len * 8) / pcie_dma_rd_len) * pcie_dma_rd_len)

            # 创建数据缓冲区
            data_buf_i = []

            # 执行DMA读取
            data_test, state = self.board_mgmt.return_data_by_size(
                addr, data_len_rd * 2, pcie_dma_rd_len * 2, slot)
            data_buf_i = ctypes.POINTER(ctypes.c_longlong)(data_test)

            # 处理读取的数据
            data_buf_o = []
            data_buf_o.append(np.int64(data_buf_i[:data_len * 2:2]))
            data_buf_o.append(np.int64(data_buf_i[1:data_len * 2:2]))

            logger.debug(
                f"PCIe 64位数据读取完成 (槽位: {slot}, 通道: {channel_num}, 地址: 0x{addr:X})")
            return data_buf_o

        except Exception as e:
            logger.error(
                f"PCIe 64位数据读取失败 (槽位: {slot}, 通道: {channel_num}): {e}")
            return None

    def pcie_read_data_8bit(self, slot: str, channel_num: int, addr: int, data_len: int) -> Optional[np.ndarray]:
        """PCIe读取8位数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            addr: 源地址
            data_len: 数据长度

        Returns:
            读取的8位数据数组，失败时返回None
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dma_size(data_len):
            raise ValidationError("data_len", data_len, "数据长度必须大于0")

        try:
            pcie_dma_rd_len = DMA_CONSTANTS['DEFAULT_PCIE_DMA_RD_LEN_8BIT']

            # 计算需要的数据长度（向上取整到块大小的倍数）
            data_len_rd = int(
                np.ceil(data_len / pcie_dma_rd_len) * pcie_dma_rd_len)

            # 创建数据缓冲区
            data_buf_i = []

            # 执行DMA读取
            data_test, state = self.board_mgmt.return_data_by_size(
                addr, data_len_rd, pcie_dma_rd_len, slot)
            data_buf_i = ctypes.POINTER(ctypes.c_int8)(data_test)

            # 处理读取的数据
            data_buf_o = np.int8(data_buf_i[:data_len])

            logger.debug(
                f"PCIe 8位数据读取完成 (槽位: {slot}, 通道: {channel_num}, 地址: 0x{addr:X})")
            return data_buf_o

        except Exception as e:
            logger.error(f"PCIe 8位数据读取失败 (槽位: {slot}, 通道: {channel_num}): {e}")
            return None

    def wait_for_dma_ready(self, slot: str, timeout: float = 5.0) -> bool:
        """等待DMA就绪

        Args:
            slot: 板卡槽位
            timeout: 超时时间（秒）

        Returns:
            是否就绪
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_timeout(timeout):
            raise ValidationError("timeout", timeout, "超时时间必须在1-3600秒之间")

        try:
            import time
            start_time = time.time()

            while time.time() - start_time < timeout:
                status = self.get_dma_status(slot)
                if status and status.get('dma_status', {}).get('ready', False):
                    logger.debug(f"DMA就绪 (槽位: {slot})")
                    return True
                time.sleep(0.01)  # 10ms间隔

            logger.warning(f"DMA等待超时 (槽位: {slot}, 超时: {timeout}秒)")
            return False

        except Exception as e:
            logger.error(f"DMA等待失败 (槽位: {slot}): {e}")
            return False

    def _get_board_id(self, slot: str) -> int:
        """获取板卡ID

        Args:
            slot: 板卡槽位

        Returns:
            板卡ID

        Raises:
            ValidationError: 当未找到板卡时
        """
        board_id = self.board_mgmt.find_board_id_by_slot(slot)
        if board_id is None:
            raise ValidationError(f"未找到槽位 {slot} 对应的板卡")
        return board_id

    def _convert_to_numpy_array(self, data: Union[List, np.ndarray], dtype: str = None) -> np.ndarray:
        """转换数据为numpy数组

        Args:
            data: 输入数据
            dtype: 数据类型，None表示使用默认类型

        Returns:
            numpy数组
        """
        if isinstance(data, list):
            data = np.array(data)

        if dtype is None:
            dtype = DMA_CONSTANTS['DATA_TYPE_INT32']

        return data.astype(dtype)

    def _create_data_buffer(self, size: int, data_type: str = 'int32') -> ctypes.Array:
        """创建数据缓冲区

        Args:
            size: 缓冲区大小
            data_type: 数据类型

        Returns:
            ctypes数组
        """
        if data_type == 'int32':
            return (ctypes.c_int32 * size)()
        elif data_type == 'int16':
            return (ctypes.c_int16 * size)()
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")

    def get_dma_status(self, slot: str) -> Optional[Dict]:
        """获取DMA传输状态

        Args:
            slot: 板卡槽位

        Returns:
            DMA传输状态信息，失败时返回None
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 查找板卡ID
            board_id = self._get_board_id(slot)

            # 检查DMA传输状态
            dma_status = {
                'ready': True,  # DMA控制器就绪
                'busy': False,  # DMA传输忙
                'error': False,  # DMA传输错误
                'description': 'DMA传输状态'
            }

            # 这里可以添加具体的DMA状态寄存器检查
            # 例如检查DMA控制寄存器、状态寄存器等
            # 目前使用简化版本，返回基本状态

            status_info = {
                'slot': slot,
                'board_id': board_id,
                'dma_status': dma_status,
                'max_data_size': DMA_CONSTANTS['MAX_DATA_SIZE'],
                'default_data_size': DMA_CONSTANTS['DEFAULT_DATA_SIZE'],
                'timestamp': time.time()
            }

            logger.debug(f"DMA状态查询完成 (槽位: {slot}): {status_info}")
            return status_info

        except Exception as e:
            logger.error(f"DMA状态查询失败 (槽位: {slot}): {e}")
            return None
