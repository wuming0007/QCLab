# -*- coding: utf-8 -*-
"""
XGM模块测试配置

定义测试相关的常量、设置和工具函数。
"""

import os
import sys
from pathlib import Path

# 测试配置常量
TEST_CONFIG = {
    # 测试超时设置
    'DEFAULT_TIMEOUT': 30.0,  # 默认测试超时时间（秒）
    'SHORT_TIMEOUT': 5.0,     # 短测试超时时间（秒）
    'LONG_TIMEOUT': 60.0,     # 长测试超时时间（秒）
    
    # 测试数据设置
    'TEST_DATA_SIZE': 1024,   # 测试数据大小
    'TEST_CHANNEL_COUNT': 4,  # 测试通道数量
    'TEST_SLOT_COUNT': 2,     # 测试槽位数量
    
    # 测试模式设置
    'VERBOSE_MODE': True,     # 详细输出模式
    'DEBUG_MODE': False,      # 调试模式
    'SKIP_SLOW_TESTS': False, # 跳过慢速测试
    
    # 测试文件路径
    'TEST_DATA_DIR': 'test_data',  # 测试数据目录
    'TEST_LOG_DIR': 'test_logs',   # 测试日志目录
    'TEST_RESULTS_DIR': 'test_results',  # 测试结果目录
}

# 测试类别定义
TEST_CATEGORIES = {
    'core': {
        'name': '核心模块测试',
        'description': '测试核心功能模块（DMA、通道控制、串口通信、触发控制、板卡管理）',
        'modules': [
            'test_dma',
            'test_channel',
            'test_serial',
            'test_trigger',
            'test_board',
        ]
    },
    'validation': {
        'name': '验证测试',
        'description': '验证重构和优化的正确性',
        'modules': [
            'test_validation',
        ]
    }
}

# 测试环境设置
def setup_test_environment():
    """设置测试环境"""
    # 创建测试目录
    test_dirs = [
        TEST_CONFIG['TEST_DATA_DIR'],
        TEST_CONFIG['TEST_LOG_DIR'],
        TEST_CONFIG['TEST_RESULTS_DIR']
    ]
    
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    # 设置环境变量
    os.environ['XGM_TEST_MODE'] = '1'
    os.environ['XGM_VERBOSE'] = str(TEST_CONFIG['VERBOSE_MODE'])
    os.environ['XGM_DEBUG'] = str(TEST_CONFIG['DEBUG_MODE'])

def cleanup_test_environment():
    """清理测试环境"""
    # 清理临时文件
    import shutil
    
    temp_dirs = [
        TEST_CONFIG['TEST_DATA_DIR'],
        TEST_CONFIG['TEST_LOG_DIR'],
        TEST_CONFIG['TEST_RESULTS_DIR']
    ]
    
    for dir_name in temp_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)

# 测试工具函数
def get_test_data_path(filename: str) -> Path:
    """获取测试数据文件路径
    
    Args:
        filename: 文件名
        
    Returns:
        完整的文件路径
    """
    return Path(TEST_CONFIG['TEST_DATA_DIR']) / filename

def get_test_log_path(filename: str) -> Path:
    """获取测试日志文件路径
    
    Args:
        filename: 文件名
        
    Returns:
        完整的文件路径
    """
    return Path(TEST_CONFIG['TEST_LOG_DIR']) / filename

def get_test_results_path(filename: str) -> Path:
    """获取测试结果文件路径
    
    Args:
        filename: 文件名
        
    Returns:
        完整的文件路径
    """
    return Path(TEST_CONFIG['TEST_RESULTS_DIR']) / filename

# 测试装饰器
def skip_if_slow_test(func):
    """跳过慢速测试的装饰器"""
    def wrapper(*args, **kwargs):
        if TEST_CONFIG['SKIP_SLOW_TESTS']:
            print(f"⏭️  跳过慢速测试: {func.__name__}")
            return
        return func(*args, **kwargs)
    return wrapper

def timeout_test(timeout_seconds: float = None):
    """测试超时装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import signal
            
            timeout = timeout_seconds or TEST_CONFIG['DEFAULT_TIMEOUT']
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"测试超时: {func.__name__}")
            
            # 设置超时信号
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消超时
                return result
            except TimeoutError:
                print(f"⏰ 测试超时: {func.__name__}")
                raise
            finally:
                signal.alarm(0)
        
        return wrapper
    return decorator

# 测试数据生成器
def generate_test_data(size: int = None, data_type: str = 'int32'):
    """生成测试数据
    
    Args:
        size: 数据大小
        data_type: 数据类型
        
    Returns:
        测试数据数组
    """
    import numpy as np
    
    size = size or TEST_CONFIG['TEST_DATA_SIZE']
    
    if data_type == 'int32':
        return np.random.randint(-1000, 1000, size, dtype=np.int32)
    elif data_type == 'int16':
        return np.random.randint(-1000, 1000, size, dtype=np.int16)
    elif data_type == 'float32':
        return np.random.uniform(-1.0, 1.0, size).astype(np.float32)
    else:
        raise ValueError(f"不支持的数据类型: {data_type}")

def generate_test_channels(count: int = None):
    """生成测试通道信息
    
    Args:
        count: 通道数量
        
    Returns:
        通道信息列表
    """
    count = count or TEST_CONFIG['TEST_CHANNEL_COUNT']
    
    channels = []
    for i in range(count):
        channels.append({
            'id': i,
            'slot': f'slot{i % TEST_CONFIG['TEST_SLOT_COUNT']}',
            'channel_num': i,
            'type': 'dac' if i % 2 == 0 else 'adc'
        })
    
    return channels 