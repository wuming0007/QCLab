# -*- coding: utf-8 -*-
"""
DLL包装器
"""

import ctypes
from pathlib import Path
import logging

logger = logging.getLogger('FpgaDev')


class FpgaDevDll:
    """FPGA设备DLL包装器"""

    def __init__(self):
        """初始化DLL包装器"""
        self.dll = None
        self._load_dll()

    def _load_dll(self):
        """加载DLL文件"""
        try:
            # 获取当前文件所在目录
            current_dir = Path(__file__).parent.parent
            dll_path = current_dir / "pcie_driver.dll"

            if not dll_path.exists():
                raise FileNotFoundError(f"DLL文件不存在: {dll_path}")

            # 加载DLL
            self.dll = ctypes.CDLL(str(dll_path))
            logger.info(f"DLL加载成功: {dll_path}")

        except Exception as e:
            logger.error(f"DLL加载失败: {e}")
            raise RuntimeError(f"无法加载DLL文件: {e}")

    def __del__(self):
        """析构函数"""
        if hasattr(self, 'dll') and self.dll:
            try:
                # 释放DLL资源
                pass
            except Exception as e:
                logger.warning(f"DLL资源释放失败: {e}")
