# -*- coding: utf-8 -*-
"""
设备控制器 - 整合所有FPGA操作模块，使用FFI包装器
"""

import logging
from typing import Optional, Dict
from .board_management import BoardManagement
from .register_operations import RegisterOperations
from .dma_operations import DmaOperations
from .channel_control import ChannelControl
from .trigger_control import TriggerControl
from .serial_communications import SerialCommunications
from .ffi_wrapper import FFIWrapper


logger = logging.getLogger(__name__)


class DeviceController:
    """设备控制器 - 整合所有FPGA操作模块，使用FFI包装器"""

    def __init__(self, fpga_dll):
        """初始化设备控制器

        Args:
            fpga_dll: FPGA DLL对象
        """
        # 创建FFI包装器作为核心组件
        self.ffi = FFIWrapper(fpga_dll)

        # 初始化各个模块，通过board_mgmt共享FFI包装器
        self.board_mgmt = BoardManagement(self.ffi)
        self.register_ops = RegisterOperations(self.board_mgmt)
        self.dma_ops = DmaOperations(self.board_mgmt)
        self.channel_ctrl = ChannelControl(self.board_mgmt)
        self.serial_comm = SerialCommunications(self.register_ops)
        self.trigger_ctrl = TriggerControl(self.serial_comm)

    def initialize_device(self) -> bool:
        """初始化设备

        Returns:
            初始化是否成功
        """
        try:
            logger.info("开始初始化设备...")

            # 初始化板卡
            if not self.board_mgmt.initialize_boards():
                logger.error("板卡初始化失败")
                return False

            # 初始化通道信息
            self._initialize_channel_info()

            # 读取固件版本信息
            self.read_firmware_versions()

            logger.info("设备初始化完成")
            return True

        except Exception as e:
            logger.error(f"设备初始化失败: {e}")
            return False

    def _initialize_channel_info(self):
        """协调通道和板卡初始化"""
        try:
            logger.info("开始协调通道和板卡初始化...")

            # 获取板卡信息
            board_info = self.board_mgmt.get_board_info()
            if not board_info:
                logger.warning("未获取到板卡信息，跳过通道初始化")
                return

            # 根据板卡信息初始化通道
            if not self.channel_ctrl.initialize_channels_from_boards(board_info):
                logger.error("通道初始化失败")
                return

            # 打开所有板卡
            if not self.board_mgmt.open_all_boards():
                logger.warning("部分板卡打开失败")

            logger.info("通道和板卡初始化协调完成")

        except Exception as e:
            logger.error(f"通道和板卡初始化协调失败: {e}")
            raise

    def get_device_info(self) -> Dict:
        """获取设备信息

        Returns:
            设备信息字典
        """
        try:
            return {
                'board_info': self.board_mgmt.get_board_info(),
                'board_number': self.board_mgmt.get_board_number(),
                'board_slots': self.board_mgmt.get_board_slots(),
                'board_types': self.board_mgmt.get_board_types(),
                'valid_boards': self.board_mgmt.get_valid_boards(),
                'all_board_status': self.board_mgmt.get_all_board_status()
            }
        except Exception as e:
            logger.error(f"获取设备信息失败: {e}")
            return {}

    def open_board(self, slot: str) -> bool:
        """打开指定槽位的板卡

        Args:
            slot: 板卡槽位

        Returns:
            操作是否成功
        """
        return self.board_mgmt.open_board(slot)

    def close_board(self, slot: str) -> bool:
        """关闭指定槽位的板卡

        Args:
            slot: 板卡槽位

        Returns:
            操作是否成功
        """
        return self.board_mgmt.close_board(slot)

    def read_register(self, addr: int, slot: str) -> int:
        """读取寄存器

        Args:
            addr: 寄存器地址
            slot: 板卡槽位

        Returns:
            寄存器值
        """
        return self.register_ops.read_reg(addr, slot)

    def write_register(self, addr: int, data: int, slot: str = '') -> int:
        """写入寄存器

        Args:
            addr: 寄存器地址
            data: 要写入的数据
            slot: 板卡槽位

        Returns:
            操作结果
        """
        return self.register_ops.write_reg(addr, data, slot)

    def read_firmware_version(self, slot: str) -> Optional[Dict]:
        """读取固件版本信息

        Args:
            slot: 板卡槽位

        Returns:
            固件版本信息字典
        """
        try:
            # 固件版本寄存器地址
            firmware_registers = {
                'PL_VERSION_MAJOR': 0x100,
                'PL_VERSION_MINOR': 0x101,
                'PS_VERSION_MAJOR': 0x102,
                'PS_VERSION_MINOR': 0x103
            }

            version_info = {}
            for name, addr in firmware_registers.items():
                try:
                    value = self.register_ops.read_reg(addr, slot)
                    version_info[name] = value
                except Exception as e:
                    logger.warning(f"读取固件版本寄存器 {name} 失败: {e}")
                    version_info[name] = None

            # 格式化版本信息
            if version_info['PL_VERSION_MAJOR'] is not None and version_info['PL_VERSION_MINOR'] is not None:
                pl_version = f"V{version_info['PL_VERSION_MAJOR'] / 10:.1f}-{version_info['PL_VERSION_MINOR']}"
            else:
                pl_version = "Unknown"

            if version_info['PS_VERSION_MAJOR'] is not None and version_info['PS_VERSION_MINOR'] is not None:
                ps_version = f"V{version_info['PS_VERSION_MAJOR'] / 10:.1f}-{version_info['PS_VERSION_MINOR']}"
            else:
                ps_version = "Unknown"

            return {
                'pl_version': pl_version,
                'ps_version': ps_version,
                'slot': slot,
                'raw_values': version_info
            }

        except Exception as e:
            logger.error(f"读取固件版本信息失败: {e}")
            return None

    def dma_write(self, slot: str, addr: int, data, size: Optional[int] = None) -> int:
        """DMA写入数据（可指定自定义大小）

        Args:
            slot: 板卡槽位
            addr: 目标地址
            data: 要写入的数据
            size: 写入大小

        Returns:
            操作结果
        """
        return self.dma_ops.dma_write(slot, addr, data, size)

    def dma_read(self, bus_id: int, addr: int, size: int):
        """DMA读取数据

        Args:
            bus_id: 总线ID
            addr: 源地址
            size: 读取大小

        Returns:
            读取的数据
        """
        return self.dma_ops.dma_read(bus_id, addr, size)

    def pcie_write_data(self, slot: str, channel_num: int, data) -> int:
        """PCIe写入数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            data: 要写入的数据

        Returns:
            操作结果，0表示成功
        """
        return self.dma_ops.pcie_write_data(slot, channel_num, data)

    def pcie_read_data(self, slot: str, channel_num: int, data_len: int):
        """PCIe读取数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            data_len: 数据长度

        Returns:
            读取的数据
        """
        return self.dma_ops.pcie_read_data(slot, channel_num, data_len)

    def pcie_write_data_64bit(self, slot: str, channel_num: int, addr: int, data) -> int:
        """PCIe写入64位数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            addr: 目标地址
            data: 要写入的64位数据

        Returns:
            操作结果，0表示成功
        """
        return self.dma_ops.pcie_write_data_64bit(slot, channel_num, addr, data)

    def pcie_read_data_64bit(self, slot: str, channel_num: int, addr: int, data_len: int):
        """PCIe读取64位数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            addr: 源地址
            data_len: 数据长度

        Returns:
            读取的64位数据列表
        """
        return self.dma_ops.pcie_read_data_64bit(slot, channel_num, addr, data_len)

    def pcie_read_data_8bit(self, slot: str, channel_num: int, addr: int, data_len: int):
        """PCIe读取8位数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            addr: 源地址
            data_len: 数据长度

        Returns:
            读取的8位数据数组
        """
        return self.dma_ops.pcie_read_data_8bit(slot, channel_num, addr, data_len)

    def return_data(self, addr: int, slot: str):
        """返回DMA数据 (原版实现)

        Args:
            addr: DMA地址
            slot: 板卡槽位

        Returns:
            DMA数据数组
        """
        return self.board_mgmt.return_data(addr, slot)

    def return_data_by_size(self, dma_addr: int, size: int, pcie_dma_rd_len: int, slot: str):
        """按大小返回DMA数据

        Args:
            dma_addr: DMA地址
            size: 数据大小
            pcie_dma_rd_len: PCIe DMA读取长度
            slot: 板卡槽位

        Returns:
            (数据缓冲区, 状态码) 元组
        """
        return self.board_mgmt.return_data_by_size(dma_addr, size, pcie_dma_rd_len, slot)

    def write_dac_data(self, slot: str, channel_num: int, dac_data) -> bool:
        """写入DAC数据

        Args:
            slot: 板卡槽位
            channel_num: 通道号
            dac_data: DAC数据

        Returns:
            操作是否成功
        """
        return self.channel_ctrl.write_dac_data(slot, channel_num, dac_data)

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
            dac_en: DAC使能

        Returns:
            操作是否成功
        """
        return self.channel_ctrl.dac_channel_control(
            slot, channel_num, replay_len, trigger_delay,
            replay_times, replay_continue, dac_en)

    def read_adc_data(self, adc_channel_num: int, times: int, save_len: int):
        """读取ADC数据

        Args:
            adc_channel_num: ADC通道号
            times: 读取次数
            save_len: 保存长度

        Returns:
            ADC数据
        """
        return self.channel_ctrl.read_adc_data(adc_channel_num, times, save_len)

    def reset_device(self) -> bool:
        """重置设备

        Returns:
            操作是否成功
        """
        try:
            logger.info("开始重置设备...")

            # 重置板卡状态
            if not self.board_mgmt.reset_boards():
                logger.error("板卡重置失败")
                return False

            logger.info("设备重置完成")
            return True

        except Exception as e:
            logger.error(f"设备重置失败: {e}")
            return False

    def read_firmware_versions(self):
        """读取所有板卡的固件版本信息"""
        try:
            for slot in self.board_mgmt.get_board_slots():
                slot_str = f"slot{slot}"
                version_info = self.read_firmware_version(slot_str)
                if version_info:
                    logger.info(
                        f"板卡 {slot_str} 固件版本: PL={version_info['pl_version']}, PS={version_info['ps_version']}")
                else:
                    logger.warning(f"板卡 {slot_str} 固件版本读取失败")
        except Exception as e:
            logger.error(f"读取固件版本信息失败: {e}")

    def get_board_status(self, slot: str) -> Optional[Dict]:
        """获取板卡状态

        Args:
            slot: 板卡槽位

        Returns:
            板卡状态信息
        """
        return self.board_mgmt.get_board_status(slot)

    def is_initialized(self) -> bool:
        """检查设备是否已初始化

        Returns:
            是否已初始化
        """
        return self.board_mgmt.is_initialized()

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
        """
        return self.trigger_ctrl.trigger_control(trigger_source, trigger_us, trigger_num, trigger_continue)

    def trigger_close(self) -> bool:
        """关闭触发

        Returns:
            操作是否成功
        """
        return self.trigger_ctrl.trigger_close()

    def get_trigger_status(self) -> Optional[Dict]:
        """获取触发状态

        Returns:
            触发状态信息
        """
        return self.trigger_ctrl.get_trigger_status()

    def serial_write(self, data, slot: str) -> int:
        """串口写入数据

        Args:
            data: 要写入的数据
            slot: 板卡槽位

        Returns:
            写入的数据长度
        """
        return self.serial_comm.serial_write(data, slot)

    def serial_read(self, slot: str, timeout: float):
        """串口读取数据

        Args:
            slot: 板卡槽位
            timeout: 超时时间（秒）

        Returns:
            读取的数据
        """
        return self.serial_comm.serial_read(slot, timeout)

    def serial_send_cmd(self, send_data, slot: str = 'slot0'):
        """串口发送命令

        Args:
            send_data: 要发送的命令数据
            slot: 板卡槽位（默认为'slot0'）

        Returns:
            接收到的响应数据
        """
        return self.serial_comm.serial_send_cmd(send_data, slot)

    def serial_reset_input_buffer(self, slot: str) -> None:
        """串口重置输入缓冲区

        Args:
            slot: 板卡槽位
        """
        return self.serial_comm.serial_reset_input_buffer(slot)

    def get_serial_status(self, slot: str) -> Optional[Dict]:
        """获取串口状态

        Args:
            slot: 板卡槽位

        Returns:
            串口状态信息
        """
        return self.serial_comm.get_serial_status(slot)

    def get_dma_status(self, slot: str) -> Optional[Dict]:
        """获取DMA状态

        Args:
            slot: 板卡槽位

        Returns:
            DMA状态信息
        """
        return self.dma_ops.get_dma_status(slot)

    def wait_for_dma_ready(self, slot: str, timeout: float = 5.0) -> bool:
        """等待DMA就绪

        Args:
            slot: 板卡槽位
            timeout: 超时时间（秒）

        Returns:
            是否就绪
        """
        return self.dma_ops.wait_for_dma_ready(slot, timeout)

    # 通道控制方法
    def register_dac_channel(self, channel_id: int, slot: str, channel_num: int) -> bool:
        """注册DAC通道

        Args:
            channel_id: 通道ID
            slot: 板卡槽位
            channel_num: 通道号

        Returns:
            注册是否成功
        """
        return self.channel_ctrl.register_dac_channel(channel_id, slot, channel_num)

    def register_adc_channel(self, channel_id: int, slot: str, channel_num: int) -> bool:
        """注册ADC通道

        Args:
            channel_id: 通道ID
            slot: 板卡槽位
            channel_num: 通道号

        Returns:
            注册是否成功
        """
        return self.channel_ctrl.register_adc_channel(channel_id, slot, channel_num)

    def get_channel_status(self, channel_id: int, channel_type: str = 'dac') -> Optional[Dict]:
        """获取通道状态

        Args:
            channel_id: 通道ID
            channel_type: 通道类型 ('dac' 或 'adc')

        Returns:
            通道状态信息
        """
        return self.channel_ctrl.get_channel_status(channel_id, channel_type)
