# -*- coding: utf-8 -*-
"""
日志配置工具
"""

import logging
import sys


def setup_logging(level=logging.INFO, log_file=None):
    """配置日志系统

    Args:
        level: 日志级别
        log_file: 日志文件路径，如果为None则只输出到控制台

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 配置根日志记录器
    logger = logging.getLogger('FpgaDev')
    logger.setLevel(level)

    # 清除现有的处理器
    logger.handlers.clear()

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
