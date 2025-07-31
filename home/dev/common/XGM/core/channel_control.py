# -*- coding: utf-8 -*-
"""
通道控制模块 - DA/AD通道控制功能
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Union, Tuple
from utils import ValidationError, ValidationUtils
from constants import REGISTER_CONSTANTS, CHANNEL_CONSTANTS, DATA_LIMITS
from .dma_operations import DmaOperations
from .register_operations import RegisterOperations

logger = logging.getLogger(__name__)


class ChannelControl:
    """通道控制模块"""

    def __init__(self, board_mgmt):
        """初始化通道控制

        Args:
            board_mgmt: 板卡管理对象
        """
        self.board_mgmt = board_mgmt
        self.dma_ops = DmaOperations(board_mgmt)
        self.register_ops = RegisterOperations(board_mgmt)

        # 通道信息管理
        self.dac_channels = {}  # DAC通道信息映射
        self.adc_channels = {}  # ADC通道信息映射

        # 优化：创建反向索引，提高查找效率
        self._dac_channel_by_num = {}  # channel_num -> channel_info
        self._adc_channel_by_num = {}  # channel_num -> channel_info

        # DC偏移值数组（与原版保持一致）
        self.offset = np.int32(
            np.zeros(CHANNEL_CONSTANTS['DC_OFFSET_CHANNELS']))

    def write_dac_data(self, slot: str, channel_num: int, dac_data) -> bool:
        """写入DAC数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            dac_data: DAC数据

        Returns:
            操作是否成功
        """
        try:
            result = self.dma_ops.pcie_write_data(slot, channel_num, dac_data)
            if result == CHANNEL_CONSTANTS['SUCCESS_CODE']:
                logger.debug(
                    f"DAC数据写入成功: 槽位{slot}, 通道{channel_num}, 数据长度{len(dac_data)}")
                return True
            else:
                logger.error(f"DAC数据写入失败，错误码: {result}")
                return False
        except Exception as e:
            logger.error(f"DAC数据写入失败: {e}")
            return False

    def dac_channel_control(self, slot: str, channel_num: int, replay_len: int,
                            trigger_delay: int, replay_times: int,
                            replay_continue: bool, dac_en: bool) -> bool:
        """DAC通道控制

        Args:
            slot: 板卡槽位
            channel_num: DAC通道号
            replay_len: 重放长度
            trigger_delay: 触发延时
            replay_times: 重放次数
            replay_continue: 重放连续模式
            dac_en: DAC使能 (True: 使能, False: 禁用)

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dac_channel(channel_num):
            raise ValidationError(
                "channel_num", channel_num, f"DAC通道号必须在0到{CHANNEL_CONSTANTS['MAX_DAC_CHANNELS']-1}之间")

        if not isinstance(dac_en, bool):
            raise ValidationError("dac_en", dac_en, "DAC使能必须是布尔值")

        try:
            # 计算寄存器地址：DAC控制寄存器的内存映射
            #
            # 寄存器地址结构：
            # base_addr = DAC_CTRL_BASE + DAC_CHANNEL_OFFSET * channel_num
            #
            # 地址组成：
            # - DAC_CTRL_BASE: 0x8000 (DAC控制基地址)
            # - DAC_CHANNEL_OFFSET: 0x400 (每个通道的寄存器空间)
            # - channel_num: 通道号 (0-7)
            #
            # 寄存器布局：
            # 通道0: 0x8000 + 0x400*0 = 0x8000
            # 通道1: 0x8000 + 0x400*1 = 0x8400
            # 通道2: 0x8000 + 0x400*2 = 0x8800
            # ...
            # 通道7: 0x8000 + 0x400*7 = 0x9C00
            #
            # 每个通道的寄存器空间：
            # +0x00: 保留
            # +0x01: DAC使能寄存器
            # +0x02: DAC重放长度寄存器
            # +0x03: DAC触发延时寄存器
            # +0x04: DAC重放次数寄存器
            # +0x05: DAC偏移寄存器
            base_addr = REGISTER_CONSTANTS['DAC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['DAC_CHANNEL_OFFSET'] * channel_num

            if not dac_en:
                # 禁用DAC
                self.register_ops.write_reg(
                    base_addr + REGISTER_CONSTANTS['DAC_ENABLE_REG'], 0, slot)
                logger.debug(f"DAC通道禁用 (槽位: {slot}, 通道: {channel_num})")
            else:
                # 配置DAC参数
                self.register_ops.write_reg(
                    # 先禁用
                    base_addr + REGISTER_CONSTANTS['DAC_ENABLE_REG'], 0, slot)
                self.register_ops.write_reg(
                    # 重放长度寄存器：配置DAC重放的数据长度
                    # 数据类型转换：确保写入寄存器的数据为32位无符号整数
                    base_addr + REGISTER_CONSTANTS['DAC_REPLAY_LEN_REG'],
                    getattr(np, CHANNEL_CONSTANTS['DATA_TYPE_UINT32'])(replay_len), slot)
                self.register_ops.write_reg(
                    # 触发延时寄存器：配置触发信号到DAC输出的延时
                    # 数据类型转换：确保写入寄存器的数据为32位无符号整数
                    base_addr + REGISTER_CONSTANTS['DAC_TRIGGER_DELAY_REG'],
                    getattr(np, CHANNEL_CONSTANTS['DATA_TYPE_UINT32'])(trigger_delay), slot)

                # 组合重放次数和连续模式：将两个参数打包到一个32位寄存器
                #
                # 寄存器位分配：
                # - 位[30:0]: 重放次数 (replay_times)
                # - 位[31]: 连续模式标志 (replay_continue)
                #
                # 位操作说明：
                # - replay_times: 直接使用低31位
                # - replay_continue << 31: 左移31位到最高位
                # - 组合: replay_times + (replay_continue << 31)
                #
                # 示例：
                # replay_times = 1000, replay_continue = 1
                # 结果: 1000 + (1 << 31) = 1000 + 2147483648 = 2147484648
                #
                # 硬件解析：
                # - 低31位: 1000 (重放次数)
                # - 最高位: 1 (连续模式)
                #
                # 数据类型转换：
                # getattr(np, 'uint32') 等价于 np.uint32
                # 确保写入寄存器的数据为32位无符号整数
                replay_config = getattr(np, CHANNEL_CONSTANTS['DATA_TYPE_UINT32'])(
                    replay_times + (int(replay_continue) << 31))
                self.register_ops.write_reg(
                    base_addr + REGISTER_CONSTANTS['DAC_REPLAY_TIMES_REG'], replay_config, slot)

                # 使能DAC
                self.register_ops.write_reg(
                    base_addr + REGISTER_CONSTANTS['DAC_ENABLE_REG'], 1, slot)

                logger.debug(
                    f"DAC通道配置完成 (槽位: {slot}, 通道: {channel_num}, 长度: {replay_len}, 延时: {trigger_delay}, 次数: {replay_times}, 连续: {replay_continue})")

            return True

        except Exception as e:
            logger.error(f"DAC通道控制失败 (槽位: {slot}, 通道: {channel_num}): {e}")
            return False

    def dac_update(self, channel_num: int, trigger_delay: int,
                   replay_times: int, replay_continue: bool,
                   dac_data: Union[List, np.ndarray]) -> bool:
        """DAC数据更新

        Args:
            channel_num: DAC通道号（从0开始）
            trigger_delay: 触发延时
            replay_times: 重放次数
            replay_continue: 重放连续模式
            dac_data: DAC数据数组

        Returns:
            操作是否成功
        """
        try:
            # 参数验证
            if not ValidationUtils.validate_dma_data(dac_data):
                raise ValidationError("dac_data", dac_data,
                                      "DAC数据必须是有效的列表或numpy数组")

            # 获取通道信息（灵活适配新架构）
            channel_info = self._get_dac_channel_info(channel_num)
            if not channel_info:
                logger.error(f"未找到DAC通道: {channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 数据缩放：将浮点数DAC数据转换为硬件可接受的13位整数格式
            #
            # 硬件规格：
            # - DAC位数：13位
            # - 最大值：2^13 - 1 = 8191
            # - 数据类型：16位有符号整数 (np.int16)
            #
            # 数据范围映射：
            # - 输入范围：[-1.0, 1.0] (浮点数)
            # - 输出范围：[-8191, 8191] (13位有符号整数)
            #
            # 为什么是 2^13 - 1：
            # - 13位DAC能表示的最大值：2^13 = 8192
            # - 实际最大值（从0开始）：2^13 - 1 = 8191
            # - 有符号范围：[-8191, 8191]
            #
            # 示例：
            # 输入: 0.5     → 输出: 0.5 * 8191 = 4095
            # 输入: -0.5    → 输出: -0.5 * 8191 = -4095
            # 输入: 1.0     → 输出: 1.0 * 8191 = 8191
            # 输入: -1.0    → 输出: -1.0 * 8191 = -8191
            dac_data_i = np.int16(dac_data * DATA_LIMITS['DAC_SCALE_FACTOR'])
            data_len = len(dac_data_i)

            # 数据长度检查：确保DAC数据不超过硬件存储限制
            #
            # 硬件限制：
            # - 最大存储深度：16384 * 32 = 524,288 个样点
            # - 16384：每个DMA块的大小
            # - 32：最大DMA块数量
            #
            # 为什么有这个限制：
            # - FPGA内部存储空间有限
            # - DMA传输效率考虑
            # - 实时性能要求
            #
            # 实际限制：524,288 个样点
            # 在2.5GHz采样率下，约等于 0.21ms 的数据长度
            if data_len > DATA_LIMITS['MAX_DAC_DATA_LENGTH']:
                logger.error(
                    f"数据长度超出限制: {data_len} > {DATA_LIMITS['MAX_DAC_DATA_LENGTH']}")
                return False

            # 配置DAC通道（先禁用）
            self.dac_channel_control(slot, ch_num, data_len,
                                     trigger_delay, replay_times, replay_continue, False)

            # 写入DAC数据
            self.write_dac_data(slot, ch_num, dac_data_i)

            # 使能DAC通道
            self.dac_channel_control(slot, ch_num, data_len,
                                     trigger_delay, replay_times, replay_continue, True)

            logger.debug(
                f"DAC数据更新完成 (通道: {channel_num}, 数据长度: {data_len}, 延时: {trigger_delay}, 次数: {replay_times}, 连续: {replay_continue})")
            return True

        except Exception as e:
            logger.error(f"DAC数据更新失败 (通道: {channel_num}): {e}")
            return False

    def _get_dac_channel_info(self, channel_num: int) -> Optional[Dict]:
        """获取DAC通道信息

        Args:
            channel_num: DAC通道号

        Returns:
            通道信息字典，包含slot和channel_num，失败时返回None
        """
        # 参数验证
        if not ValidationUtils.validate_dac_channel(channel_num):
            logger.error(f"无效的DAC通道号: {channel_num}")
            return None

        # 优化：使用反向索引直接查找，O(1)时间复杂度
        channel_info = self._dac_channel_by_num.get(channel_num)
        if channel_info:
            return {
                'slot': channel_info['slot'],
                'channel_num': channel_info['channel_num']
            }

        # 未找到匹配的通道
        logger.error(f"未找到DAC通道: {channel_num}")
        return None

    def _get_adc_channel_info(self, channel_num: int) -> Optional[Dict]:
        """获取ADC通道信息

        Args:
            channel_num: ADC通道号

        Returns:
            通道信息字典，包含slot和channel_num，失败时返回None
        """
        # 参数验证
        if not ValidationUtils.validate_adc_channel(channel_num):
            logger.error(f"无效的ADC通道号: {channel_num}")
            return None

        # 优化：使用反向索引直接查找，O(1)时间复杂度
        channel_info = self._adc_channel_by_num.get(channel_num)
        if channel_info:
            return {
                'slot': channel_info['slot'],
                'channel_num': channel_info['channel_num']
            }

        # 未找到匹配的通道
        logger.error(f"未找到ADC通道: {channel_num}")
        return None

    def dac_open(self, channel_num: int) -> bool:
        """打开DAC通道

        Args:
            channel_num: DAC通道号

        Returns:
            操作是否成功
        """
        try:
            # 获取通道信息
            channel_info = self._get_dac_channel_info(channel_num)
            if not channel_info:
                logger.error(f"未找到DAC通道: {channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 使能DAC通道
            base_addr = REGISTER_CONSTANTS['DAC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['DAC_CHANNEL_OFFSET'] * ch_num
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['DAC_ENABLE_REG'], 1, slot)

            logger.debug(f"DAC通道打开完成 (通道: {channel_num})")
            return True

        except Exception as e:
            logger.error(f"DAC通道打开失败 (通道: {channel_num}): {e}")
            return False

    def dac_close(self, channel_num: int) -> bool:
        """关闭DAC通道

        Args:
            channel_num: DAC通道号

        Returns:
            操作是否成功
        """
        try:
            # 获取通道信息
            channel_info = self._get_dac_channel_info(channel_num)
            if not channel_info:
                logger.error(f"未找到DAC通道: {channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 禁用DAC通道
            base_addr = REGISTER_CONSTANTS['DAC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['DAC_CHANNEL_OFFSET'] * ch_num
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['DAC_ENABLE_REG'], 0, slot)

            logger.debug(f"DAC通道关闭完成 (通道: {channel_num})")
            return True

        except Exception as e:
            logger.error(f"DAC通道关闭失败 (通道: {channel_num}): {e}")
            return False

    def read_adc_data_control(self, adc_channel_num: int, trigger_delay: int,
                              times: int, save_len: int) -> bool:
        """ADC数据读取控制

        Args:
            adc_channel_num: ADC通道号
            trigger_delay: 触发延迟
            times: 读取次数
            save_len: 保存长度

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            raise ValidationError(
                "adc_channel_num", adc_channel_num, f"ADC通道号必须在0到{CHANNEL_CONSTANTS['MAX_ADC_CHANNELS']-1}之间")

        if not ValidationUtils.validate_trigger_delay(trigger_delay):
            raise ValidationError(
                "trigger_delay", trigger_delay, "触发延迟必须大于等于0")

        if not ValidationUtils.validate_replay_times(times):
            raise ValidationError("times", times, "读取次数必须大于0")

        if not ValidationUtils.validate_save_length(save_len):
            raise ValidationError("save_len", save_len, "保存长度必须大于0")

        try:
            # 获取通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 使用常量定义的寄存器操作逻辑
            # 计算ADC控制寄存器基地址
            base_addr = REGISTER_CONSTANTS['ADC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['ADC_CHANNEL_OFFSET'] * ch_num

            # 1. 使能ADC模块
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['ADC_ENABLE_REG'], 1, slot)

            # 2. 配置触发延时
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['ADC_TRIGGER_DELAY_REG'],
                np.uint32(trigger_delay), slot)

            # 3. 配置保存长度
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['ADC_SAVE_LEN_REG'],
                np.uint32(save_len), slot)

            # 4. 配置读取次数（与原版一致：times-1）
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['ADC_TIMES_REG'],
                np.uint32(times - 1), slot)

            # 5. 禁用ADC模块
            self.register_ops.write_reg(
                base_addr + REGISTER_CONSTANTS['ADC_ENABLE_REG'], 0, slot)

            logger.debug(f"ADC数据读取控制完成: 通道{adc_channel_num}")
            return True

        except Exception as e:
            logger.error(f"ADC数据读取控制失败: {e}")
            return False

    def read_adc_data(self, adc_channel_num: int, times: int, save_len: int) -> Optional[np.ndarray]:
        """读取ADC数据

        Args:
            adc_channel_num: ADC通道号
            times: 读取次数
            save_len: 保存长度

        Returns:
            ADC数据数组，失败时返回None
        """
        # 参数验证
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            raise ValidationError(
                "adc_channel_num", adc_channel_num, f"ADC通道号必须在0到{CHANNEL_CONSTANTS['MAX_ADC_CHANNELS']-1}之间")

        if not ValidationUtils.validate_replay_times(times):
            raise ValidationError("times", times, "读取次数必须大于0")

        if not ValidationUtils.validate_save_length(save_len):
            raise ValidationError("save_len", save_len, "保存长度必须大于0")

        try:
            # 获取通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return None

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 使用常量定义的寄存器操作逻辑
            # 计算ADC控制寄存器基地址
            base_addr = REGISTER_CONSTANTS['ADC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['ADC_CHANNEL_OFFSET'] * ch_num

            # 读取ADC保存状态寄存器
            save_state_i = self.register_ops.read_reg(
                base_addr + REGISTER_CONSTANTS['ADC_SAVE_LEN_REG'], slot)

            # 检查保存状态
            if (save_state_i & 1) == 0:
                # 数据保存未完成，返回空数组和-1长度
                logger.debug(f"ADC数据保存未完成: 通道{adc_channel_num}")
                return np.array([]).reshape(0, 0)
            else:
                # 数据保存完成，读取ADC数据
                adc_data = self.dma_ops.pcie_read_data(slot, ch_num, save_len)

                if adc_data is not None:
                    # 转换为numpy数组并重塑为二维数组
                    data = np.array(adc_data, dtype=CHANNEL_CONSTANTS['DATA_TYPE_INT32']).reshape(
                        times, save_len)
                    logger.debug(
                        f"ADC数据读取成功: 通道{adc_channel_num}, 数据形状{data.shape}")
                    return data
                else:
                    logger.error(f"ADC数据读取失败: 通道{adc_channel_num}")
                    return None

        except Exception as e:
            logger.error(f"ADC数据读取失败: {e}")
            return None

    def dac_offset(self, channel_num: int, offset: int) -> bool:
        """设置DAC通道偏移

        Args:
            channel_num: DAC通道号
            offset: 偏移值

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_dac_channel(channel_num):
            raise ValidationError(
                "channel_num", channel_num, f"DAC通道号必须在0到{CHANNEL_CONSTANTS['MAX_DAC_CHANNELS']-1}之间")

        try:
            # 获取通道信息
            channel_info = self._get_dac_channel_info(channel_num)
            if not channel_info:
                logger.error(f"未找到DAC通道: {channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 设置DAC偏移寄存器
            base_addr = REGISTER_CONSTANTS['DAC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['DAC_CHANNEL_OFFSET'] * ch_num
            self.register_ops.write_reg(base_addr + REGISTER_CONSTANTS['DAC_OFFSET_REG'],
                                        np.int32(offset), slot)

            logger.debug(f"DAC偏移设置成功: 通道{channel_num}, 偏移{offset}")
            return True

        except Exception as e:
            logger.error(f"DAC偏移设置失败: {e}")
            return False

    def dac_offset_flash(self, channel_num: int, offset: int, password: int) -> bool:
        """设置DAC通道偏移并保存到Flash

        Args:
            channel_num: DAC通道号
            offset: 偏移值
            password: 密码

        Returns:
            操作是否成功
        """
        # 参数验证 - 只允许Z-PULSE通道
        if not ValidationUtils.validate_z_pulse_channel(channel_num):
            logger.error(f'非Z-PULSE通道：{channel_num}')
            return False

        try:
            # 获取通道信息
            channel_info = self._get_dac_channel_info(channel_num)
            if not channel_info:
                logger.error(f"未找到DAC通道: {channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 设置DAC偏移寄存器
            base_addr = REGISTER_CONSTANTS['DAC_CTRL_BASE'] + \
                REGISTER_CONSTANTS['DAC_CHANNEL_OFFSET'] * ch_num
            self.register_ops.write_reg(base_addr + REGISTER_CONSTANTS['DAC_OFFSET_REG'],
                                        np.int32(offset), slot)

            # 保存到Flash
            self.set_dc_offset_to_flash(ch_num, password, offset, slot)

            # 读取DC偏移值
            self.offset = self.read_dc_offset()

            logger.debug(f"DAC偏移Flash设置成功: 通道{channel_num}, 偏移{offset}")
            return True

        except Exception as e:
            logger.error(f"DAC偏移Flash设置失败: {e}")
            return False

    def read_dc_offset(self) -> np.ndarray:
        """读取DC偏移值

        Returns:
            DC偏移值数组
        """
        try:
            slot = CHANNEL_CONSTANTS['DC_OFFSET_SLOT']  # 原版使用slot1
            OFFSET_BASE_ADDR = CHANNEL_CONSTANTS['DC_OFFSET_BASE_ADDR']
            dc_offset = np.int32(
                np.zeros(CHANNEL_CONSTANTS['DC_OFFSET_CHANNELS']))

            for i in range(CHANNEL_CONSTANTS['DC_OFFSET_CHANNELS']):
                dc_offset[CHANNEL_CONSTANTS['DC_OFFSET_LAST_INDEX']-i] = np.int32(
                    self.register_ops.read_reg(OFFSET_BASE_ADDR + i, slot))

            logger.debug(f"DC偏移值读取成功: {dc_offset}")
            return dc_offset

        except Exception as e:
            logger.error(f"DC偏移值读取失败: {e}")
            return np.int32(np.zeros(CHANNEL_CONSTANTS['DC_OFFSET_CHANNELS']))

    def set_dc_offset_to_flash(self, dc_ch_num: int, password: int, offset: int, slot: str) -> bool:
        """将DC偏移值保存到Flash

        Args:
            dc_ch_num: DC通道号 (0-7)
            password: 密码
            offset: 偏移值
            slot: 板卡槽位

        Returns:
            操作是否成功
        """
        import time

        # 参数验证
        if not (0 <= dc_ch_num < CHANNEL_CONSTANTS['DC_OFFSET_CHANNELS']):
            logger.error(f"无效的DC通道号: {dc_ch_num}")
            return False

        if not ValidationUtils.validate_slot(slot):
            logger.error(f"无效的槽位: {slot}")
            return False

        try:
            # 使用常量定义寄存器地址
            CMD_REG_ADDR = CHANNEL_CONSTANTS['DC_CMD_REG_ADDR']
            OFFSET_BASE_ADDR = CHANNEL_CONSTANTS['DC_OFFSET_BASE_ADDR']
            STATUS_REG_ADDR = CHANNEL_CONSTANTS['DC_STATUS_REG_ADDR']

            # 写入命令寄存器
            self.register_ops.write_reg(CHANNEL_CONSTANTS['DC_CMD_OFFSET'] + CMD_REG_ADDR,
                                        (np.uint32(password) << CHANNEL_CONSTANTS['DC_PASSWORD_SHIFT']) + dc_ch_num, slot)

            # 写入偏移值
            self.register_ops.write_reg(
                OFFSET_BASE_ADDR + dc_ch_num, np.int32(offset), slot)

            # 执行命令
            self.register_ops.write_reg(
                0, np.uint32(CMD_REG_ADDR << CHANNEL_CONSTANTS['DC_CMD_SHIFT']) + CHANNEL_CONSTANTS['DC_CMD_EXECUTE'], slot)

            # 等待命令完成（添加超时机制）
            timeout = 5.0  # 5秒超时
            start_time = time.time()

            while True:
                if self.register_ops.read_reg(STATUS_REG_ADDR, slot) == 0:
                    break
                elif time.time() - start_time > timeout:
                    logger.error(f"DC偏移值保存到Flash超时: 通道{dc_ch_num}")
                    return False
                else:
                    time.sleep(0.01)

            logger.debug(f"DC偏移值保存到Flash成功: 通道{dc_ch_num}, 偏移{offset}")
            return True

        except Exception as e:
            logger.error(f"DC偏移值保存到Flash失败: {e}")
            return False

    def set_channel_offset(self, channel_num: int, offset: float) -> bool:
        """设置通道偏移

        Args:
            channel_num: 通道号
            offset: 偏移值

        Returns:
            操作是否成功
        """
        # 参数验证 - 使用专门的Z-PULSE通道验证
        if not ValidationUtils.validate_z_pulse_channel(channel_num):
            logger.error(f'非Z-PULSE通道：{channel_num}')
            return False

        try:
            # 计算DC偏移通道号（Z-PULSE通道8-15对应DC偏移通道0-7）
            dc_channel = channel_num - \
                CHANNEL_CONSTANTS['Z_PULSE_TO_DC_OFFSET']

            # 边界检查
            if not (0 <= dc_channel < CHANNEL_CONSTANTS['DC_OFFSET_CHANNELS']):
                logger.error(f"DC偏移通道号超出范围: {dc_channel}")
                return False

            # 获取基础偏移值
            base_offset = self.offset[dc_channel]

            # 计算最终偏移值（与原版逻辑一致）
            dc1v = 0  # 原版中未定义，默认为0
            final_offset = int(np.round(dc1v * offset + base_offset))

            # 调用dac_offset方法
            result = self.dac_offset(channel_num, final_offset)

            if result:
                logger.debug(f"通道偏移设置成功: 通道{channel_num}, 偏移{offset}")
            else:
                logger.error(f"通道偏移设置失败: 通道{channel_num}")

            return result

        except Exception as e:
            logger.error(f"通道偏移设置失败: {e}")
            return False

    def read_adc_mul_data_control(self, adc_channel_num: int, trigger_delay: int,
                                  times: int, mul_f_len: int, mul_f: List) -> bool:
        """ADC解调模块控制

        Args:
            adc_channel_num: ADC通道号，从0开始
            trigger_delay: 解调通道对应数据延时精度为ADC的采样点
            times: 解调次数，最大为163840
            mul_f_len: 解调长度最大16384
            mul_f: 频率列表，每个元素为[start_phase, frequency]

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            logger.error(f'未找到ADC通道：{adc_channel_num}')
            return False

        if len(mul_f) > CHANNEL_CONSTANTS['ADC_MUL_MAX_FREQUENCIES']:
            logger.error(f'频率数量过多: {len(mul_f)}')
            return False

        if mul_f_len > CHANNEL_CONSTANTS['ADC_MUL_MAX_LENGTH']:
            logger.error(f'读取数据超出最大长度，最大长度为1.71s')
            return False

        try:
            # 获取ADC通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 计算相位参数
            dds_phase_amp = CHANNEL_CONSTANTS['DDS_PHASE_AMP']
            adc_fs = CHANNEL_CONSTANTS['ADC_FS']

            mul_start_phase = []
            mul_f_phase = []

            for i in range(len(mul_f)):
                mul_start_phase.append(
                    np.uint32(mul_f[i][0]/2/np.pi*dds_phase_amp))
                mul_f_phase.append(np.uint32(mul_f[i][1]/adc_fs*dds_phase_amp))

            # 计算寄存器基地址
            base_addr = CHANNEL_CONSTANTS['ADC_MUL_BASE_ADDR'] + \
                CHANNEL_CONSTANTS['ADC_MUL_CHANNEL_OFFSET'] * ch_num

            # 写入控制寄存器
            self.register_ops.write_reg(base_addr + 0, 1, slot)
            self.register_ops.write_reg(
                base_addr + 1, np.uint32(trigger_delay), slot)
            self.register_ops.write_reg(
                base_addr + 2, np.uint32(times-1), slot)
            self.register_ops.write_reg(
                base_addr + 3, np.uint32(mul_f_len), slot)

            # 写入频率参数
            for i in range(len(mul_f)):
                self.register_ops.write_reg(
                    base_addr + 2*i + 4, mul_start_phase[i], slot)
                self.register_ops.write_reg(
                    base_addr + 2*i + 5, mul_f_phase[i], slot)

            # 启动解调
            self.register_ops.write_reg(base_addr + 0, 0, slot)

            logger.debug(
                f"ADC解调控制成功: 通道{adc_channel_num}, 次数{times}, 长度{mul_f_len}")
            return True

        except Exception as e:
            logger.error(f"ADC解调控制失败: {e}")
            return False

    def read_adc_mul_data(self, adc_channel_num: int, module_num: int, times: int) -> Optional[Tuple[np.ndarray, int]]:
        """ADC解调结果读取

        Args:
            adc_channel_num: ADC通道号
            module_num: 解调模块通道号，0~11
            times: 读取的解调次数

        Returns:
            解调结果数据和数据长度，其中解调未完成数据长度返回-1
            解调结果数据格式为复数二维数据，其中第一维为times，第二维为复数结果
        """
        # 参数验证
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            logger.error(f'未找到ADC通道：{adc_channel_num}')
            return None

        if module_num >= CHANNEL_CONSTANTS['ADC_MUL_MAX_MODULE_NUM']:
            logger.error(f'module_num超出范围: {module_num}')
            return None

        try:
            # 获取ADC通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return None

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 计算DMA基地址
            base_addr = CHANNEL_CONSTANTS['ADC_MUL_DMA_BASE_ADDR'] + \
                CHANNEL_CONSTANTS['ADC_MUL_DMA_CHANNEL_OFFSET'] * ch_num + \
                CHANNEL_CONSTANTS['ADC_MUL_DMA_MODULE_OFFSET'] * module_num

            # 计算寄存器基地址
            reg_base_addr = CHANNEL_CONSTANTS['ADC_MUL_BASE_ADDR'] + \
                CHANNEL_CONSTANTS['ADC_MUL_CHANNEL_OFFSET'] * ch_num

            # 检查保存状态
            save_state = self.register_ops.read_reg(reg_base_addr + 2, slot)

            if (save_state & 1) == 0:
                read_data_len = -1
                logger.debug(f'ADC解调未完成: 通道{adc_channel_num}, 模块{module_num}')
                return np.array([]), read_data_len
            else:
                read_data_len = times
                # 读取DMA数据
                adc_data = self.dma_ops.pcie_read_data64bit(
                    slot, ch_num, base_addr, read_data_len)
                if adc_data is None:
                    logger.error(
                        f"ADC解调数据读取失败: 通道{adc_channel_num}, 模块{module_num}")
                    return None

                # 转换为复数数据
                recv_data = adc_data[0] + adc_data[1] * 1j
                logger.debug(
                    f"ADC解调数据读取成功: 通道{adc_channel_num}, 模块{module_num}, 长度{read_data_len}")
                return recv_data, read_data_len

        except Exception as e:
            logger.error(f"ADC解调数据读取失败: {e}")
            return None

    def adc_mul_restart(self) -> bool:
        """ADC解调模块重启

        Returns:
            操作是否成功
        """
        try:
            for channel_id, channel_info in self.adc_channels.items():
                slot = channel_info['slot']
                ch_num = channel_info['channel_num']

                # 计算寄存器基地址
                base_addr = CHANNEL_CONSTANTS['ADC_MUL_BASE_ADDR'] + \
                    CHANNEL_CONSTANTS['ADC_MUL_CHANNEL_OFFSET'] * ch_num

                # 重启解调模块
                self.register_ops.write_reg(base_addr + 0, 1, slot)
                self.register_ops.write_reg(base_addr + 0, 0, slot)

            logger.debug("ADC解调模块重启成功")
            return True

        except Exception as e:
            logger.error(f"ADC解调模块重启失败: {e}")
            return False

    def adc_mul_decision_control(self, adc_channel_num: int, decision_in: List) -> bool:
        """ADC解调决策控制（重构adc_mul_decision_ctrl）

        Args:
            adc_channel_num: ADC通道号
            decision_in: 决策输入列表，每个元素为[旋转向量, 决策值]

        Returns:
            操作是否成功
        """
        # 参数校验
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            logger.error(f'未找到ADC通道：{adc_channel_num}')
            return False

        if len(decision_in) > CHANNEL_CONSTANTS['ADC_DECISION_MAX_COUNT']:
            logger.error(f'决策数量过多: {len(decision_in)}')
            return False

        try:
            # 获取ADC通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return False

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 计算寄存器基地址
            base_addr = CHANNEL_CONSTANTS['ADC_MUL_BASE_ADDR'] + \
                CHANNEL_CONSTANTS['ADC_MUL_CHANNEL_OFFSET'] * ch_num

            # 写入决策参数
            for i in range(len(decision_in)):
                # 计算旋转向量的实部和虚部
                revolve_vector_real = np.int32(
                    decision_in[i][0].real * CHANNEL_CONSTANTS['REVOLVE_VECTOR_SCALE'])
                revolve_vector_imag = np.int32(
                    decision_in[i][0].imag * CHANNEL_CONSTANTS['REVOLVE_VECTOR_SCALE'])

                # 计算决策值
                decision_value = np.int64(
                    decision_in[i][1].real * CHANNEL_CONSTANTS['DECISION_VALUE_SCALE'])

                # 写入寄存器
                reg_offset = CHANNEL_CONSTANTS['ADC_DECISION_BASE_OFFSET'] + \
                    i * CHANNEL_CONSTANTS['ADC_DECISION_REG_OFFSET']

                self.register_ops.write_reg(
                    base_addr + reg_offset, revolve_vector_real, slot)
                self.register_ops.write_reg(
                    base_addr + reg_offset + 1, revolve_vector_imag, slot)
                self.register_ops.write_reg(
                    base_addr + reg_offset + 2, decision_value & 0xffffffff, slot)
                self.register_ops.write_reg(base_addr + reg_offset + 3,
                                            int(decision_value >> 32) & 0xffffffff, slot)

            logger.debug(
                f"ADC解调决策控制成功: 通道{adc_channel_num}, 决策数量{len(decision_in)}")
            return True

        except Exception as e:
            logger.error(f"ADC解调决策控制失败: {e}")
            return False

    def read_adc_mul_decision_count(self, adc_channel_num: int, module_num: int):
        """读取ADC解调决策计数（重构rd_adc_mul_decision_cnt）

        Args:
            adc_channel_num: ADC通道号
            module_num: 解调模块号

        Returns:
            决策计数值，未完成时返回-1，失败时返回None
        """
        # 参数校验
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            logger.error(f'未找到ADC通道：{adc_channel_num}')
            return None

        if module_num > CHANNEL_CONSTANTS['ADC_DECISION_MAX_COUNT']:
            logger.error(f'module_num超出范围: {module_num}')
            return None

        try:
            # 获取ADC通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return None

            slot = channel_info['slot']
            ch_num = channel_info['channel_num']

            # 计算寄存器基地址
            base_addr = CHANNEL_CONSTANTS['ADC_MUL_BASE_ADDR'] + \
                CHANNEL_CONSTANTS['ADC_MUL_CHANNEL_OFFSET'] * ch_num

            # 检查保存状态
            save_state = self.register_ops.read_reg(base_addr + 2, slot)

            if (save_state & 1) == 0:
                decision_cnt = -1
                logger.debug(
                    f'ADC解调决策未完成: 通道{adc_channel_num}, 模块{module_num}')
                return decision_cnt
            else:
                # 读取决策计数
                decision_reg_offset = CHANNEL_CONSTANTS['ADC_DECISION_BASE_OFFSET'] + \
                    module_num * CHANNEL_CONSTANTS['ADC_DECISION_REG_OFFSET']
                decision_cnt = self.register_ops.read_reg(
                    base_addr + decision_reg_offset, slot)
                logger.debug(
                    f"ADC解调决策计数读取成功: 通道{adc_channel_num}, 模块{module_num}, 计数{decision_cnt}")
                return decision_cnt

        except Exception as e:
            logger.error(f"ADC解调决策计数读取失败: {e}")
            return None

    def set_rf_dac_nyquist_zone(self, nyquist_zone: int, board_num: int) -> bool:
        """设置RF DAC Nyquist区域（重构rfdac_SetNyquistZone）

        Args:
            nyquist_zone: Nyquist区域值
            board_num: 板卡号

        Returns:
            操作是否成功
        """
        try:
            # 获取板卡对应的槽位
            # 原版使用 self.da_ch[board_num*8][0]，这里需要根据实际注册的通道获取
            dac_channels = [info for info in self.dac_channels.values()
                            if info.get('channel_num', 0) // 8 == board_num]

            if not dac_channels:
                logger.error(f"未找到板卡{board_num}对应的DAC通道")
                return False

            slot = dac_channels[0]['slot']

            # 使用常量定义
            cmd_reg = CHANNEL_CONSTANTS['RF_DAC_NYQUIST_CMD_REG']
            cmd_offset = CHANNEL_CONSTANTS['RF_DAC_CMD_OFFSET']
            status_reg = CHANNEL_CONSTANTS['RF_DAC_STATUS_REG']

            # 写入命令寄存器
            self.register_ops.write_reg(
                cmd_offset + cmd_reg, np.uint32(nyquist_zone), slot)
            self.register_ops.write_reg(0, np.uint32(cmd_reg << 1) + 1, slot)

            # 等待命令完成
            import time
            timeout = 5.0  # 5秒超时
            start_time = time.time()

            while True:
                if self.register_ops.read_reg(status_reg, slot) == 0:
                    break
                elif time.time() - start_time > timeout:
                    logger.error(f"设置Nyquist区域超时: 板卡{board_num}")
                    return False
                else:
                    time.sleep(0.01)

            logger.debug(f"设置slot{board_num}为Nyquist-{nyquist_zone}成功")
            return True

        except Exception as e:
            logger.error(f"设置RF DAC Nyquist区域失败: {e}")
            return False

    def set_rf_dac_sampling(self, sampling: int, board_num: int) -> bool:
        """设置RF DAC采样率（重构rfdac_sampling）

        Args:
            sampling: 采样率
            board_num: 板卡号

        Returns:
            操作是否成功
        """
        try:
            # 获取板卡对应的槽位
            dac_channels = [info for info in self.dac_channels.values()
                            if info.get('channel_num', 0) // 8 == board_num]

            if not dac_channels:
                logger.error(f"未找到板卡{board_num}对应的DAC通道")
                return False

            slot = dac_channels[0]['slot']

            # 使用常量定义
            cmd_reg = CHANNEL_CONSTANTS['RF_DAC_SAMPLING_CMD_REG']
            cmd_offset = CHANNEL_CONSTANTS['RF_DAC_CMD_OFFSET']
            status_reg = CHANNEL_CONSTANTS['RF_DAC_STATUS_REG']
            sampling_status_reg = CHANNEL_CONSTANTS['RF_DAC_SAMPLING_STATUS_REG']
            sampling_modulo = CHANNEL_CONSTANTS['RF_DAC_SAMPLING_MODULO']

            # 写入命令寄存器
            self.register_ops.write_reg(
                cmd_offset + cmd_reg, np.uint32(sampling), slot)
            self.register_ops.write_reg(0, np.uint32(cmd_reg << 1) + 1, slot)

            # 等待命令完成
            import time
            timeout = 5.0  # 5秒超时
            start_time = time.time()

            while True:
                if self.register_ops.read_reg(status_reg, slot) == 0:
                    break
                elif time.time() - start_time > timeout:
                    logger.error(f"设置采样率超时: 板卡{board_num}")
                    return False
                else:
                    time.sleep(0.01)

            # 验证采样率设置
            sampling_set = self.register_ops.read_reg(
                sampling_status_reg, slot)
            if sampling_set % sampling_modulo == 0 and sampling == sampling_set:
                logger.debug(f"设置slot{board_num}采样率{sampling}成功")
                return True
            else:
                logger.error(
                    f"设置slot{board_num}采样率{sampling}失败！实际采样率为: {sampling_set}, 采样率不支持！！！")
                return False

        except Exception as e:
            logger.error(f"设置RF DAC采样率失败: {e}")
            return False

    def adc_coef(self, adc_channel_num: int, password: int) -> bool:
        """ADC系数设置（重构adc_coef）

        Args:
            adc_channel_num: ADC通道号
            password: 密码

        Returns:
            操作是否成功
        """
        # 参数验证
        if not ValidationUtils.validate_adc_channel(adc_channel_num):
            logger.error(f'未找到ADC通道：{adc_channel_num}')
            return False

        try:
            # 获取ADC通道信息
            channel_info = self._get_adc_channel_info(adc_channel_num)
            if not channel_info:
                logger.error(f"未找到ADC通道: {adc_channel_num}")
                return False

            slot = channel_info['slot']

            # 使用常量定义
            cmd_reg_addr = REGISTER_CONSTANTS['ADC_COEF_CMD_REG']
            cmd_offset = REGISTER_CONSTANTS['CMD_OFFSET']
            status_reg = REGISTER_CONSTANTS['STATUS_REG']

            # 写入命令寄存器
            self.register_ops.write_reg(
                cmd_offset + cmd_reg_addr,
                (np.uint32(password) << 3) + adc_channel_num, slot)

            # 执行命令
            self.register_ops.write_reg(
                0, np.uint32(cmd_reg_addr << 1) + 1, slot)

            # 等待命令完成（添加超时机制）
            import time
            timeout = 5.0  # 5秒超时
            start_time = time.time()

            while True:
                if self.register_ops.read_reg(status_reg, slot) == 0:
                    break
                elif time.time() - start_time > timeout:
                    logger.error(f"ADC系数设置超时: 通道{adc_channel_num}")
                    return False
                else:
                    time.sleep(0.01)

            logger.debug(f"ADC系数设置成功: 通道{adc_channel_num}")
            return True

        except Exception as e:
            logger.error(f"ADC系数设置失败: {e}")
            return False

    def register_dac_channel(self, channel_id: int, slot: str, channel_num: int) -> bool:
        """注册DAC通道

        Args:
            channel_id: 通道ID
            slot: 板卡槽位
            channel_num: 通道号

        Returns:
            注册是否成功
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_dac_channel(channel_num):
            raise ValidationError("channel_num", channel_num,
                                  f"无效的DAC通道号: {channel_num}")

        if not isinstance(channel_id, int) or channel_id < 0:
            raise ValidationError("channel_id", channel_id, "通道ID必须是非负整数")

        try:
            channel_info = {
                'slot': slot,
                'channel_num': channel_num,
                'enabled': False
            }
            self.dac_channels[channel_id] = channel_info

            # 优化：维护反向索引
            self._dac_channel_by_num[channel_num] = channel_info

            logger.debug(
                f"DAC通道注册成功: ID{channel_id}, 槽位{slot}, 通道{channel_num}")
            return True
        except Exception as e:
            logger.error(f"DAC通道注册失败: {e}")
            return False

    def register_adc_channel(self, channel_id: int, slot: str, channel_num: int) -> bool:
        """注册ADC通道

        Args:
            channel_id: 通道ID
            slot: 板卡槽位
            channel_num: 通道号

        Returns:
            注册是否成功
        """
        if not ValidationUtils.validate_slot(slot):
            raise ValidationError(f"无效的槽位: {slot}")

        if not ValidationUtils.validate_adc_channel(channel_num):
            raise ValidationError("channel_num", channel_num,
                                  f"无效的ADC通道号: {channel_num}")

        if not isinstance(channel_id, int) or channel_id < 0:
            raise ValidationError("channel_id", channel_id, "通道ID必须是非负整数")

        try:
            self.adc_channels[channel_id] = {
                'slot': slot,
                'channel_num': channel_num,
                'enabled': False
            }
            logger.debug(
                f"ADC通道注册成功: ID{channel_id}, 槽位{slot}, 通道{channel_num}")
            return True
        except Exception as e:
            logger.error(f"ADC通道注册失败: {e}")
            return False

    def _clear_channel_indices(self):
        """清理通道索引缓存"""
        self._dac_channel_by_num.clear()
        self._adc_channel_by_num.clear()

        # 重新构建索引
        for channel_info in self.dac_channels.values():
            self._dac_channel_by_num[channel_info['channel_num']
                                     ] = channel_info

        for channel_info in self.adc_channels.values():
            self._adc_channel_by_num[channel_info['channel_num']
                                     ] = channel_info

    def get_dac_channels_by_nums(self, channel_nums: List[int]) -> Dict[int, Dict]:
        """批量获取DAC通道信息

        Args:
            channel_nums: DAC通道号列表

        Returns:
            通道信息字典，key为channel_num，value为通道信息
        """
        result = {}
        for channel_num in channel_nums:
            channel_info = self._dac_channel_by_num.get(channel_num)
            if channel_info:
                result[channel_num] = {
                    'slot': channel_info['slot'],
                    'channel_num': channel_info['channel_num']
                }
        return result

    def get_all_dac_channels(self) -> Dict[int, Dict]:
        """获取所有DAC通道信息

        Returns:
            所有DAC通道信息字典
        """
        return {
            channel_num: {
                'slot': info['slot'],
                'channel_num': info['channel_num']
            }
            for channel_num, info in self._dac_channel_by_num.items()
        }

    def get_channel_info(self, channel_id: int, channel_type: str = 'dac') -> Optional[Dict]:
        """获取通道信息

        Args:
            channel_id: 通道ID
            channel_type: 通道类型 ('dac' 或 'adc')

        Returns:
            通道信息，失败时返回None
        """
        try:
            if channel_type.lower() == 'dac':
                return self.dac_channels.get(channel_id)
            elif channel_type.lower() == 'adc':
                return self.adc_channels.get(channel_id)
            else:
                raise ValidationError(
                    "channel_type", channel_type, "通道类型必须是 'dac' 或 'adc'")
        except Exception as e:
            logger.error(f"获取通道信息失败: {e}")
            return None

    def initialize_channels_from_boards(self, board_info: Dict) -> bool:
        """根据板卡信息自动初始化通道

        Args:
            board_info: 板卡信息字典

        Returns:
            初始化是否成功
        """
        try:
            logger.info("开始根据板卡信息初始化通道...")

            # 清空现有通道信息
            self.dac_channels.clear()
            self.adc_channels.clear()

            # 遍历板卡信息
            for board_id, board_data in board_info.items():
                if not board_data.get('is_valid', False):
                    continue

                slot = board_data['slot']
                board_type = board_data['type']

                # 根据板卡类型配置通道
                if board_type == '0x22':  # DAC板卡
                    self._configure_dac_board(board_id, slot)

            logger.info(
                f"通道初始化完成: DAC通道{len(self.dac_channels)}, ADC通道{len(self.adc_channels)}")
            return True

        except Exception as e:
            logger.error(f"通道初始化失败: {e}")
            return False

    def _configure_dac_board(self, board_id: int, slot: str):
        """配置DAC板卡通道"""
        from constants import CHANNEL_CONSTANTS
        channels_per_board = CHANNEL_CONSTANTS['DA_CHANNELS_PER_BOARD']

        for ch_i in range(channels_per_board):
            channel_id = board_id * channels_per_board + ch_i
            self.register_dac_channel(
                channel_id=channel_id,
                slot=slot,
                channel_num=ch_i
            )
            logger.debug(f"注册DAC通道: ID{channel_id}, 槽位{slot}, 通道{ch_i}")

    def get_channel_status(self, channel_id: int, channel_type: str = 'dac') -> Optional[Dict]:
        """获取通道状态

        Args:
            channel_id: 通道ID
            channel_type: 通道类型 ('dac' 或 'adc')

        Returns:
            通道状态信息，失败时返回None
        """
        try:
            channel_info = self.get_channel_info(channel_id, channel_type)
            if channel_info is None:
                return None

            status_info = {
                'channel_id': channel_id,
                'channel_type': channel_type,
                'slot': channel_info['slot'],
                'channel_num': channel_info['channel_num'],
                'enabled': channel_info['enabled'],
                'registered': True
            }

            logger.debug(f"通道状态查询完成: {status_info}")
            return status_info

        except Exception as e:
            logger.error(f"通道状态查询失败: {e}")
            return None
