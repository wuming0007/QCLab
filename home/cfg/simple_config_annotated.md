# 简化配置文件注解版 (simple_config.json)

本文档详细解释了 `simple_config.json` 配置文件中每个部分和参数的含义。

## 文件结构概览

```json
{
    "dev": { ... },      // 硬件设备配置
    "etc": { ... },      // 全局配置
    "var": {},           // 全局变量
    "usr": { ... },      // 用户会话信息
    "station": { ... },  // 实验站配置
    "gate": { ... },     // 量子门参数
    "M0": { ... },       // 测量系统配置
    "Q0": { ... },       // 量子比特配置
    "C0": { ... }        // 耦合器配置
}
```

---

## 1. 硬件设备配置 (dev)

```json
"dev": {
    "NS_PQ": {
        "addr": "192.168.110.25",        // 设备IP地址
        "name": "NS_DDS_NEW",            // 驱动程序名称
        "type": "driver",                // 设备类型：驱动程序
        "srate": 6400000000.0,           // 采样率：6.4 GSa/s
        "pid": 0,                        // 进程ID (0表示未启动)
        "inuse": true                    // 设备使用状态：正在使用
    }
}
```

**说明：**
- **NS_PQ**: Network Synthesizer - Pulse Quantizer，主要的量子控制设备
- **addr**: 设备的网络地址，用于连接控制
- **name**: 对应的驱动程序名称，系统会加载 `home/dev/NS_DDS_NEW.py`
- **srate**: 采样率，对于AWG和数字化仪至关重要
- **inuse**: 表示设备当前是否被占用

---

## 2. 全局配置 (etc)

### 2.1 驱动程序配置

```json
"driver": {
    "path": "systemq.dev",           // 驱动程序模块路径
    "concurrent": true,              // 允许并发访问
    "timeout": 10,                   // 超时时间：10秒
    "filter": ["NS"],                // 设备过滤器：只处理NS设备
    
    "mapping": {
        "setting_LO": "LO.Frequency",        // 本地振荡器频率设置
        "setting_POW": "LO.Power",           // 本地振荡器功率设置
        "setting_OFFSET": "ZBIAS.Offset",    // Z偏置偏移设置
        "waveform_RF_I": "I.Waveform",       // RF I路波形
        "waveform_RF_Q": "Q.Waveform",       // RF Q路波形
        "waveform_TRIG": "TRIG.Marker1",     // 触发波形
        "waveform_DDS": "DDS.Waveform",      // DDS波形
        "waveform_SW": "SW.Marker1",         // 开关波形
        "waveform_Z": "Z.Waveform",          // Z控制波形
        "setting_PNT": "ADC.PointNumber",    // ADC采样点数
        "setting_SHOT": "ADC.Shot",          // ADC单次采样
        "setting_TRIGD": "ADC.TriggerDelay"  // ADC触发延迟
    }
}
```

**说明：**
- **mapping**: 硬件抽象层(HAL)的核心，将通用指令映射到具体硬件属性
- 这使得实验代码可以独立于具体硬件，提高可移植性

### 2.2 服务器配置

```json
"server": {
    "workers": 4,                    // 工作进程数：4个
    "shared": 0,                     // 共享模式：0=独占
    "delay": 10.0,                   // 延迟：10秒
    "cached": 5,                     // 缓存大小：5个任务
    "review": [-2, -1, 0, 1, 2],     // 数据回顾范围：±2个点
    "schedule": {
        "job": {
            "hour": "2"              // 定时任务：每天凌晨2点执行
        }
    },
    "filesize": 4000.0               // 文件大小限制：4000MB
}
```

### 2.3 其他配置

```json
"canvas": {
    "range": [0, 0.0001],            // 显示范围：[0, 0.1ms]
    "filter": []                     // 过滤器：空
},
"cloud": {
    "online": false,                 // 在线状态：离线
    "station": "Dongling"            // 站点名称：Dongling
}
```

---

## 3. 用户会话信息 (usr)

```json
"usr": {
    "workflow": "default",               // 工作流：默认
    "quark": {
        "pid": 12016,                    // 主进程ID
        "sub": {
            "pid": 5332,                 // 子进程ID
            "sub": {
                "Assembler": {           // 汇编器进程
                    "0": 20064,          // 工作线程0的PID
                    "1": 18952,          // 工作线程1的PID
                    "2": 15080,          // 工作线程2的PID
                    "3": 19632           // 工作线程3的PID
                },
                "Calculator": 4156,      // 计算器进程PID
                "DeviceManager": 2408,   // 设备管理器进程PID
                "Demodulator": 18688     // 解调器进程PID
            }
        }
    }
}
```

**说明：**
- 记录了软件各个组件的进程ID，主要用于调试
- 用户通常无需关心此部分

---

## 4. 实验站配置 (station)

```json
"station": {
    "sample": "84V503_ST_LML_250429",   // 样品名称
    "triggercmds": [                     // 触发命令列表
        "NS_PQ_QSYNC.CH1.TRIG"          // 同步触发命令
    ],
    "shots": 1024,                       // 默认测量次数：1024次
    "default_delay": 1e-06               // 默认延迟：1微秒
}
```

**说明：**
- **sample**: 当前测试的样品名称，应与文件名对应
- **triggercmds**: 触发一次完整实验序列所需的命令
- **shots**: 默认的单次测量重复次数，用于统计平均
- **default_delay**: 两次shots之间的默认等待时间

---

## 5. 量子门参数 (gate)

### 5.1 测量门 (Measure Gate)

```json
"Measure": {
    "Q1": {                          // 量子比特Q1的测量参数
        "default_type": "default",   // 默认类型
        "params": {
            "duration": 3.072e-06,   // 测量脉冲时长：3.072微秒
            "amp": 0.07,             // 测量脉冲幅度：0.07V
            "frequency": 7301000000.0, // 测量频率：7.301GHz
            "weight": "const(1)",    // 权重函数：常数1
            "phi": 0,                // 相位：0
            "threshold": 0,          // 判别阈值：0 (未校准)
            "ring_up_amp": 0.14,     // 上升沿幅度：0.14V
            "ring_up_waist": 0.035,  // 上升沿宽度：0.035
            "ring_up_time": 2.56e-07, // 上升沿时间：256ns
            "before": 1e-07,         // 测量前等待：100ns
            "after": 4e-07           // 测量后等待：400ns
        }
    }
}
```

**关键参数说明：**
- **frequency**: 读出谐振腔的中心频率，通过S21实验找到
- **threshold**: 用于区分比特|0⟩和|1⟩态的IQ值阈值，0值通常意味着未校准
- **ring_up_***: 脉冲上升沿相关参数，用于优化测量脉冲形状

### 5.2 单比特旋转门 (R Gate)

```json
"R": {
    "Q1": {                          // 量子比特Q1的旋转门参数
        "params": {
            "width": 6e-08,          // 脉冲宽度：60ns
            "amp": 0.5,              // 脉冲幅度：0.5V
            "frequency": 4000000000.0, // 驱动频率：4GHz (默认值，未校准)
            "delta": 0,              // 频率偏移：0
            "plateau": 0             // 平台时间：0
        }
    }
}
```

**关键参数说明：**
- **frequency**: 量子比特的跃迁频率，通过能谱实验找到
- **amp, width**: 驱动脉冲的幅度和时长，共同决定旋转角度
- **4GHz默认值**: 表明该比特的此项操作尚未校准

### 5.3 π/2旋转门 (R12 Gate)

```json
"R12": {
    "Q1": {                          // 量子比特Q1的π/2旋转门参数
        "params": {
            "width": 6e-08,          // 脉冲宽度：60ns
            "amp": 0.5,              // 脉冲幅度：0.5V
            "frequency": 4000000000.0, // 驱动频率：4GHz (默认值，未校准)
            "delta": 0,              // 频率偏移：0
            "plateau": 0             // 平台时间：0
        }
    }
}
```

---

## 6. 测量系统配置 (M0)

```json
"M0": {
    "qubits": [                          // 该测量系统控制的量子比特列表
        "Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6"
    ],
    "adcsr": 4000000000.0,               // ADC采样率：4GSa/s
    
    "setting": {                         // 测量系统设置
        "TRIGD": 9.5e-07,                // 触发延迟：950ns
        "LO": 0                          // 本地振荡器：0
    },
    
    "waveform": {                        // 波形配置
        "SR": 8000000000.0,              // 采样率：8GSa/s
        "LEN": 7.5e-05,                  // 波形长度：75微秒
        "DDS_LO": 8000000000.0,          // DDS本地振荡器频率：8GHz
        "RF": "zero()",                  // RF波形：零函数
        "TRIG": "zero()",                // 触发波形：零函数
        "DDS": "zero()"                  // DDS波形：零函数
    },
    
    "channel": {                         // 通道配置
        "DDS": null,                     // DDS通道：未分配
        "ADC": null,                     // ADC通道：未分配
        "TRIG": null,                    // 触发通道：未分配
        "LO": null                       // 本地振荡器通道：未分配
    },
    
    "calibration": {                     // 校准参数
        "DDS": {
            "delay": 5e-07               // DDS延迟：500ns
        }
    }
}
```

**说明：**
- **M0**: 测量系统0，负责控制多个量子比特的测量
- **qubits**: 该测量系统可以测量的量子比特列表
- **waveform**: 定义测量波形的参数
- **channel**: 硬件通道分配，null表示未分配

---

## 7. 量子比特配置 (Q0)

```json
"Q0": {
    "probe": "M0",                       // 关联的测量系统：M0
    "couplers": ["C0"],                  // 关联的耦合器：C0
    
    "waveform": {                        // 波形配置
        "SR": 6000000000.0,              // 采样率：6GSa/s
        "LEN": 7.5e-05,                  // 波形长度：75微秒
        "DDS_LO": 6000000000.0,          // DDS本地振荡器频率：6GHz
        "RF": "zero()",                  // RF波形：零函数
        "DDS": "zero()"                  // DDS波形：零函数
    },
    
    "channel": {                         // 通道配置
        "DDS": null,                     // DDS通道：未分配
        "Z": null                        // Z控制通道：未分配
    },
    
    "calibration": {                     // 校准参数
        "DDS": {
            "delay": 0                   // DDS延迟：0
        },
        "Z": {
            "delay": 0                   // Z控制延迟：0
        }
    },
    
    "params": {                          // 量子比特参数
        "drop_bias": 0,                  // 下降偏置：0
        "idle_bias": 0                   // 空闲偏置：0
    },
    
    "setting": {}                        // 设置：空
}
```

**说明：**
- **probe**: 指定该比特使用哪个测量系统进行测量
- **couplers**: 与该比特相连的耦合器列表
- **waveform**: 该比特的驱动波形参数
- **params**: 量子比特的物理参数，如偏置电压

---

## 8. 耦合器配置 (C0)

```json
"C0": {
    "qubits": ["Q0", "Q7"],              // 该耦合器连接的量子比特：Q0和Q7
    
    "setting": {                         // 耦合器设置
        "OFFSET": 0                      // 偏移：0
    },
    
    "waveform": {                        // 波形配置
        "SR": 4000000000.0,              // 采样率：4GSa/s
        "LEN": 7.5e-05,                  // 波形长度：75微秒
        "Z": "zero()"                    // Z控制波形：零函数
    },
    
    "channel": {                         // 通道配置
        "Z": null                        // Z控制通道：未分配
    },
    
    "calibration": {                     // 校准参数
        "Z": {
            "delay": 0                   // Z控制延迟：0
        }
    },
    
    "params": {                          // 耦合器参数
        "drop_bias": 0,                  // 下降偏置：0
        "idle_bias": 0                   // 空闲偏置：0
    }
}
```

**说明：**
- **qubits**: 该耦合器连接的两个量子比特
- **C0**: 耦合器0，用于实现Q0和Q7之间的双比特门操作
- **waveform**: 耦合器的控制波形参数
- **params**: 耦合器的物理参数

---

## 总结

这个简化配置文件包含了：

1. **硬件层**: 设备连接和驱动配置
2. **系统层**: 服务器、调度、云服务等全局配置
3. **实验层**: 样品信息、触发命令、默认参数
4. **量子层**: 量子门参数、测量系统、量子比特、耦合器配置

相比原始配置文件，这个简化版本：
- 只包含一个量子比特(Q1)的门参数
- 只包含一个测量系统(M0)和一个耦合器(C0)
- 保留了所有重要的配置结构
- 便于理解和学习配置文件的结构 