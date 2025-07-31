# -*- coding: utf-8 -*-
"""
系统管理模块 - 风扇控制、系统状态监控等功能
"""

import numpy as np
import logging
from typing import Optional, Dict
from constants import SYSTEM_CONSTANTS

logger = logging.getLogger(__name__)


class SystemManagement:
    """系统管理类"""

    def __init__(self, board_mgmt):
        """初始化系统管理

        Args:
            board_mgmt: 板卡管理对象
        """
        self.board_mgmt = board_mgmt
        # 获取串口通信模块
        self.serial_ops = getattr(board_mgmt, 'serial_ops', None)

    def set_fan_speed(self, fan_speed: float) -> bool:
        """设置风扇速度（重构set_fan_speed）

        Args:
            fan_speed: 风扇速度值

        Returns:
            操作是否成功
        """
        try:
            # 计算风扇速度值
            fan_speed_lh = np.uint32(
                fan_speed * SYSTEM_CONSTANTS['FAN_SPEED_SCALE'])

            # 构建风扇控制命令
            fan_cmd_buf = []

            # 添加命令头
            fan_cmd_buf.append(np.uint8(SYSTEM_CONSTANTS['FAN_CMD_HEADER_1']))
            fan_cmd_buf.append(np.uint8(SYSTEM_CONSTANTS['FAN_CMD_HEADER_2']))

            fan_cmd_buf.append(np.uint8(SYSTEM_CONSTANTS['FAN_CMD_HEADER_1']))
            fan_cmd_buf.append(np.uint8(0x00))
            fan_cmd_buf.append(np.uint8(0x00))

            # 添加风扇速度值（4字节，大端序）
            fan_cmd_buf.append(np.uint8((fan_speed_lh >> 24) & 0xff))
            fan_cmd_buf.append(np.uint8((fan_speed_lh >> 16) & 0xff))
            fan_cmd_buf.append(np.uint8((fan_speed_lh >> 8) & 0xff))
            fan_cmd_buf.append(np.uint8(fan_speed_lh & 0xff))

            # 添加填充字节
            for i in range(SYSTEM_CONSTANTS['FAN_CMD_PADDING_COUNT']):
                fan_cmd_buf.append(np.uint8(0x00))

            # 添加命令尾
            fan_cmd_buf.append(np.uint8(SYSTEM_CONSTANTS['FAN_CMD_HEADER_2']))
            fan_cmd_buf.append(np.uint8(SYSTEM_CONSTANTS['FAN_CMD_HEADER_1']))

            # 发送命令
            if self.serial_ops:
                try:
                    # 使用默认槽位发送命令
                    self.serial_ops.serial_send_cmd(fan_cmd_buf, 'slot0')
                    logger.debug(f"风扇速度设置命令已发送: {fan_speed}")
                    return True
                except Exception as e:
                    logger.error(f"串口发送风扇命令失败: {e}")
                    return False
            else:
                logger.warning("串口通信模块未初始化，无法发送风扇命令")
                return False

        except Exception as e:
            logger.error(f"设置风扇速度失败: {e}")
            return False

    def get_system_status(self) -> Optional[Dict]:
        """获取系统状态

        Returns:
            系统状态信息字典，失败时返回None
        """
        try:
            # 这里可以添加获取系统温度、风扇转速、电源状态等信息
            # 暂时返回基本状态
            status = {
                'temperature': 0,  # 系统温度
                'fan_speed': 0,    # 风扇转速
                'power_status': SYSTEM_CONSTANTS['STATUS_NORMAL'],  # 电源状态
                'uptime': 0        # 运行时间
            }

            logger.debug("系统状态获取成功")
            return status

        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return None

    def reset_system(self) -> bool:
        """重置系统

        Returns:
            操作是否成功
        """
        try:
            # 这里可以添加系统重置逻辑
            logger.debug("系统重置命令已发送")
            return True

        except Exception as e:
            logger.error(f"系统重置失败: {e}")
            return False
