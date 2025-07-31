# -*- coding: utf-8 -*-
"""
触发管理模块 - 处理触发相关的业务逻辑
"""

import logging
from typing import Dict, Any
from utils import ValidationError, ValidationUtils
from constants import TRIGGER_CONSTANTS

logger = logging.getLogger(__name__)


class TriggerManagement:
    """触发管理类"""

    def __init__(self, board_mgmt):
        """初始化触发管理

        Args:
            board_mgmt: 板卡管理对象
        """
        self.board_mgmt = board_mgmt
        # 获取触发控制模块（硬件层）
        self.trigger_control = getattr(board_mgmt, 'trigger_control', None)

        # 触发参数状态
        self._trigger_us = TRIGGER_CONSTANTS['DEFAULT_TRIGGER_US']
        self._trigger_num = TRIGGER_CONSTANTS['DEFAULT_TRIGGER_NUM']
        self._trigger_source = TRIGGER_CONSTANTS['DEFAULT_TRIGGER_SOURCE']
        self._trigger_continue = TRIGGER_CONSTANTS['DEFAULT_TRIGGER_CONTINUE']

    def set_trigger_period(self, period: float) -> bool:
        """设置触发周期

        Args:
            period: 触发周期（秒）

        Returns:
            操作是否成功
        """
        try:
            # 计算周期时间（纳秒）
            period_time = TRIGGER_CONSTANTS['PERIOD_TIME_NS']
            times = round(period * 1e9 / period_time)

            # 验证周期是否匹配
            if period_time * times != period * 1e9:
                raise ValidationError(
                    "period", period,
                    f"采样模式与触发时间不匹配！请通过setValue()函数更改trigger_us"
                )

            self._trigger_us = period * 1e6  # 转换为微秒
            logger.debug(f"触发周期设置成功: {period}s ({self._trigger_us}us)")
            return True

        except Exception as e:
            logger.error(f"触发周期设置失败: {e}")
            return False

    def set_trigger_source(self, source: str) -> bool:
        """设置触发源

        Args:
            source: 触发源 ('Internal' 或 'External')

        Returns:
            操作是否成功
        """
        try:
            if source not in ['Internal', 'External']:
                raise ValidationError(
                    "source", source, "触发源不支持"
                )

            self._trigger_source = int(source == 'External')
            logger.debug(f"触发源设置成功: {source}")
            return True

        except Exception as e:
            logger.error(f"触发源设置失败: {e}")
            return False

    def set_trigger_number(self, number: int) -> bool:
        """设置触发次数

        Args:
            number: 触发次数

        Returns:
            操作是否成功
        """
        try:
            if not ValidationUtils.validate_trigger_number(number):
                raise ValidationError(
                    "number", number, "触发次数必须大于0"
                )

            self._trigger_num = number
            logger.debug(f"触发次数设置成功: {number}")
            return True

        except Exception as e:
            logger.error(f"触发次数设置失败: {e}")
            return False

    def set_trigger_continue(self, continue_flag: bool) -> bool:
        """设置触发连续模式

        Args:
            continue_flag: 连续触发标志

        Returns:
            操作是否成功
        """
        try:
            self._trigger_continue = int(continue_flag)
            logger.debug(f"触发连续模式设置成功: {continue_flag}")
            return True

        except Exception as e:
            logger.error(f"触发连续模式设置失败: {e}")
            return False

    def execute_trigger(self) -> bool:
        """执行触发控制

        Returns:
            操作是否成功
        """
        try:
            if not self.trigger_control:
                logger.error("触发控制模块未初始化")
                return False

            # 调用硬件层的触发控制
            result = self.trigger_control.trigger_control(
                trigger_source=self._trigger_source,
                trigger_us=self._trigger_us,
                trigger_num=self._trigger_num,
                trigger_continue=self._trigger_continue
            )

            if result:
                logger.debug("触发控制执行成功")
                return True
            else:
                logger.error("触发控制执行失败")
                return False

        except Exception as e:
            logger.error(f"触发控制执行失败: {e}")
            return False

    def close_trigger(self) -> bool:
        """关闭触发

        Returns:
            操作是否成功
        """
        try:
            if not self.trigger_control:
                logger.error("触发控制模块未初始化")
                return False

            result = self.trigger_control.trigger_close()

            if result:
                logger.debug("触发关闭成功")
                return True
            else:
                logger.error("触发关闭失败")
                return False

        except Exception as e:
            logger.error(f"触发关闭失败: {e}")
            return False

    def get_trigger_status(self) -> Dict[str, Any]:
        """获取触发状态

        Returns:
            触发状态信息字典
        """
        try:
            # 获取硬件层状态
            hw_status = None
            if self.trigger_control:
                hw_status = self.trigger_control.get_trigger_status()

            # 构建业务层状态
            status = {
                'trigger_source': 'External' if self._trigger_source == 1 else 'Internal',
                'trigger_period': self._trigger_us / 1e6,  # 转换为秒
                'trigger_number': self._trigger_num,
                'trigger_continue': bool(self._trigger_continue),
                'trigger_control_available': self.trigger_control is not None,
                'hardware_status': hw_status
            }

            logger.debug(f"触发状态获取成功: {status}")
            return status

        except Exception as e:
            logger.error(f"触发状态获取失败: {e}")
            return {}

    def set_TRIG(self, name: str, value) -> bool:
        """设置触发参数（重构set_TRIG）

        Args:
            name: 参数名称
            value: 参数值

        Returns:
            操作是否成功
        """
        try:
            if name == 'TriggerPeriod':
                return self.set_trigger_period(value)
            elif name == 'TriggerSource':
                return self.set_trigger_source(value)
            elif name == 'TriggerNumber':
                return self.set_trigger_number(value)
            elif name == 'TriggerContinue':
                return self.set_trigger_continue(value)
            elif name == 'Trigger':
                return self.execute_trigger()
            else:
                logger.warning(f"未知的触发参数: {name}")
                return False

        except Exception as e:
            logger.error(f"触发参数设置失败: {e}")
            return False
