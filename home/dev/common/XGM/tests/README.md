# XGM模块测试套件

本目录包含XGM模块的所有测试文件，用于验证重构和优化后的功能。

## 📁 目录结构

```
tests/
├── __init__.py                 # 测试包初始化文件
├── README.md                   # 本说明文档
├── TEST_SUMMARY.md            # 测试总结文档
├── run_all_tests.py           # 测试运行器
├── test_config.py             # 测试配置文件
├── test_dma.py                # DMA模块统一测试
├── test_channel.py            # 通道控制模块统一测试
├── test_serial.py             # 串口通信模块统一测试
├── test_trigger.py            # 触发控制模块统一测试
├── test_board.py              # 板卡管理模块统一测试
└── test_validation.py         # 验证测试统一文件
```

## 🚀 快速开始

### 运行所有测试

```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行特定类别测试
python tests/run_all_tests.py --category core
python tests/run_all_tests.py --category functional
python tests/run_all_tests.py --category validation
```

### 运行单个测试

```bash
# 运行DMA模块测试
python tests/test_dma.py

# 运行通道控制测试
python tests/test_channel.py

# 运行串口通信测试
python tests/test_serial.py

# 运行触发控制测试
python tests/test_trigger.py

# 运行板卡管理测试
python tests/test_board.py

# 运行验证测试
python tests/test_validation.py
```

## 📊 测试类别

### 1. 核心模块测试 (core)
- **test_dma.py**: DMA模块统一测试（包含优化验证、功能测试、性能测试）
- **test_channel.py**: 通道控制模块统一测试（包含DAC/ADC通道控制、优化验证）
- **test_serial.py**: 串口通信模块统一测试（包含优化验证、功能测试、性能测试）
- **test_trigger.py**: 触发控制模块统一测试（包含优化验证、功能测试、性能测试）
- **test_board.py**: 板卡管理模块统一测试（包含初始化、验证、功能测试）

### 2. 验证测试 (validation)
- **test_validation.py**: 验证测试统一文件（包含重构验证、优化验证、等价性验证等）

## ⚙️ 测试配置

测试配置在 `test_config.py` 文件中定义，包括：

- **超时设置**: 默认超时时间、短测试超时、长测试超时
- **数据设置**: 测试数据大小、通道数量、槽位数量
- **模式设置**: 详细输出、调试模式、跳过慢速测试
- **路径设置**: 测试数据、日志、结果目录

## 🛠️ 测试工具

### 测试运行器 (run_all_tests.py)

提供统一的测试运行接口：

```python
# 运行所有测试
run_all_tests()

# 运行特定类别测试
run_specific_test_category('core')
run_specific_test_category('functional')
run_specific_test_category('validation')
```

### 测试配置 (test_config.py)

提供测试相关的工具函数：

```python
# 设置测试环境
setup_test_environment()

# 生成测试数据
test_data = generate_test_data(size=1024, data_type='int32')

# 生成测试通道
channels = generate_test_channels(count=4)

# 获取测试文件路径
data_path = get_test_data_path('test_data.npy')
log_path = get_test_log_path('test.log')
```

### 测试装饰器

```python
# 跳过慢速测试
@skip_if_slow_test
def slow_test_function():
    pass

# 设置测试超时
@timeout_test(timeout_seconds=30.0)
def timeout_test_function():
    pass
```

## 📝 编写新测试

### 1. 创建测试文件

```python
# -*- coding: utf-8 -*-
"""
新模块测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.new_module import NewModule
from utils import ValidationUtils

def test_new_module_functionality():
    """测试新模块功能"""
    print("🧪 测试新模块功能")
    
    # 测试代码
    module = NewModule()
    result = module.test_function()
    
    assert result == True
    print("✅ 新模块功能测试通过")

if __name__ == "__main__":
    test_new_module_functionality()
    print("🎉 新模块测试完成")
```

### 2. 添加到测试运行器

在 `run_all_tests.py` 中添加新测试：

```python
test_modules = [
    # ... 现有测试
    "test_new_module",  # 添加新测试
]
```

### 3. 更新测试类别

在 `test_config.py` 中更新测试类别：

```python
TEST_CATEGORIES = {
    'functional': {
        'modules': [
            # ... 现有模块
            'test_new_module',  # 添加新模块
        ]
    }
}
```

## 🔍 测试结果

测试运行后会显示：

- ✅ 成功的测试数量
- ❌ 失败的测试数量
- ⏱️ 测试耗时
- 📊 详细的测试结果

## 🐛 故障排除

### 常见问题

1. **导入错误**: 确保项目根目录已添加到Python路径
2. **模块未找到**: 检查测试文件是否在正确的目录中
3. **依赖缺失**: 确保所有必要的依赖已安装

### 调试模式

启用调试模式获取更详细的信息：

```python
# 在test_config.py中设置
TEST_CONFIG['DEBUG_MODE'] = True
```

## 📚 相关文档

- [API参考](../API_REFERENCE.md)
- [快速开始](../QUICK_START.md)
- [项目总结](../PROJECT_SUMMARY.md)
- [优化说明](../README_OPTIMIZATION.md) 