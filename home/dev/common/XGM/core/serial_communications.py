# -*- coding: utf-8 -*-
"""
串口通信模块

提供PCIe串口通信功能，包括数据读写、命令发送等
"""

import time
import numpy as np
import logging
from typing import List, Union, Optional, Dict
from utils import ValidationError, ValidationUtils
from constants import REGISTER_CONSTANTS, SERIAL_CONSTANTS


logger = logging.getLogger(__name__)


class SerialCommunications:
    """串口通信模块"""

    def __init__(self, register_ops):
        """初始化串口通信模块

        Args:
            register_ops: 寄存器操作模块实例
        """
        self.register_ops = register_ops

    def serial_write(self, data: Union[List, np.ndarray], slot: str) -> int:
        """PCIe串口写入数据

        Args:
            data: 要写入的数据数组
            slot: 板卡槽位

        Returns:
            写入的数据长度

        Raises:
            ValidationError: 当参数无效时
            RuntimeError: 当串口写入失败时
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_serial_data(data):
            raise ValidationError("data", data, "数据必须是有效的列表或numpy数组")

        try:
            for send_cnt in range(len(data)):
                # 等待发送缓冲区就绪
                for i in range(SERIAL_CONSTANTS['MAX_RETRY_COUNT']):
                    status = self.register_ops.read_reg(
                        REGISTER_CONSTANTS['SERIAL_STATUS_REG'], slot)
                    if (status & SERIAL_CONSTANTS['TX_READY_MASK']) == 0:
                        break
                    else:
                        time.sleep(SERIAL_CONSTANTS['RETRY_DELAY'])
                else:
                    logger.warning(f"串口发送超时 (槽位: {slot}, 数据索引: {send_cnt})")

                # 写入数据
                self.register_ops.write_reg(
                    REGISTER_CONSTANTS['SERIAL_CTRL_REG'], data[send_cnt], slot)

            logger.debug(f"串口数据写入完成 (槽位: {slot}, 数据长度: {len(data)})")
            return len(data)

        except Exception as e:
            logger.error(f"串口数据写入失败 (槽位: {slot}): {e}")
            raise RuntimeError(f"串口数据写入失败: {e}")

    def serial_read(self, slot: str, time_out: float) -> Union[List, str]:
        """PCIe串口读取数据

        Args:
            slot: 板卡槽位
            time_out: 超时时间（秒）

        Returns:
            读取的数据数组，超时时返回'time_out'

        Raises:
            ValidationError: 当参数无效时
            RuntimeError: 当串口读取失败时
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_timeout(time_out):
            raise ValidationError("time_out", time_out, "超时时间必须是0-3600秒之间的正数")

        try:
            recv_data = []
            recv_num = 0
            time0 = time.time()

            while True:
                # 检查接收缓冲区状态
                status = self.register_ops.read_reg(
                    REGISTER_CONSTANTS['SERIAL_STATUS_REG'], slot)
                if (status & SERIAL_CONSTANTS['RX_READY_MASK']) == 1:
                    # 读取数据
                    data = self.register_ops.read_reg(
                        REGISTER_CONSTANTS['SERIAL_DATA_REG'], slot)
                    recv_data.append(np.uint8(data))
                    recv_num += 1

                # 检查是否达到最大接收大小
                if recv_num == SERIAL_CONSTANTS['MAX_RECV_SIZE']:
                    logger.debug(
                        f"串口数据读取完成 (槽位: {slot}, 数据长度: {len(recv_data)})")
                    return recv_data

                # 检查超时
                time1 = time.time()
                if time1 - time0 > time_out:
                    logger.warning(f"串口读取超时 (槽位: {slot}, 超时时间: {time_out}s)")
                    return 'time_out'

                # 添加短暂延时，避免CPU占用过高
                time.sleep(SERIAL_CONSTANTS['READ_DELAY'])

        except Exception as e:
            logger.error(f"串口数据读取失败 (槽位: {slot}): {e}")
            raise RuntimeError(f"串口数据读取失败: {e}")

    def serial_reset_input_buffer(self, slot: str) -> None:
        """PCIe串口重置输入缓冲区

        Args:
            slot: 板卡槽位

        Raises:
            ValidationError: 当槽位无效时
            RuntimeError: 当串口重置失败时
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            while True:
                # 检查接收缓冲区状态
                status = self.register_ops.read_reg(
                    REGISTER_CONSTANTS['SERIAL_STATUS_REG'], slot)
                if (status & SERIAL_CONSTANTS['RX_READY_MASK']) == 1:
                    # 读取并丢弃数据
                    self.register_ops.read_reg(
                        REGISTER_CONSTANTS['SERIAL_DATA_REG'], slot)
                else:
                    break

            logger.debug(f"串口输入缓冲区重置完成 (槽位: {slot})")

        except Exception as e:
            logger.error(f"串口输入缓冲区重置失败 (槽位: {slot}): {e}")
            raise RuntimeError(f"串口输入缓冲区重置失败: {e}")

    def serial_send_cmd(self, send_data: Union[List, np.ndarray], slot: str = 'slot0') -> List:
        """PCIe串口发送命令

        Args:
            send_data: 要发送的命令数据
            slot: 板卡槽位（默认为'slot0'）

        Returns:
            接收到的响应数据

        Raises:
            ValidationError: 当参数无效时
            RuntimeError: 当命令发送失败时
        """
        if not ValidationUtils.validate_serial_data(send_data):
            raise ValidationError("send_data", send_data,
                                  "命令数据必须是有效的列表或numpy数组")

        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            # 重置输入缓冲区
            self.serial_reset_input_buffer(slot)

            # 发送命令并等待响应
            while True:
                self.serial_write(send_data, slot)
                recv_data = self.serial_read(
                    slot, SERIAL_CONSTANTS['DEFAULT_TIMEOUT'])

                # 检查响应是否正确
                if recv_data == 'time_out':
                    logger.warning(f"命令发送超时 (槽位: {slot})")
                    continue

                # 验证命令响应数据
                expected_response = send_data[SERIAL_CONSTANTS['CMD_RESPONSE_START_INDEX']
                    :SERIAL_CONSTANTS['CMD_RESPONSE_END_INDEX']]
                actual_response = recv_data[:SERIAL_CONSTANTS['CMD_RESPONSE_TAIL_INDEX']]

                if actual_response == expected_response:
                    logger.debug(
                        f"命令发送成功 (槽位: {slot}, 数据长度: {len(recv_data)})")
                    break
                else:
                    logger.warning(f"命令响应错误 (槽位: {slot})")
                    continue

            return recv_data

        except Exception as e:
            logger.error(f"命令发送失败: {e}")
            raise RuntimeError(f"命令发送失败: {e}")

    def get_serial_status(self, slot: str) -> Optional[Dict]:
        """获取串口状态

        Args:
            slot: 板卡槽位

        Returns:
            串口状态信息，失败时返回None
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        try:
            status_reg = self.register_ops.read_reg(
                REGISTER_CONSTANTS['SERIAL_STATUS_REG'], slot)

            status_info = {
                'slot': slot,
                'tx_ready': (status_reg & SERIAL_CONSTANTS['TX_READY_MASK']) == 0,
                'rx_ready': (status_reg & SERIAL_CONSTANTS['RX_READY_MASK']) == 1,
                'raw_status': f'0x{status_reg:02X}'
            }

            logger.debug(f"串口状态查询完成 (槽位: {slot}): {status_info}")
            return status_info

        except Exception as e:
            logger.error(f"串口状态查询失败 (槽位: {slot}): {e}")
            return None
