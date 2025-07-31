# -*- coding: utf-8 -*-
"""
触发控制模块

提供触发控制功能，包括触发配置、触发关闭等
"""

import numpy as np
import logging
from typing import Optional, Dict
from utils import ValidationError, ValidationUtils
from constants import TRIGGER_CONSTANTS

logger = logging.getLogger(__name__)


class TriggerControl:
    """触发控制模块"""

    def __init__(self, serial_communications):
        """初始化触发控制模块

        Args:
            serial_communications: 串口通信模块实例
        """
        self.serial_comm = serial_communications

    def trigger_control(self, trigger_source: int, trigger_us: float,
                        trigger_num: int, trigger_continue: int) -> bool:
        """触发控制

        Args:
            trigger_source: 触发源 (0: 内部触发, 1: 外部触发)
            trigger_us: 触发周期（微秒）
            trigger_num: 触发次数（连续模式时无效）
            trigger_continue: 触发模式 (0: 单次模式, 1: 连续模式)

        Returns:
            操作是否成功

        Raises:
            ValidationError: 当参数无效时
            RuntimeError: 当触发控制失败时
        """
        # 参数验证
        if not ValidationUtils.validate_trigger_source(trigger_source):
            raise ValidationError(
                "trigger_source", trigger_source, f"无效的触发源: {trigger_source}")

        if not ValidationUtils.validate_trigger_period(trigger_us):
            raise ValidationError("trigger_us", trigger_us, "触发周期必须是正数")

        if not ValidationUtils.validate_trigger_count(trigger_num):
            raise ValidationError("trigger_num", trigger_num, "触发次数必须是非负整数")

        if not ValidationUtils.validate_trigger_mode(trigger_continue):
            raise ValidationError(
                "trigger_continue", trigger_continue, f"无效的触发模式: {trigger_continue}")

        try:
            # 计算触发参数
            trigger_times = np.uint32(trigger_num)
            trigger_us_cnt = np.uint32(
                round(trigger_us / TRIGGER_CONSTANTS['TRIGGER_PERIOD_SCALE']) - 1)

            # 构建命令数据
            # [CMD][ENABLE][ENABLE][SRC][MODE][COUNT(4)][PERIOD(4)]...
            fband_data_buf = []

            # 命令头
            fband_data_buf.extend(TRIGGER_CONSTANTS['CMD_HEADER'])

            # 触发命令
            fband_data_buf.append(np.uint8(TRIGGER_CONSTANTS['TRIGGER_CMD']))
            fband_data_buf.append(
                np.uint8(TRIGGER_CONSTANTS['TRIGGER_ENABLE']))
            fband_data_buf.append(
                np.uint8(TRIGGER_CONSTANTS['TRIGGER_ENABLE']))
            fband_data_buf.append(np.uint8(trigger_source))
            fband_data_buf.append(np.uint8(trigger_continue))

            # 触发次数（4字节）
            fband_data_buf.append(np.uint8(trigger_times >> 24 & 0xff))
            fband_data_buf.append(np.uint8(trigger_times >> 16 & 0xff))
            fband_data_buf.append(np.uint8(trigger_times >> 8 & 0xff))
            fband_data_buf.append(np.uint8(trigger_times & 0xff))

            # 触发周期（4字节）
            fband_data_buf.append(np.uint8(trigger_us_cnt >> 24 & 0xff))
            fband_data_buf.append(np.uint8(trigger_us_cnt >> 16 & 0xff))
            fband_data_buf.append(np.uint8(trigger_us_cnt >> 8 & 0xff))
            fband_data_buf.append(np.uint8(trigger_us_cnt & 0xff))

            # 填充剩余字节到固定数据包长度
            # 数据包总长度固定为36字节，需要填充18个字节
            for i in range(TRIGGER_CONSTANTS['TRIGGER_CONTROL_PADDING_SIZE']):
                fband_data_buf.append(np.uint8(0x00))

            # 命令尾
            fband_data_buf.extend(TRIGGER_CONSTANTS['CMD_FOOTER'])

            # 验证数据包长度
            packet_length = len(fband_data_buf)
            expected_length = TRIGGER_CONSTANTS['PACKET_TOTAL_SIZE']
            if packet_length != expected_length:
                logger.warning(
                    f"数据包长度不匹配: 实际{packet_length}字节, 期望{expected_length}字节")

            # 发送命令
            if self.serial_comm:
                try:
                    self.serial_comm.serial_send_cmd(fband_data_buf)
                except Exception as e:
                    logger.error(f"串口通信发送失败: {e}")
                    return False
            else:
                logger.warning("串口通信模块未初始化，无法发送触发命令")
                return False

            logger.debug(
                f"触发控制设置完成 (源: {trigger_source}, 周期: {trigger_us}us, 次数: {trigger_num}, 模式: {trigger_continue})")
            return True

        except Exception as e:
            logger.error(f"触发控制设置失败: {e}")
            return False

    def trigger_close(self) -> bool:
        """关闭触发

        Returns:
            操作是否成功
        """
        try:
            fband_data_buf = []

            fband_data_buf.extend(TRIGGER_CONSTANTS['CMD_HEADER'])

            # 触发关闭命令
            fband_data_buf.append(np.uint8(TRIGGER_CONSTANTS['TRIGGER_CMD']))
            fband_data_buf.append(
                np.uint8(TRIGGER_CONSTANTS['TRIGGER_DISABLE']))
            fband_data_buf.append(
                np.uint8(TRIGGER_CONSTANTS['TRIGGER_DISABLE']))

            # 填充剩余字节到固定数据包长度
            for i in range(TRIGGER_CONSTANTS['TRIGGER_CLOSE_PADDING_SIZE']):
                fband_data_buf.append(np.uint8(0x00))

            # 使用常量构建命令尾
            fband_data_buf.extend(TRIGGER_CONSTANTS['CMD_FOOTER'])

            # 验证数据包长度
            packet_length = len(fband_data_buf)
            expected_length = TRIGGER_CONSTANTS['PACKET_TOTAL_SIZE']
            if packet_length != expected_length:
                logger.warning(
                    f"数据包长度不匹配: 实际{packet_length}字节, 期望{expected_length}字节")

            if self.serial_comm:
                try:
                    self.serial_comm.serial_send_cmd(fband_data_buf)
                except Exception as e:
                    logger.error(f"串口通信发送失败: {e}")
                    return False
            else:
                logger.warning("串口通信模块未初始化，无法发送触发关闭命令")
                return False

            logger.debug("触发关闭完成")
            return True

        except Exception as e:
            logger.error(f"触发关闭失败: {e}")
            return False

    def get_trigger_status(self) -> Optional[Dict]:
        """获取触发状态

        Returns:
            触发状态信息，失败时返回None
        """
        try:
            # 这里可以添加查询触发状态的逻辑
            # 例如通过寄存器读取当前触发状态
            status = {
                'is_enabled': False,  # 默认状态
                'trigger_source': None,
                'trigger_mode': None,
                'trigger_count': 0,
                'trigger_period': 0.0
            }

            logger.debug("获取触发状态完成")
            return status

        except Exception as e:
            logger.error(f"获取触发状态失败: {e}")
            return None
