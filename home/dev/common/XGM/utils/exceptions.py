# -*- coding: utf-8 -*-
"""
错误处理模块 - 设备驱动异常定义
"""


class FpgaDevError(Exception):
    """FPGA设备基础异常"""

    def __init__(self, message: str = "", error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code is not None:
            return f"[{self.error_code}] {self.message}"
        return self.message


class BoardNotFoundError(FpgaDevError):
    """板卡未找到异常"""

    def __init__(self, slot: str = "", message: str = ""):
        if not message:
            message = f"未找到板卡: {slot}" if slot else "板卡未找到"
        super().__init__(message, error_code=1001)


class RegisterAccessError(FpgaDevError):
    """寄存器访问异常"""

    def __init__(self, addr: int = None, slot: str = "", message: str = ""):
        if not message:
            if addr is not None and slot:
                message = f"寄存器访问失败: 0x{addr:X} (槽位: {slot})"
            elif addr is not None:
                message = f"寄存器访问失败: 0x{addr:X}"
            else:
                message = "寄存器访问失败"
        super().__init__(message, error_code=1002)


class ValidationError(FpgaDevError):
    """参数验证异常"""

    def __init__(self, param_name: str = "", value=None, message: str = ""):
        if not message:
            if param_name and value is not None:
                message = f"参数验证失败: {param_name} = {value}"
            elif param_name:
                message = f"参数验证失败: {param_name}"
            else:
                message = "参数验证失败"
        super().__init__(message, error_code=1003)


# FeatureError 已删除 - Features系统已移除


class HardwareError(FpgaDevError):
    """硬件错误异常"""

    def __init__(self, device: str = "", operation: str = "", message: str = ""):
        if not message:
            if device and operation:
                message = f"硬件错误: {device} {operation}"
            elif device:
                message = f"硬件错误: {device}"
            else:
                message = "硬件错误"
        super().__init__(message, error_code=1005)


class ConfigurationError(FpgaDevError):
    """配置错误异常"""

    def __init__(self, config_item: str = "", message: str = ""):
        if not message:
            if config_item:
                message = f"配置错误: {config_item}"
            else:
                message = "配置错误"
        super().__init__(message, error_code=1006)


class CommunicationError(FpgaDevError):
    """通信错误异常"""

    def __init__(self, target: str = "", message: str = ""):
        if not message:
            if target:
                message = f"通信错误: {target}"
            else:
                message = "通信错误"
        super().__init__(message, error_code=1007)


class TimeoutError(FpgaDevError):
    """超时错误异常"""

    def __init__(self, operation: str = "", timeout: float = None, message: str = ""):
        if not message:
            if operation and timeout is not None:
                message = f"操作超时: {operation} (超时时间: {timeout}s)"
            elif operation:
                message = f"操作超时: {operation}"
            else:
                message = "操作超时"
        super().__init__(message, error_code=1008)


# 错误代码映射
ERROR_CODES = {
    1001: "板卡未找到",
    1002: "寄存器访问失败",
    1003: "参数验证失败",
    1004: "功能操作失败",  # 原FeatureError，已移除
    1005: "硬件错误",
    1006: "配置错误",
    1007: "通信错误",
    1008: "操作超时",
}


def get_error_description(error_code: int) -> str:
    """获取错误代码描述"""
    return ERROR_CODES.get(error_code, "未知错误")


def handle_device_error(func):
    """设备错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FpgaDevError:
            raise
        except Exception as e:
            raise HardwareError(message=f"设备操作异常: {str(e)}")
    return wrapper
