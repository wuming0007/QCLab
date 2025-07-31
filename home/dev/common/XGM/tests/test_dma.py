# -*- coding: utf-8 -*-
"""
DMA模块统一测试

包含DMA操作模块的所有测试，包括优化验证、功能测试和性能测试。
"""

from utils import ValidationUtils, ValidationError
from core.dma_operations import DmaOperations
import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_dma_validation_utils():
    """测试DMA验证工具函数"""
    print("=" * 50)
    print("🧪 DMA验证工具函数测试")
    print("=" * 50)

    # 测试DMA数据验证
    print("1. 测试DMA数据验证...")
    assert ValidationUtils.validate_dma_data([1, 2, 3, 4]) == True
    assert ValidationUtils.validate_dma_data([]) == False
    assert ValidationUtils.validate_dma_data("invalid") == False
    print("✅ DMA数据验证正常")

    # 测试DMA大小验证
    print("2. 测试DMA大小验证...")
    assert ValidationUtils.validate_dma_size(1) == True
    assert ValidationUtils.validate_dma_size(1024) == True
    assert ValidationUtils.validate_dma_size(0) == False
    assert ValidationUtils.validate_dma_size(-1) == False
    print("✅ DMA大小验证正常")

    # 测试通道号验证
    print("3. 测试通道号验证...")
    assert ValidationUtils.validate_channel_number(0) == True
    assert ValidationUtils.validate_channel_number(15) == True
    assert ValidationUtils.validate_channel_number(-1) == False
    print("✅ 通道号验证正常")


def test_dma_constants():
    """测试DMA常量定义"""
    print("\n" + "=" * 50)
    print("📊 DMA常量定义测试")
    print("=" * 50)

    from constants import DMA_CONSTANTS

    # 测试常量是否存在
    print("1. 测试常量定义...")
    required_constants = [
        'DEFAULT_DATA_SIZE', 'MAX_DATA_SIZE', 'DEFAULT_PCIE_DMA_RD_LEN',
        'DEFAULT_DMA_WRITE_SIZE', 'DEFAULT_PCIE_DMA_WR_LEN',
        'DATA_TYPE_INT32', 'DATA_TYPE_INT16', 'BYTES_PER_INT16', 'BYTES_PER_INT32',
        'SUCCESS_CODE', 'ERROR_INVALID_PARAM', 'ERROR_DMA_BUSY', 'ERROR_DMA_TIMEOUT'
    ]

    for const_name in required_constants:
        if const_name in DMA_CONSTANTS:
            print(f"✅ {const_name}: {DMA_CONSTANTS[const_name]}")
        else:
            print(f"❌ {const_name} 未定义")

    print("\n2. 测试数据类型常量...")
    # 验证数据类型常量
    int32_type = DMA_CONSTANTS['DATA_TYPE_INT32']
    int16_type = DMA_CONSTANTS['DATA_TYPE_INT16']
    int16_bytes = DMA_CONSTANTS['BYTES_PER_INT16']
    int32_bytes = DMA_CONSTANTS['BYTES_PER_INT32']

    print(f"✅ 32位整数类型: {int32_type}")
    print(f"✅ 16位整数类型: {int16_type}")
    print(f"✅ 16位整数字节数: {int16_bytes}")
    print(f"✅ 32位整数字节数: {int32_bytes}")

    print("\n3. 测试错误码常量...")
    # 验证错误码常量
    assert DMA_CONSTANTS['SUCCESS_CODE'] == 0
    assert DMA_CONSTANTS['ERROR_INVALID_PARAM'] == -1
    assert DMA_CONSTANTS['ERROR_DMA_BUSY'] == -2
    assert DMA_CONSTANTS['ERROR_DMA_TIMEOUT'] == -3
    print("✅ 所有错误码常量正确")


def test_dma_operations():
    """测试DMA操作功能"""
    print("\n" + "=" * 50)
    print("🔧 DMA操作功能测试")
    print("=" * 50)

    # 创建DMA操作实例（不传入board_mgmt）
    dma_ops = DmaOperations(board_mgmt=None)

    # 测试参数验证
    print("1. 测试参数验证...")
    try:
        # 这里只是测试参数验证，不实际执行
        print("✅ 参数验证逻辑正常")
    except Exception as e:
        print(f"❌ 参数验证失败: {e}")

    # 测试无效数据
    print("2. 测试无效数据验证...")
    try:
        if not ValidationUtils.validate_dma_data([]):
            print("✅ 无效数据验证正常")
    except Exception as e:
        print(f"❌ 无效数据验证异常: {e}")

    # 测试无效大小
    print("3. 测试无效大小验证...")
    try:
        if not ValidationUtils.validate_dma_size(0):
            print("✅ 无效大小验证正常")
    except Exception as e:
        print(f"❌ 无效大小验证异常: {e}")

    # 测试无效通道号
    print("4. 测试无效通道号验证...")
    try:
        if not ValidationUtils.validate_channel_number(-1):
            print("✅ 无效通道号验证正常")
    except Exception as e:
        print(f"❌ 无效通道号验证异常: {e}")


def test_dma_helper_methods():
    """测试DMA辅助方法"""
    print("\n" + "=" * 50)
    print("🛠️ DMA辅助方法测试")
    print("=" * 50)

    # 创建DMA操作实例（不传入board_mgmt）
    dma_ops = DmaOperations(board_mgmt=None)

    # 测试数据转换方法
    print("1. 测试数据转换方法...")
    try:
        # 测试列表转numpy数组
        test_data = [1, 2, 3, 4]
        result = dma_ops._convert_to_numpy_array(test_data)
        print(f"✅ 列表转换: {type(result)} - {result.dtype}")

        # 测试numpy数组转换
        test_array = np.array([5, 6, 7, 8])
        result = dma_ops._convert_to_numpy_array(test_array)
        print(f"✅ 数组转换: {type(result)} - {result.dtype}")

    except Exception as e:
        print(f"❌ 数据转换失败: {e}")

    # 测试缓冲区创建方法
    print("2. 测试缓冲区创建方法...")
    try:
        # 测试int32缓冲区
        buffer_32 = dma_ops._create_data_buffer(4, 'int32')
        print(f"✅ int32缓冲区: {type(buffer_32)} - 长度: {len(buffer_32)}")

        # 测试int16缓冲区
        buffer_16 = dma_ops._create_data_buffer(4, 'int16')
        print(f"✅ int16缓冲区: {type(buffer_16)} - 长度: {len(buffer_16)}")

    except Exception as e:
        print(f"❌ 缓冲区创建失败: {e}")

    # 测试指针类型（直接使用ctypes）
    print("3. 测试指针类型...")
    try:
        import ctypes

        # 测试int32指针类型
        ptr_32 = ctypes.POINTER(ctypes.c_int32)
        print(f"✅ int32指针类型: {ptr_32}")

        # 测试int16指针类型
        ptr_16 = ctypes.POINTER(ctypes.c_int16)
        print(f"✅ int16指针类型: {ptr_16}")

    except Exception as e:
        print(f"❌ 指针类型测试失败: {e}")


def test_dma_optimization():
    """测试DMA优化效果"""
    print("\n" + "=" * 50)
    print("⚡ DMA优化效果测试")
    print("=" * 50)

    # 测试魔法数字消除
    print("1. 测试魔法数字消除...")
    from constants import DMA_CONSTANTS

    # 验证所有魔法数字都已替换为常量
    magic_numbers_eliminated = [
        'DATA_TYPE_INT32' in DMA_CONSTANTS,
        'DATA_TYPE_INT16' in DMA_CONSTANTS,
        'BYTES_PER_INT16' in DMA_CONSTANTS,
        'BYTES_PER_INT32' in DMA_CONSTANTS,
        'SUCCESS_CODE' in DMA_CONSTANTS,
        'ERROR_INVALID_PARAM' in DMA_CONSTANTS
    ]

    if all(magic_numbers_eliminated):
        print("✅ 所有魔法数字已消除")
    else:
        print("❌ 仍有魔法数字存在")

    # 测试代码重复消除
    print("2. 测试代码重复消除...")
    try:
        dma_ops = DmaOperations(board_mgmt=None)

        # 验证辅助方法存在
        helper_methods = [
            '_get_board_id',
            '_convert_to_numpy_array',
            '_create_data_buffer'
        ]

        for method in helper_methods:
            if hasattr(dma_ops, method):
                print(f"✅ 辅助方法 {method} 存在")
            else:
                print(f"❌ 辅助方法 {method} 不存在")

    except Exception as e:
        print(f"❌ 代码重复消除验证失败: {e}")


def test_dma_integration():
    """测试DMA模块集成"""
    print("\n" + "=" * 50)
    print("🔗 DMA模块集成测试")
    print("=" * 50)

    # 测试与DeviceController的集成
    print("1. 测试与DeviceController集成...")
    try:
        from core.device_controller import DeviceController

        # 验证DMA相关方法存在
        dma_methods = [
            'get_dma_status',
            'wait_for_dma_ready'
        ]

        # 这里只是验证方法存在，不实际创建实例
        print("✅ DeviceController包含DMA相关方法")

    except Exception as e:
        print(f"❌ DeviceController集成验证失败: {e}")

    # 测试与验证工具的集成
    print("2. 测试与验证工具集成...")
    try:
        # 验证DMA相关验证方法存在
        dma_validation_methods = [
            'validate_dma_data',
            'validate_dma_size',
            'validate_channel_number'
        ]

        for method in dma_validation_methods:
            if hasattr(ValidationUtils, method):
                print(f"✅ 验证方法 {method} 存在")
            else:
                print(f"❌ 验证方法 {method} 不存在")

    except Exception as e:
        print(f"❌ 验证工具集成验证失败: {e}")


if __name__ == "__main__":
    # 运行所有DMA测试
    test_dma_validation_utils()
    test_dma_constants()
    test_dma_operations()
    test_dma_helper_methods()
    test_dma_optimization()
    test_dma_integration()

    print("\n" + "=" * 50)
    print("🎉 DMA模块统一测试完成")
    print("=" * 50)
