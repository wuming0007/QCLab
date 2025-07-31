# -*- coding: utf-8 -*-
"""
XGM模块测试运行器

统一运行所有模块的测试，验证重构和优化后的功能。
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_module(module_name: str, test_function: str = None):
    """运行指定的测试模块
    
    Args:
        module_name: 测试模块名称
        test_function: 特定测试函数名称（可选）
    """
    try:
        print(f"\n{'='*60}")
        print(f"🧪 运行测试模块: {module_name}")
        print(f"{'='*60}")
        
        # 导入测试模块
        test_module = __import__(module_name)
        
        if test_function:
            # 运行特定测试函数
            if hasattr(test_module, test_function):
                getattr(test_module, test_function)()
            else:
                print(f"❌ 测试函数 {test_function} 不存在")
        else:
            # 运行模块的主函数
            if hasattr(test_module, '__main__'):
                test_module.__main__()
            elif hasattr(test_module, 'main'):
                test_module.main()
            else:
                # 尝试运行模块中的所有测试函数
                test_functions = [name for name in dir(test_module) 
                                if name.startswith('test_') and callable(getattr(test_module, name))]
                
                if test_functions:
                    print(f"🔍 发现 {len(test_functions)} 个测试函数")
                    for func_name in test_functions:
                        try:
                            print(f"  - 运行 {func_name}...")
                            getattr(test_module, func_name)()
                            print(f"    ✅ {func_name} 完成")
                        except Exception as e:
                            print(f"    ❌ {func_name} 失败: {e}")
                else:
                    print(f"❌ 模块 {module_name} 没有找到测试函数")
                
        print(f"✅ 测试模块 {module_name} 运行完成")
        
    except Exception as e:
        print(f"❌ 测试模块 {module_name} 运行失败: {e}")

def run_all_tests():
    """运行所有测试模块"""
    print("🚀 XGM模块测试套件")
    print("=" * 60)
    
    # 定义测试模块列表
    test_modules = [
        # 核心模块测试
        "test_dma",
        "test_channel", 
        "test_serial",
        "test_trigger",
        "test_board",
        
        # 验证测试
        "test_validation",
    ]
    
    start_time = time.time()
    success_count = 0
    total_count = len(test_modules)
    
    for module_name in test_modules:
        try:
            run_test_module(module_name)
            success_count += 1
        except Exception as e:
            print(f"❌ 模块 {module_name} 测试失败: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失败: {total_count - success_count}/{total_count}")
    print(f"⏱️  耗时: {duration:.2f}秒")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关模块")
        return False

def run_specific_test_category(category: str):
    """运行特定类别的测试
    
    Args:
        category: 测试类别 ('core', 'functional', 'validation', 'all')
    """
    test_categories = {
        'core': [
            "test_dma",
            "test_channel", 
            "test_serial",
            "test_trigger",
            "test_board",
        ],
        'validation': [
            "test_validation",
        ]
    }
    
    if category == 'all':
        return run_all_tests()
    
    if category not in test_categories:
        print(f"❌ 未知的测试类别: {category}")
        print(f"可用类别: {list(test_categories.keys())} + 'all'")
        return False
    
    print(f"🎯 运行 {category} 类别测试")
    print("=" * 60)
    
    start_time = time.time()
    success_count = 0
    total_count = len(test_categories[category])
    
    for module_name in test_categories[category]:
        try:
            run_test_module(module_name)
            success_count += 1
        except Exception as e:
            print(f"❌ 模块 {module_name} 测试失败: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📊 {category} 类别测试结果:")
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失败: {total_count - success_count}/{total_count}")
    print(f"⏱️  耗时: {duration:.2f}秒")
    
    return success_count == total_count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="XGM模块测试运行器")
    parser.add_argument(
        '--category', 
        choices=['core', 'functional', 'validation', 'all'],
        default='all',
        help='运行特定类别的测试 (默认: all)'
    )
    
    args = parser.parse_args()
    
    if args.category == 'all':
        success = run_all_tests()
    else:
        success = run_specific_test_category(args.category)
    
    sys.exit(0 if success else 1) 