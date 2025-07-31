# -*- coding: utf-8 -*-
"""
单例模式混入类
"""

import threading
import logging

logger = logging.getLogger('FpgaDev')


class SingletonMixin:
    """单例模式混入类"""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def get_instance(cls):
        """获取单例实例的推荐方法"""
        return cls()

    @classmethod
    def is_initialized(cls):
        """检查设备是否已初始化"""
        return cls._initialized

    @classmethod
    def reset_instance(cls):
        """重置单例实例（用于测试或重新初始化）"""
        with cls._lock:
            if cls._instance is not None:
                if hasattr(cls._instance, '_cleanup'):
                    cls._instance._cleanup()
                cls._instance = None
            cls._initialized = False
            logger.info("单例实例已重置")

    @classmethod
    def safe_get_instance(cls, reset_if_needed=False):
        """安全获取单例实例

        Args:
            reset_if_needed: 如果设备已初始化但需要重新初始化，是否重置

        Returns:
            单例实例

        Raises:
            RuntimeError: 当设备初始化失败时
        """
        try:
            return cls.get_instance()
        except RuntimeError as e:
            if "可能已经初始化" in str(e) and reset_if_needed:
                logger.info("检测到设备已初始化，正在重置...")
                cls.reset_instance()
                return cls._create_instance_without_version()
            else:
                raise

    @classmethod
    def _create_instance_without_version(cls):
        """创建实例但不显示版本信息（用于重置后的重新初始化）"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(cls, cls).__new__(cls)

        # 避免重复初始化
        if cls._initialized:
            return cls._instance

        # 线程锁，确保线程安全
        with cls._lock:
            if cls._initialized:
                return cls._instance

            try:
                # 不显示版本信息，直接初始化设备
                cls._instance._initialize_device()
                cls._initialized = True
                logger.info("设备重新初始化成功")
                return cls._instance
            except Exception as e:
                cls._initialized = False
                raise
