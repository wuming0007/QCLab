# 量子比特测控手册 (QCLab)

## 第一章：引言与基本原理

### 1.1 本手册的目的与范围

欢迎使用 QCLab 量子比特测控手册。

本手册旨在为量子计算研究人员、工程师和学生提供一个全面、详尽的实践指南。我们将理论知识与 `QCLab` 项目中的代码实现相结合，系统性地介绍超导量子比特的表征、校准和控制流程。

**范围覆盖：**

*   **基本原理：** 从量子比特和测控系统的基本概念讲起。
*   **软件环境：** `QCLab` 项目的配置、安装，以及核心控制语言 `qlisp` 的使用。
*   **表征流程：** 覆盖从最基础的谐振器谱测量到关键的相干性时间（T1, T2）表征。
*   **门校准：** 介绍单比特和双比特量子门的校准方法。
*   **代码实践：** 为每一个实验流程提供基于 `qlisp` 的代码范例和详细讲解。

无论您是初学者还是有经验的研究者，本手册都将帮助您更好地理解和使用 `QCLab` 系统进行高效的量子实验。

### 1.2 量子计算与量子比特简介

**量子计算**是一种遵循量子力学规律来处理和计算信息的新型计算模式。与经典计算机使用“比特”（0 或 1）作为基本单元不同，量子计算机使用**量子比特（Qubit）**。

一个量子比特可以同时处于 `|0⟩` 态和 `|1⟩` 态的**叠加态**，表示为：
`|ψ⟩ = α|0⟩ + β|1⟩`
其中，α 和 β 是复数，且满足 `|α|² + |β|² = 1`。`|α|²` 和 `|β|²` 分别代表了测量量子比特时，其状态坍缩到 `|0⟩` 或 `|1⟩` 的概率。

这种叠加特性，以及量子比特间的**纠缠**现象，使得量子计算机在处理特定问题（如大数分解、量子模拟）时拥有超越经典计算机的巨大潜力。

**超导量子比特**是实现量子计算的一种主流物理体系。它利用超导电路（如约瑟夫森结）来构建具有非等谐能级的量子系统，从而将最低的两个能级定义为 `|0⟩` 和 `|1⟩` 态。

### 1.3 量子测控系统概述

要精确地操控和测量脆弱的量子比特，需要一个复杂的电子学系统，即**量子测控系统**。该系统的核心任务是：

1.  **生成控制信号：** 产生精确的微波或直流脉冲，用于驱动量子比特完成各种量子门操作（例如，从 `|0⟩` 态翻转到 `|1⟩` 态）。
2.  **读取比特状态：** 向与比特耦合的谐振器发送探测信号，并通过分析返回信号的振幅和相位来判断量子比特处于 `|0⟩` 还是 `|1⟩` 态。
3.  **执行复杂序列：** 按照预先设计的脉冲序列（`qlisp` 程序），自动化地完成复杂的实验流程，如 T1 测量或量子算法。

**`QCLab` 在此扮演的角色：**

`QCLab` 是一个高层次的软件控制框架。它将复杂的硬件指令抽象为更易于理解和编写的 `qlisp` 语言。研究人员无需直接操作底层的任意波形发生器（AWG）或数据采集卡，而是通过编写 `qlisp` 脚本来定义实验逻辑。`QCLab` 会将这些脚本编译、优化，并下发给硬件执行，最终将测量结果返回给用户。

这种分层架构极大地提高了实验效率和代码的可复用性。在接下来的章节中，我们将深入学习如何利用 `QCLab` 和 `qlisp` 来实现具体的测控任务。

## 第二章：环境配置与 `qlisp` 语言入门

本章将指导您完成 `QCLab` 的环境配置，并快速入门其核心控制语言 `qlisp`。正确的环境配置是顺利开展后续所有实验的基础。

### 2.1 硬件与软件环境要求

（*注意：此部分为通用指南，请根据您的具体硬件和操作系统版本进行调整。*）

*   **操作系统：** Linux (推荐) / Windows / macOS
*   **Python 版本：** 3.8+
*   **核心依赖：** `numpy`, `scipy`, `matplotlib` 等科学计算包。
*   **硬件驱动：** 确保所有测控硬件（AWG, 信号发生器, 数据采集卡等）的驱动程序已正确安装。

### 2.2 `QCLab` 项目的安装与配置

我们强烈建议使用 `uv` 管理虚拟环境与依赖（更快、更可复现）。如不便使用 `uv`，也可采用经典 `venv + pip`。

#### 2.2.A 使用 `uv`（推荐）

参考快速上手：`QUICK_GUIDE.md`

1) 创建并激活虚拟环境

```bash
uv venv venv-qc --python 3.12

# 激活 (macOS/Linux)
source venv-qc/bin/activate
# 激活 (Windows)
./venv-qc/Scripts/activate
```

2) 安装依赖（使用清华镜像）

```bash
uv pip install "quarkstudio[full]" --index-url https://pypi.tuna.tsinghua.edu.cn/simple
# 按需修正：
uv pip install pyside6==6.9.0
uv pip install wath
```

3) 初始化全局配置与服务

```bash
# 首次运行会生成 ~/quark.json，编辑其中的 server.home 指向本仓库的 `home` 目录
quark

# 启动后端服务（建议在已激活环境中）
uv run quark server
```

更多细节、故障排查与示例命令，请参见 `QUICK_GUIDE.md`。

#### 2.2.B 使用 `venv + pip`（可选）

**1) 创建并激活虚拟环境：**

```bash
python -m venv .venv
source .venv/bin/activate            # Linux/macOS
.venv\Scripts\activate               # Windows
```

**2) 安装依赖：**

```bash
pip install -r requirements.txt      # 若本仓库提供
```

**3) 系统配置：**

根据 `CONFIG_GUIDE.md` 的指引，配置硬件连接和通道信息。这通常涉及到一个或多个 YAML 或 JSON 格式的配置文件。您需要将物理仪器、通道与 `QCLab` 中的逻辑名称对应起来。

例如：

```yaml
AWG_XY:
  type: Tektronix_AWG5014
  address: 'TCPIP0::192.168.1.10::inst0::INSTR'
  channels:
    - {id: 1, name: Qubit1_X}
    - {id: 2, name: Qubit1_Y}
```

**请务必仔细阅读 `CONFIG_GUIDE.md` 并完成此步骤。**

### 2.3 `qlisp` 语法核心

`qlisp` (Quantum Lisp) 是一种专为量子脉冲序列编程设计的领域特定语言。它的语法简洁，富有表达力，核心思想是**将脉冲序列的定义与执行分离开**。

> 重要说明（与本仓库对齐）：
> 本手册部分章节为便于理解，使用了“脉冲级”示例（如 `PULSE`/`WAIT`/`TRIG` 与假想的 `qclab_run`/`qclab_sweep`）。
> 在本仓库的实际实现中，推荐采用更高层的 `Recipe + QLisp 电路` 工作流：电路以“(operation, target)”元组列表表示，编译后由后端生成并下发具体脉冲。参见 `qlisp_syntax_guide.md` 与 `home/run/s21_annotated.py`。

**基本概念：**

*   **指令 (Instruction)：** `qlisp` 程序的基本单元，代表一个具体的操作，如 `PULSE`（播放脉冲）、`WAIT`（等待）、`TRIG`（触发采集）。
*   **块 (Block)：** 一组指令的集合。块可以嵌套，形成层次结构。
*   **参数化：** `qlisp` 支持在定义时使用变量作为参数，在执行时再传入具体数值。这使得序列的复用和扫描变得非常方便。

**示例代码（与本仓库对齐）：**

```python
# 电路以“(operation, target)”元组的列表表示
# operation 也为元组，如 ('X90',) / ('Measure', 0)
circuit = [
    (('X90',), 'Q0'),
    (('Measure', 0), 'Q0'),
]
```

### 2.4 编写并执行第一个 `qlisp` 程序（概念示例）

让我们结合一个简单的例子——播放一个高斯脉冲并触发一次测量——来实践一下。

**1. 创建 `hello_quantum.py` 文件：**

```python
# 本示例为“概念示例”，展示参数化思想
from qlisp import var

rabi_pulse = [
    # 概念化的脉冲级描述：
    # PULSE(channel='Qubit1_XY', waveform='gaussian', length=20e-9, amplitude=var('amp')),
    # TRIG(channel='Measure_Trig', duration=10e-9)
]

# 实际运行请参考 2.5 小节的 Recipe 范式
result = {"note": "conceptual only"}
print(result)
```

**2. 执行程序：**

确保你的虚拟环境已激活，并且硬件已连接并上电。

```bash
python hello_quantum.py
```

如果一切配置正确，您应该能看到服务正常启动。实际实验执行方式请参考下一节的 Recipe 示例。

在下一章中，我们将开始进行真正的量子比特表征实验。

### 2.5 使用 Recipe 运行第一个实验（S21，参考实现）

下面给出与本仓库一致的最小化工作流，展示如何使用 `Recipe` 与电路描述来执行一次 S21 扫描。

电路函数（节选）：

```python
def circuit(qubits: list[str], ctx=None) -> list:
    cc = [(('Measure', i, ), q) for i, q in enumerate(qubits)]
    return cc
```

执行函数（节选）：

```python
def calibrate(qubits: list[str]) -> list:
    qubits = [f'Q{i}' for i in [999]]

    rcp = Recipe('s21', signal='iq_avg')
    rcp.lib = 'lib.gates.u3rcp'
    rcp.arch = 'rcp'
    rcp.circuit = circuit

    rcp['qubits'] = tuple(qubits)
    rcp['freq'] = np.linspace(-10, 10, 101) * 1e6
    # ...
```

运行步骤（示例）：

```bash
# 1) 启动服务（确保 ~/quark.json 的 server.home 指向本仓库的 home 目录）
uv run quark server

# 2) 另开终端，激活同一虚拟环境后运行示例脚本
uv run python home/run/s21.py
```

## 第三章：基础单比特表征

在能够对量子比特进行精确的量子门操作之前，我们必须首先“找到”并“理解”它。本章介绍的实验是所有后续操作的基础，其目的是确定量子系统的关键物理参数。

### 3.1 谐振器谱 (Resonator Spectroscopy)

**1. 物理原理与目的**

在典型的超导量子比特架构中，每个量子比特都与一个微波谐振器（Resonator）耦合。这个谐振器不仅用于读取比特的状态，其自身的谐振频率也会受到比特状态的微小影响（即色散频移）。

**谐振器谱**实验的目的就是精确找到这个谐振器的中心频率 `f_r`。

实验过程非常直接：

*   向谐振器发送一个频率连续变化的微波探测信号（通常称为“读出脉冲”）。
*   同时，测量并记录返回信号的振幅（Amplitude）和相位（Phase）。
*   当探测频率与谐振器频率一致时，谐振器会吸收最多的能量，导致返回信号的振幅出现一个明显的下降（谷值），同时相位也会发生显著的变化。这个谷值对应的频率点就是 `f_r`。

找到 `f_r` 是至关重要的第一步，因为后续所有的读出操作都将使用这个频率的微波信号。

**2. `qlisp` 代码实现**

谐振器谱实验的核心是**扫描频率**。在 `qlisp` 中，我们可以通过参数化脉冲的频率，并在执行循环中传入不同的频率值来实现这一点。

以下是一个典型的谐振器谱 `qlisp` 序列范例：

```python
# resonator_spectroscopy.py

import numpy as np
from qlisp import *
# 假设 qclab_run 是 QCLab 中用于执行的函数
from qclab.execution import qclab_run 
# 假设 qclab_sweep 是一个用于执行扫描任务的便捷函数
from qclab.sweeping import qclab_sweep

# 1. 定义脉冲序列模板
# 我们将读出脉冲的频率定义为一个变量 'freq'
resonator_spec_seq = [
    # 长时间、低功率的读出脉冲
    PULSE(channel='Readout_Drive', 
          waveform='square', 
          length=2000e-9, 
          frequency=var('freq'), # 参数化频率
          amplitude=0.1),
    
    # 紧接着触发数据采集
    TRIG(channel='Measure_Trig', duration=2000e-9)
]

# 2. 设置扫描参数
# 定义一个频率扫描范围，例如从 6.0 GHz 到 6.2 GHz，扫描 201 个点
freq_sweep = np.linspace(6.0e9, 6.2e9, 201)

# 3. 执行扫描
# qclab_sweep 会循环执行序列，每次更新 'freq' 的值
# 它会返回两个数组：扫描的频率点，以及每个点对应的测量结果 (I, Q)
scan_params, scan_results = qclab_sweep(
    resonator_spec_seq, 
    sweep_vars={'freq': freq_sweep}
)

# 4. 数据处理与可视化
# scan_results 通常是复数 (I + jQ)
# 我们可以计算其振幅和相位
amplitude = np.abs(scan_results)
phase = np.angle(scan_results, deg=True)

# (此处省略了使用 matplotlib 绘图的代码)
# 绘制 amplitude vs. scan_params['freq'] 曲线
# 找到曲线的谷值，即为谐振器频率 f_r

print(f"扫描完成！请分析数据以确定谐振器频率。")

```

**3. 代码讲解**

*   `PULSE(...)`: 我们定义了一个方波脉冲，作用于读出驱动通道 (`Readout_Drive`)。它的频率被设置为一个名为 `freq` 的变量 (`var('freq')`)。
*   `TRIG(...)`: 紧随脉冲之后，我们触发测量系统在相同的时间窗口内进行数据采集。
*   `qclab_sweep(...)`: 这是一个高级函数（我们假设 `QCLab` 提供此类功能），它简化了扫描操作。它会自动遍历 `freq_sweep` 数组中的每一个频率值，将其赋给序列中的 `freq` 参数，然后执行序列并收集结果。
*   **数据分析**: 实验结束后，我们需要对返回的 `amplitude` 和 `phase` 数据进行分析。通常，我们会用一个洛рен兹函数来拟合振幅曲线的谷值，从而更精确地提取 `f_r`。

### 3.2 交流斯塔克频移 (AC Stark Shift)

**1. 物理原理与目的**

交流斯塔克频移是一种**双音谱（two-tone spectroscopy）**技术。在找到谐振器频率 `f_r` 后，我们可以利用它来间接探测量子比特的能级信息。

**实验目的：**

*   **验证耦合：** 证实量子比特与读出谐振器之间存在有效的量子耦合。
*   **粗略定位比特频率：** 初步确定量子比特的跃迁频率 `f_q` 的大致范围。

**实验过程：**

1.  向谐振器发送一个**频率固定**的探测信号（Probe），其频率就设置为我们刚刚测得的 `f_r`。
2.  同时，向量子比特的控制线发送另一个**频率扫描**的强驱动信号（Drive/Pump）。这个驱动信号的频率范围覆盖了我们预估的比特频率 `f_q` 所在区间。
3.  我们持续监测并记录从谐振器返回的探测信号的振幅和相位。

当驱动信号的频率 `f_drive` 接近或等于比特的真实跃迁频率 `f_q` 时，驱动信号会与比特发生相互作用，有效地“激发”比特。这种激发会改变比特的状态，进而通过耦合效应，改变谐振器的等效电容或电感，最终导致谐振器的中心频率发生一个微小的偏移。我们的探测信号（频率为 `f_r`）就会“看到”这个变化，其返回的振幅和相位也随之改变。

通过绘制返回信号（特别是相位）随驱动频率 `f_drive` 变化的曲线，我们就能观察到一个明显的频移特征，其中心位置就对应着比特的大致跃迁频率 `f_q`。

**2. `qlisp` 代码实现**

这个实验需要在两个通道上同时施加脉冲：一个在读出通道（固频），一个在比特控制通道（扫频）。在 `qlisp` 中，我们可以使用 `BLOCK` 结构来实现脉冲的并行播放。

```python
# ac_stark_shift.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：从上一个实验中我们已经知道了谐振器的频率
# 例如 f_r = 6.05 GHz
f_r = 6.05e9

# 1. 定义双音脉冲序列
# 我们将扫描比特驱动脉冲的频率 'qubit_freq'
ac_stark_seq = [
    # 使用 BLOCK 来并行执行内部的指令
    BLOCK([
        # 比特驱动脉冲 (Pump)
        PULSE(channel='Qubit_XY',       # 作用于比特的 XY 控制线
              waveform='square',      # 使用方波以提供持续的驱动
              length=1000e-9,         # 驱动时长
              frequency=var('qubit_freq'), # 此频率将被扫描
              amplitude=0.2),         # 驱动幅度不宜过大，避免过饱和

        # 读出探测脉冲 (Probe)
        PULSE(channel='Readout_Drive',  # 作用于读出谐zhèn器
              waveform='square',      # 探测脉冲也持续作用
              length=1000e-9,
              frequency=f_r,          # 频率固定为谐振器频率
              amplitude=0.1)
    ]),

    # 紧随其后触发测量
    TRIG(channel='Measure_Trig', duration=1000e-9)
]

# 2. 设置扫描参数
# 扫描比特驱动频率，例如从 4.0 GHz 到 4.5 GHz
qubit_freq_sweep = np.linspace(4.0e9, 4.5e9, 101)

# 3. 执行扫描
scan_params, scan_results = qclab_sweep(
    ac_stark_seq,
    sweep_vars={'qubit_freq': qubit_freq_sweep}
)

# 4. 数据分析
# 绘制谐振器的响应（振幅或相位） vs. 比特驱动频率
amplitude = np.abs(scan_results)
phase = np.angle(scan_results, deg=True)

# (此处省略绘图代码)
# 分析 phase vs. qubit_freq_sweep 曲线中的频移特征
# 其中心点就是 f_q 的一个很好的近似值

print("AC Stark shift 实验完成。")

```

**3. 代码讲解**

*   `f_r = 6.05e9`: 我们首先需要一个准确的谐振器频率值，这是上一步实验（谐振器谱）的输出。
*   `BLOCK([...])`: 这是实现双音谱的关键。`BLOCK` 内的所有 `PULSE` 指令会**同时开始**执行。这确保了在施加探测脉冲的整个过程中，比特也一直受到驱动脉冲的作用。
*   **Pump Pulse**: `PULSE(channel='Qubit_XY', ...)` 是驱动脉冲。它的频率 `qubit_freq` 是变量，将在扫描中被改变。
*   **Probe Pulse**: `PULSE(channel='Readout_Drive', ...)` 是探测脉冲。它的频率被**固定**为 `f_r`。
*   `qclab_sweep`: 与上一个实验类似，该函数负责迭代 `qubit_freq_sweep` 中的每一个值，执行脉冲序列，并记录结果。
*   **数据分析**: 实验完成后，我们主要关心的是相位的变化。在 `f_drive ≈ f_q` 的地方，相位会有一个类似色散的过零点，通过定位这个特征的中心，我们就能得到 `f_q` 的一个很好的估计值。

### 3.3 比特谱 (Qubit Spectroscopy)

**1. 物理原理与目的**

比特谱实验与交流斯塔克频移非常相似，都是一种双音谱技术。但它的目的更为直接：**精确测量量子比特的跃迁频率 `f_q`**。

**与 AC Stark Shift 的区别：**

*   **驱动功率：** 比特谱通常使用**更低**的驱动功率（Pump）。在 AC Stark Shift 中，我们使用强驱动来“移动”谐振器频率；而在比特谱中，我们只想在驱动频率与比特跃迁频率共振时，刚好能激发它从 `|0⟩` 态跃迁到 `|1⟩` 态即可，避免过强的功率导致斯塔克频移本身或能级展宽，从而影响测量精度。
*   **测量方式：** 比特谱的测量方式更接近于一次真正的“状态读出”。我们先施加一个较短的驱动脉冲（Pump），然后立刻用一个读出脉冲（Probe）去测量比特的状态。如果驱动脉冲的频率 `f_drive` 正好是 `f_q`，比特就会被翻转到 `|1⟩` 态。由于色散耦合，处于 `|1⟩` 态的比特会导致谐振器频率有一个微小的偏移 `δ`。因此，读出脉冲返回的信号振幅和相位会与比特处于 `|0⟩` 态时不同。

通过扫描驱动脉冲的频率 `f_drive`，并记录每次读出的结果，我们就能在 `f_drive = f_q` 的位置看到一个响应峰或谷，从而精确地确定比特频率。

**2. `qlisp` 代码实现**

`qlisp` 序列的结构从“并行”变为了“串行”：先驱动，后读出。

```python
# qubit_spectroscopy.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：已知 f_r 和 f_q 的大致范围
f_r = 6.05e9
# f_q_estimate 来自 AC Stark Shift 实验, e.g., 4.25 GHz
f_q_estimate = 4.25e9

# 1. 定义脉冲序列：先驱动，后读出
qubit_spec_seq = [
    # 1. 比特驱动脉冲 (Pump)
    PULSE(channel='Qubit_XY',
          waveform='gaussian',      # 使用高斯脉冲以减少频谱泄露
          length=500e-9,          # 脉冲可以长一些，以保证足够的分辨率
          frequency=var('qubit_freq'), # 此频率将被扫描
          amplitude=0.05),          # 使用较低的幅度

    # 2. 等待一小段时间，确保驱动脉冲完全结束
    WAIT(duration=20e-9),

    # 3. 读出脉冲 (Probe)
    PULSE(channel='Readout_Drive',
          waveform='square',
          length=400e-9,          # 标准的读出脉冲长度
          frequency=f_r,          # 固定频率为谐振器频率
          amplitude=0.1),

    # 4. 触发测量
    TRIG(channel='Measure_Trig', duration=400e-9, delay=20e-9) # delay与WAIT匹配
]

# 2. 设置扫描参数
# 在 f_q_estimate 周围进行精细扫描
# 例如，扫描 +/- 50 MHz 范围，共 101 个点
qubit_freq_sweep = np.linspace(f_q_estimate - 50e6, f_q_estimate + 50e6, 101)

# 3. 执行扫描
scan_params, scan_results = qclab_sweep(
    qubit_spec_seq,
    sweep_vars={'qubit_freq': qubit_freq_sweep}
)

# 4. 数据分析
# 绘制测量结果 vs. 驱动频率
amplitude = np.abs(scan_results)
phase = np.angle(scan_results, deg=True)

# (此处省略绘图代码)
# 寻找振幅或相位的峰/谷，其中心位置就是精确的 f_q
# 通常使用洛伦兹函数拟合来获得更高精度的中心频率值

print("Qubit spectroscopy 实验完成。")

```

**3. 代码讲解**

*   **串行结构**: 与 AC Stark Shift 不同，这里的 `PULSE` 指令是按顺序执行的。`Qubit_XY` 上的脉冲结束后，`Readout_Drive` 上的脉冲才开始。这是一个典型的“Pump-Probe”实验序列。
*   `PULSE(..., waveform='gaussian', ...)`: 我们为驱动脉冲选用了高斯波形。相比方波，高斯脉冲在频域上更集中，能更精确地激发目标频率，减少对邻近能级的影响。
*   `amplitude=0.05`: 我们显著降低了驱动脉冲的幅度，以避免功率展宽（Power Broadening），从而获得更窄、更精确的谱线。
*   `WAIT(duration=20e-9)`: 在驱动和读出之间插入一个短暂的等待，可以确保两个操作之间没有重叠，避免干扰。
*   **精细扫描**: 扫描范围 `qubit_freq_sweep` 变得更小（例如总共 100 MHz），但扫描点数更多。这允许我们以更高的分辨率来确定 `f_q` 的精确值。
*   **数据拟合**: 为了从实验数据中提取最精确的 `f_q` 值，通常会对得到的谱线（峰或谷）用洛伦兹函数（Lorentzian function）进行拟合，峰值的中心即为所求的 `f_q`。

### 3.4 拉比振荡 (Rabi Oscillation)

**1. 物理原理与目的**

在确定了比特的跃迁频率 `f_q` 后，我们就可以向比特发送**共振**的驱动脉冲来操控它的状态。拉比振荡是一个用来校准脉冲参数（主要是**幅度**或**时长**）的基础实验。

**实验目的：**

*   **校准 π 脉冲和 π/2 脉冲：** 找到能将比特从 `|0⟩` 翻转到 `|1⟩` 的脉冲参数（π 脉冲），以及能将其制备成 `(|0⟩ + |1⟩)/√2` 叠加态的脉冲参数（π/2 脉冲）。这是实现所有单比特量子门的基础。
*   **观察量子相干性：** 拉比振荡的存在本身就是量子比特相干性的一个有力证明。

**实验过程：**

1.  将量子比特初始化到基态 `|0⟩` (通常通过等待足够长的时间使其弛豫到基态即可)。
2.  向比特发送一个频率固定为 `f_q` 的驱动脉冲。
3.  **扫描**这个脉冲的某个参数，最常见的是**幅度 (Amplitude)** 或 **时长 (Length)**。
4.  在每个扫描点，驱动脉冲结束后，立刻进行一次读出操作，测量比特末态是 `|0⟩` 还是 `|1⟩` 的概率。

当脉冲的“能量”（由幅度和时长的乘积决定）逐渐增加时，比特的状态会在 `|0⟩` 和 `|1⟩` 之间周期性地振荡。例如，从 `|0⟩` 开始，它会逐渐变为 `|1⟩`，然后回到 `|0⟩`，再到 `|1⟩`，如此往复。这个现象就是拉比振荡。

通过绘制比特处于 `|1⟩` 态的概率（或读出信号的幅值）随扫描参数（如幅度）变化的曲线，我们将得到一个衰减的正弦波。第一个峰值对应的参数就是 **π 脉冲**，第一个过零点（或曲线中点）对应的参数就是 **π/2 脉冲**。

**2. `qlisp` 代码实现 (扫描幅度)**

```python
# rabi_oscillation.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：已知 f_r 和 f_q
f_r = 6.05e9
f_q = 4.251e9 # 使用比特谱得到的精确频率

# 1. 定义拉比脉冲序列
# 我们将扫描驱动脉冲的幅度 'amp'
rabi_seq = [
    # 1. XY驱动脉冲，用于翻转比特
    PULSE(channel='Qubit_XY',
          waveform='gaussian', 
          length=40e-9,           # 固定脉冲时长
          frequency=f_q,          # 固定频率为比特频率
          amplitude=var('amp')),   # 扫描此幅度

    # 2. 等待
    WAIT(duration=20e-9),

    # 3. 读出脉冲
    PULSE(channel='Readout_Drive', waveform='square', length=400e-9, frequency=f_r),

    # 4. 触发测量
    TRIG(channel='Measure_Trig', duration=400e-9, delay=20e-9)
]

# 2. 设置扫描参数
# 扫描幅度，例如从 0 到 1.0，共 101 个点
amp_sweep = np.linspace(0, 1.0, 101)

# 3. 执行扫描
# 为了提高信噪比，每个扫描点通常会重复测量多次（例如 1000 次）并取平均
# 这个功能通常由 qclab_sweep 或其配置项支持
scan_params, scan_results = qclab_sweep(
    rabi_seq,
    sweep_vars={'amp': amp_sweep},
    num_averages=1000
)

# 4. 数据分析
# 绘制测量结果 vs. 扫描的幅度
population_1 = process_readout_to_population(scan_results) # 假设有函数处理原始数据

# (此处省略绘图和拟合代码)
# 对 population_1 vs. amp_sweep 数据进行正弦衰减拟合：
# y = A * sin(B * x + C) * exp(-D * x) + E
# 从拟合参数 B 中可以提取出 π 脉冲和 π/2 脉冲的幅度

pi_pulse_amp = find_first_peak(amp_sweep, population_1)
pi_half_pulse_amp = find_first_midpoint(amp_sweep, population_1)

print(f"π 脉冲幅度 (X180) 校准为: {pi_pulse_amp:.4f}")
print(f"π/2 脉冲幅度 (X90) 校准为: {pi_half_pulse_amp:.4f}")

```

**3. 代码讲解**

*   `length=40e-9`: 在扫描幅度时，我们通常会选择一个固定的、适中的脉冲时长。这个时长需要足够短以减少退相干的影响，又要足够长以避免需要过大的驱动功率。
*   `amplitude=var('amp')`: 这是我们的扫描变量。`qclab_sweep` 将会用 `amp_sweep` 数组中的值来依次替换它。
*   `num_averages=1000`: 单次量子测量具有随机性。为了获得确定的概率，我们需要对同一个实验重复成百上千次，然后对结果进行平均。这是一个非常关键的步骤，我们假设 `qclab_sweep` 函数支持这个功能。
*   `process_readout_to_population(...)`: 读出系统返回的原始数据（I-Q值）需要被正确地分类为 `|0⟩` 态或 `|1⟩` 态，并计算出 `|1⟩` 态的布居数（概率）。这通常需要一个预先校准好的判别阈值。
*   **数据拟合**: 拉比振荡曲线的衰减反映了量子比特的退相干效应。通过对数据进行正弦衰减拟合，我们可以精确地提取振荡的频率，从而计算出第一个峰值点（π 脉冲）和半峰值点（π/2 脉冲）对应的幅度值。

完成拉比振荡实验后，我们就拥有了最基本的量子逻辑门：任意角度的 X 旋转门（通过改变脉冲幅度和时长实现）。

## 第四章：相干性与弛豫时间表征

拥有了可靠的 π 脉冲后，我们就可以开始评估量子比特的性能了。相干性是量子比特能够维持其量子态（特别是叠加态）能力的核心指标。本章将介绍如何测量几个最关键的相干性时间：T1, T2* 和 T2。

### 4.1 T1 测量 (弛豫时间)

**1. 物理原理与目的**

**T1**，即**纵向弛豫时间**或**能量弛豫时间**，是衡量量子比特能级寿命的指标。它描述了当比特处于激发态 `|1⟩` 时，会以多快的速度自发地、不可逆地衰变回基态 `|0⟩`。这个过程主要是由于比特与环境的能量交换引起的。

**实验目的：**

*   **量化比特寿命：** 测量 T1 时间常数。一个更长的 T1 意味着比特可以将量子信息（以 `|1⟩` 态的形式）保存得更久，这是实现复杂量子算法的先决条件。

**实验过程：**

1.  将量子比特初始化到 `|0⟩` 态。
2.  使用一个**π 脉冲**（已在拉比实验中校准好）将其精确地翻转到 `|1⟩` 态。
3.  让比特自由演化，**等待一段可变的时间 `t_delay`**。在这段时间里，比特会以一定的概率从 `|1⟩` 弛豫回 `|0⟩`。
4.  在等待 `t_delay` 结束后，立刻进行一次读出操作，测量比特的状态。
5.  重复以上步骤，扫描不同的 `t_delay` 值，从 0 开始一直到数倍于预估的 T1 时间。

通过绘制比特最终仍处于 `|1⟩` 态的概率随 `t_delay` 变化的曲线，我们将得到一个指数衰减曲线。这个曲线的时间常数就是 T1。

**2. `qlisp` 代码实现**

```python
# t1_measurement.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：已知 f_r, f_q, 和 π 脉冲的幅度
f_r = 6.05e9
f_q = 4.251e9
pi_pulse_amp = 0.85 # 来自拉比实验的校准结果
pi_pulse_len = 40e-9

# 1. 定义 T1 测量序列
# 我们将扫描激发态和读出之间的等待时间 't_delay'
t1_seq = [
    # 1. π 脉冲，将比特从 |0> 翻转到 |1>
    PULSE(channel='Qubit_XY',
          waveform='gaussian',
          length=pi_pulse_len,
          frequency=f_q,
          amplitude=pi_pulse_amp),

    # 2. 可变的等待时间，让比特自由弛豫
    WAIT(duration=var('t_delay')),

    # 3. 读出脉冲
    PULSE(channel='Readout_Drive', waveform='square', length=400e-9, frequency=f_r),

    # 4. 触发测量
    TRIG(channel='Measure_Trig', duration=400e-9)
]

# 2. 设置扫描参数
# 扫描等待时间，例如从 0 到 50 微秒，共 51 个点
t_delay_sweep = np.linspace(0, 50e-6, 51)

# 3. 执行扫描
scan_params, scan_results = qclab_sweep(
    t1_seq,
    sweep_vars={'t_delay': t_delay_sweep},
    num_averages=1000
)

# 4. 数据分析
# 将原始读出数据转换为 |1> 态的布居数
population_1 = process_readout_to_population(scan_results)

# (此处省略绘图和拟合代码)
# 对 population_1 vs. t_delay_sweep 数据进行指数衰减拟合：
# y = A * exp(-x / T1) + B
# 从拟合中提取出的参数 T1 就是我们要求解的弛豫时间

# t1_fit = fit_exponential_decay(t_delay_sweep, population_1)
# print(f"T1 time: {t1_fit.T1:.2f} µs")

print("T1 测量完成。")

```

**3. 代码讲解**

*   `PULSE(..., amplitude=pi_pulse_amp, ...)`: 我们使用在拉比实验中校准好的 π 脉冲参数，确保能够高效地将比特制备到 `|1⟩` 态。
*   `WAIT(duration=var('t_delay'))`: 这是 T1 实验的核心。`qclab_sweep` 会用 `t_delay_sweep` 数组中的值来依次替换 `t_delay`，从而实现对弛豫时间的扫描。
*   **序列结构**: 整个序列非常直观：`激发 -> 等待 -> 测量`。这清晰地反映了 T1 实验的物理过程。
*   `t_delay_sweep`: 扫描范围的选取很重要。终点值应该远大于预期的 T1（例如 3-5 倍），以确保能观察到完整的衰减过程。扫描的步长则决定了曲线的分辨率。
*   **数据拟合**: 拟合函数 `y = A * exp(-x / T1) + B` 中，`A` 是振幅，`B` 是基线（由于测量误差等原因，最终布居数可能不会完全衰减到0），而 `T1` 就是我们最关心的参数。

### 4.2 T2* 测量 (Ramsey 实验)

**1. 物理原理与目的**

**T2***，即**自由感应衰减（Free Induction Decay, FID）时间**，是衡量量子比特相位稳定性的一个关键指标。它描述了一个处于叠加态的量子比特，由于与环境的相互作用以及自身频率的缓慢漂移，其相位信息会以多快的速度丢失。

**实验目的：**

*   **测量相位退相干时间：** 确定 T2* 时间常数。T2* 通常远小于 T1，因为它对更多的噪声源（特别是低频噪声，如磁场波动、电荷噪声）敏感。
*   **精确测量比特频率：** Ramsey 实验的振荡频率实际上是施加的驱动脉冲频率与比特真实跃迁频率之间的差值（Detuning）。因此，它也可以被用来进行比比特谱更精确的频率校准。

**实验过程（Ramsey 实验）：**

1.  将量子比特初始化到 `|0⟩` 态。
2.  使用一个**π/2 脉冲**将其翻转到 X-Y 平面，制备成 `(|0⟩ + |1⟩)/√2` 叠加态。
3.  让比特自由演化，**等待一段可变的时间 `t_delay`**。在这段时间里，比特的相位会相对于驱动它的参考时钟演化。同时，各种噪声会使这个相位变得不确定，导致退相干。
4.  在等待 `t_delay` 结束后，再施加一个**π/2 脉冲**。这个脉冲会将 X-Y 平面上的相位信息转换回 Z 轴上的布居数差异。
5.  立刻进行读出操作，测量比特的状态。
6.  重复以上步骤，扫描不同的 `t_delay` 值。

如果驱动频率与比特频率有微小失谐 `Δf`，最终测得的 `|1⟩` 态概率会随 `t_delay` 按 `cos(2π * Δf * t_delay)` 振荡。这个振荡的包络线则是一个指数衰减，其时间常数就是 T2*。

**2. `qlisp` 代码实现**

```python
# ramsey_experiment.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：已知 f_r, f_q, 和 π/2 脉冲的幅度
f_r = 6.05e9
f_q_drive = 4.251e9 # 我们故意引入一个微小的失谐，例如 1 MHz
pi_half_pulse_amp = 0.425 # 来自拉比实验的校准结果
pi_half_pulse_len = 40e-9

# 1. 定义 Ramsey 序列
# 我们将扫描两个 π/2 脉冲之间的等待时间 't_delay'
ramsey_seq = [
    # 1. 第一个 π/2 脉冲
    PULSE(channel='Qubit_XY',
          waveform='gaussian',
          length=pi_half_pulse_len,
          frequency=f_q_drive,
          amplitude=pi_half_pulse_amp),

    # 2. 可变的自由演化时间
    WAIT(duration=var('t_delay')),

    # 3. 第二个 π/2 脉冲
    PULSE(channel='Qubit_XY',
          waveform='gaussian',
          length=pi_half_pulse_len,
          frequency=f_q_drive,
          amplitude=pi_half_pulse_amp),

    # 4. 读出
    PULSE(channel='Readout_Drive', waveform='square', length=400e-9, frequency=f_r),
    TRIG(channel='Measure_Trig', duration=400e-9)
]

# 2. 设置扫描参数
# 扫描等待时间，例如从 0 到 10 微秒，共 101 个点
t_delay_sweep = np.linspace(0, 10e-6, 101)

# 3. 执行扫描
scan_params, scan_results = qclab_sweep(
    ramsey_seq,
    sweep_vars={'t_delay': t_delay_sweep},
    num_averages=1000
)

# 4. 数据分析
population_1 = process_readout_to_population(scan_results)

# (此处省略绘图和拟合代码)
# 对数据进行正弦衰减拟合：
# y = A * cos(2 * pi * f_detuning * x + phi) * exp(-x / T2_star) + B
# 从拟合中可以同时提取出 T2* 和精确的频率差 f_detuning

# ramsey_fit = fit_ramsey_decay(t_delay_sweep, population_1)
# print(f"T2* time: {ramsey_fit.T2_star:.2f} µs")
# print(f"Frequency Detuning: {ramsey_fit.f_detuning / 1e6:.3f} MHz")
# f_q_precise = f_q_drive + ramsey_fit.f_detuning
# print(f"Precise Qubit Frequency: {f_q_precise / 1e9:.6f} GHz")

print("Ramsey 实验完成。")

```

**3. 代码讲解**

*   **π/2 - wait - π/2 结构**: 这是 Ramsey 实验的标志性序列。第一个 π/2 脉冲创建叠加态，`WAIT` 提供演化时间，第二个 π/2 脉冲将相位转回布居数。
*   `f_q_drive`: 我们使用的驱动频率。在实践中，它可能与比特的真实频率 `f_q_true` 有一个小的差值 `Δf = f_q_drive - f_q_true`。Ramsey 实验的结果会揭示这个 `Δf`。
*   `WAIT(duration=var('t_delay'))`: 扫描的核心，改变这段等待时间就改变了比特的相位累积量。
*   **数据拟合**: 拟合函数现在是一个带指数衰减包络的余弦函数。从这个拟合中我们可以一举两得：
    1.  **T2***: 从指数衰减项 `exp(-x / T2_star)` 中获得。
    2.  **精确频率**: 从余弦项 `cos(2 * pi * f_detuning * x + phi)` 的频率 `f_detuning` 中获得。之后，我们可以将驱动频率更新为 `f_q_drive - f_detuning` 来更精确地匹配比特频率。

T2* 是一个非常敏感的参数，它通常是我们需要通过各种技术（如动态解耦）来努力延长和优化的对象。

### 4.3 T2 测量 (Hahn Echo)

**1. 物理原理与目的**

我们已经看到 T2* 对各种噪声（特别是低频噪声）都非常敏感。然而，在这些噪声中，变化比实验时间慢得多的“准静态”噪声，其影响是可以通过巧妙的脉冲序列来消除的。**Hahn Echo** 就是最基础、最经典的例子。

**实验目的：**

*   **消除准静态噪声影响：** 通过“反转”相位的演化，抵消掉由缓慢漂移的场或频率带来的退相干效应。
*   **测量 T2 时间：** 确定 T2 时间常数。T2 反映了比特在排除了慢噪声影响后，由更快的、不可逆的随机过程（如涨落的临近电荷、散粒噪声等）所决定的“内禀”退相干时间。因此，我们总是有 `T2 >= T2*`。

**实验过程（Hahn Echo）：**

1.  将量子比特初始化到 `|0⟩` 态。
2.  使用一个**π/2 脉冲**将其制备成叠加态。
3.  让比特自由演化 **`t_delay / 2`** 的时间。在此期间，不同比特（或同一个比特在不同重复实验中）因为频率的微小差异，会累积不同的相位，导致“失相”。
4.  施加一个**π 脉冲**。这个脉冲会将比特在 X-Y 平面上的状态绕 X 轴（或 Y 轴）翻转180度。这个操作的效果是“反转”了之前累积的相位。原本跑得快的比特现在会“向后跑”，跑得慢的会“向前追”。
5.  再让比特自由演化 **`t_delay / 2`** 的时间。在这段时间里，之前失相的过程被完美地逆转，所有比特的相位相对于中心频率重新“聚焦”到同一点。
6.  施加最后一个**π/2 脉冲**，将相位信息转回布居数。
7.  进行读出，并扫描总的演化时间 `t_delay`。

这个 `π/2 - wait - π - wait - π/2` 的过程就像赛跑中的“折返跑”，π 脉冲就是那个折返点，它让跑得快的选手需要往回跑更长的距离，最终使得所有选手能在同一时间点回到起点。通过这种方式，由起跑速度的微小差异（对应频率的准静态噪声）造成的影响就被消除了。

**2. `qlisp` 代码实现**

```python
# hahn_echo.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：已知 f_r, f_q, π 和 π/2 脉冲的参数
f_r = 6.05e9
f_q = 4.250e9 # 使用 Ramsey 校准后的精确频率
pi_pulse_amp = 0.85
pi_pulse_len = 40e-9
pi_half_pulse_amp = 0.425
pi_half_pulse_len = 40e-9

# 1. 定义 Hahn Echo 序列
# 我们将扫描总的演化时间 't_delay'
# 注意：qlisp 中需要将 t_delay 分为两半
hahn_echo_seq = [
    # 1. 第一个 π/2 脉冲
    PULSE(channel='Qubit_XY', waveform='gaussian', length=pi_half_pulse_len, frequency=f_q, amplitude=pi_half_pulse_amp),

    # 2. 等待 t_delay / 2
    WAIT(duration=var('t_delay') / 2),

    # 3. π 脉冲 (Echo Pulse)
    PULSE(channel='Qubit_XY', waveform='gaussian', length=pi_pulse_len, frequency=f_q, amplitude=pi_pulse_amp),

    # 4. 再等待 t_delay / 2
    WAIT(duration=var('t_delay') / 2),

    # 5. 第二个 π/2 脉冲
    PULSE(channel='Qubit_XY', waveform='gaussian', length=pi_half_pulse_len, frequency=f_q, amplitude=pi_half_pulse_amp),

    # 6. 读出
    PULSE(channel='Readout_Drive', waveform='square', length=400e-9, frequency=f_r),
    TRIG(channel='Measure_Trig', duration=400e-9)
]

# 2. 设置扫描参数
# T2 通常比 T2* 长，所以扫描范围可以更大
t_delay_sweep = np.linspace(0, 30e-6, 51)

# 3. 执行扫描
scan_params, scan_results = qclab_sweep(
    hahn_echo_seq,
    sweep_vars={'t_delay': t_delay_sweep},
    num_averages=1000
)

# 4. 数据分析
population_1 = process_readout_to_population(scan_results)

# (此处省略绘图和拟合代码)
# 对数据进行指数衰减拟合：
# y = A * exp(-x / T2) + B
# 拟合得到的 T2 时间常数即为 Hahn Echo T2

# t2_fit = fit_exponential_decay(t_delay_sweep, population_1)
# print(f"T2 (Hahn Echo) time: {t2_fit.T2:.2f} µs")

print("Hahn Echo 实验完成。")

```

**3. 代码讲解**

*   **序列结构**: 核心是 `π/2 - wait - π - wait - π/2` 结构。这是所有自旋回波类动态解耦序列的基础。
*   `WAIT(duration=var('t_delay') / 2)`: `qlisp` 编译器需要能够处理参数的算术运算。我们将总的演化时间 `t_delay` 在代码中明确地一分为二，分别赋给 π 脉冲前后的两个 `WAIT` 指令。
*   **π 脉冲**: 序列中间的 π 脉冲是实现“回波”的关键。它必须被精确校准，否则翻转将不完全，导致重聚焦效果不佳，从而低估真实的 T2。
*   **数据拟合**: 与 T1 实验类似，Hahn Echo 的结果是一个简单的指数衰减曲线（因为由失谐 `Δf` 引起的振荡也被 π 脉冲消除了）。我们使用标准的指数衰减函数对其进行拟合，提取出 T2 时间。

通过比较 T1, T2* 和 T2，我们可以对量子比特的退相干机制有一个初步的诊断。例如，如果 T2 远大于 T2*，则说明低频噪声是主要的退相干来源。

## 第五章：门校准与优化

在测量了比特基本的相干时间后，我们的目标是实现尽可能高的量子门保真度。标准的脉冲（如高斯脉冲）虽然有效，但仍有优化的空间。本章将介绍一些高级的校准技术，以进一步提升单比特门的性能，并初步探索双比特门。

### 5.1 单比特门优化 (DRAG 校准)

**1. 物理原理与目的**

**问题背景：**

一个理想的量子比特只有两个能级 `|0⟩` 和 `|1⟩`。然而，真实的物理系统（如超导transmon比特）实际上是一个**非谐振子**，它拥有无穷多的能级 `|0⟩, |1⟩, |2⟩, ...`。虽然 `|0⟩-|1⟩` 的跃迁频率 `f_q` 与 `|1⟩-|2⟩` 的跃迁频率 `f_12` 不同（其差值被称为**非谐性 `α`**），但当我们用一个频率为 `f_q` 的脉冲驱动比特时，如果脉冲的频谱不够窄（例如，脉冲时间很短），或者功率过高，脉冲的频谱成分仍然可能会“泄露”到 `|1⟩-|2⟩` 的跃迁上，导致比特被错误地激发到 `|2⟩` 态。这种错误被称为**泄露（Leakage）**。

**DRAG (Derivative Removal by Adiabatic Gate)** 是一种脉冲整形技术，其目的就是**抑制这种泄露错误**。

**DRAG 的核心思想：**

标准的驱动脉冲只作用于一个正交分量（例如，I 分量）。DRAG 技术则在另一个正交分量（Q 分量）上，额外施加一个与主脉冲包络的**导数**成正比的修正脉冲。这个修正脉冲经过精心设计，其产生的抵消场刚好可以抑制掉到 `|2⟩` 态的虚部跃迁，从而最大程度地减少泄露。

**实验目的：**

*   **校准 DRAG 参数 `β`：** 找到最佳的修正脉冲幅度（由参数 `β` 或 `alpha` 控制），使得泄露到 `|2⟩` 态的概率最小。

**实验过程（一种简单的校准方法）：**

1.  将比特初始化到 `|0⟩` 态。
2.  连续施加两个脉冲：一个 X90 脉冲，紧接着一个 Y90 脉冲（或反之）。理论上，这个 `Y90 * X90` 的组合操作后，比特应该处于一个特定的状态。
3.  但是，如果存在泄露，这个最终状态会偏离预期的位置。
4.  我们扫描 DRAG 参数 `β`，重复上述 `Y90 * X90` 操作，并测量最终的比特状态。
5.  当 `β` 取到最佳值时，泄露被最大程度抑制，最终的测量结果会最接近理论值。

**2. `qlisp` 代码实现**

在 `qlisp` 中，DRAG 脉冲通常是硬件或波形生成库内建支持的。我们只需要在 `PULSE` 指令中指定波形为 `gaussian_drag` 或类似名称，并传入 `beta` 参数即可。

```python
# drag_calibration.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep

# 前提：所有基础参数已知
f_r, f_q = 6.05e9, 4.250e9
pi_half_pulse_amp, pi_half_pulse_len = 0.425, 40e-9

# 1. 定义 DRAG 校准序列
# 我们将扫描 X90 脉冲中的 DRAG 参数 'beta'
# 序列是 X90 - Y90 - Readout
# 注意：Y90 脉冲通常是通过给 X90 脉冲增加 pi/2 的相位来实现
drag_cal_seq = [
    # 1. X90 脉冲，带有 DRAG 修正
    PULSE(channel='Qubit_XY',
          waveform='gaussian_drag', # 指定使用 DRAG 波形
          length=pi_half_pulse_len,
          frequency=f_q,
          amplitude=pi_half_pulse_amp,
          phase=0,                  # X 脉冲相位为 0
          beta=var('beta')),      # 扫描 DRAG 参数

    # 2. Y90 脉冲，也带有 DRAG 修正
    PULSE(channel='Qubit_XY',
          waveform='gaussian_drag',
          length=pi_half_pulse_len,
          frequency=f_q,
          amplitude=pi_half_pulse_amp,
          phase=90,                 # Y 脉冲相位为 90 度
          beta=var('beta')),

    # 3. 读出
    PULSE(channel='Readout_Drive', waveform='square', length=400e-9, frequency=f_r),
    TRIG(channel='Measure_Trig', duration=400e-9)
]

# 2. 设置扫描参数
# 扫描 beta 值，通常在 -1 到 1 的范围内
beta_sweep = np.linspace(-1.0, 1.0, 101)

# 3. 执行扫描
scan_params, scan_results = qclab_sweep(
    drag_cal_seq,
    sweep_vars={'beta': beta_sweep},
    num_averages=1000
)

# 4. 数据分析
population_1 = process_readout_to_population(scan_results)

# (此处省略绘图和拟合代码)
# 绘制 population_1 vs. beta_sweep 曲线
# 理论上，当 beta 最优时，泄露最小，比特状态最纯净，
# 此时的测量结果会呈现一个极值（最大值或最小值，取决于具体序列）

# optimal_beta = find_extremum(beta_sweep, population_1)
# print(f"Optimal DRAG beta parameter: {optimal_beta:.4f}")

print("DRAG calibration 完成。")

```

**3. 代码讲解**

*   `waveform='gaussian_drag'`: 我们显式地调用了支持 DRAG 的波形。这会告诉波形生成器去计算并合成 I 和 Q 两路信号。
*   `beta=var('beta')`: `beta` (有时也叫 `alpha` 或 `drag_scale`) 是控制 Q 路修正脉冲幅度的关键参数，也是我们的扫描对象。
*   `phase=90`: 实现 Y90 脉冲最简单的方式，就是将 X90 脉冲的载波相位整体偏移 90 度。`PULSE` 指令通常都支持 `phase` 参数。
*   **校准序列**: `X90-Y90` 只是众多 DRAG 校准序列中的一种（例如 ALLXY 序列）。其核心思想是设计一个理论上结果已知（例如，最终回到 `|0⟩` 或 `|1⟩`），但对泄露误差敏感的脉冲序列。通过调整 `beta` 来让实际测量结果最接近理论值，我们就能找到最佳的 DRAG 参数。

经过 DRAG 校准后，单比特门的保真度通常会有显著的提升，为后续更复杂的实验（如 Randomized Benchmarking 和双比特门操作）打下坚实的基础。

### 5.2 单比特门保真度评估 (Clifford Randomized Benchmarking - RB)

**1. 物理原理与目的**

到目前为止，我们已经校准了频率、时间和脉冲形状，但我们如何给量子门的“好坏”一个定量的评价？一个门的**保真度（Fidelity）**有多高？这就是 Randomized Benchmarking (RB) 要解决的问题。

**实验目的：**

*   **测量平均门保真度：** 得到一个可靠的、可与其他系统比较的数字，来描述我们实现的单比特 Clifford 门的平均误差率。
*   **SPAM 错误不敏感：** RB 的一个巨大优势是，其测量结果在很大程度上独立于状态制备（**S**tate **P**reparation）和测量（**A**nd **M**easurement）本身引入的误差（SPAM error）。它衡量的是门操作过程中的误差。

**实验过程：**

RB 的过程比较复杂，但核心思想是“做随机的事，然后把它反转回来”。

1.  **选择 Clifford 门集：** Clifford 门是一组特殊的量子门，它们的重要特性是任何 Clifford 门的组合仍然是一个 Clifford 门。对于单比特，这组门包括 I, X, Y, Z, H, S 等基本操作的组合。
2.  **生成随机序列：** 随机地从 Clifford 门集中挑选出一系列（`m` 个）门，并将它们作用于初始为 `|0⟩` 态的比特上。
3.  **计算反转门：** 由于 Clifford 群的封闭性，我们可以计算出这 `m` 个随机门操作的净效果，并找到一个**唯一的**“反转门”，它能把经过 `m` 次随机操作后的状态精确地送回到初始的 `|0⟩` 态。
4.  **执行并测量：** 在 `m` 个随机门之后，施加这个计算出的反转门，然后测量比特的状态。如果所有的门都是完美的，那么最终测量的结果**永远**应该是 `|0⟩`。
5.  **扫描序列长度 `m`：** 重复以上过程，但使用不同长度 `m` 的随机序列。随着 `m` 的增加，序列中累积的误差也会增加，导致最终结果偏离 `|0⟩` 的概率变大。
6.  **多次随机化：** 对于每一个长度 `m`，我们都需要生成许多个不同的随机序列（例如 `k` 次），并对结果进行平均，以消除特定序列带来的偏差。

通过绘制“存活概率”（即最终测得 `|0⟩` 的概率）随序列长度 `m` 变化的曲线，我们会得到一个指数衰减曲线。这个衰减率 `p` 与门的平均保真度 `F` 直接相关。

**2. `qlisp` 代码实现**

RB 的实现严重依赖于软件层。`qlisp` 本身只负责执行最终生成的脉冲序列。真正的复杂性在于生成随机 Clifford 序列和计算反转门。我们假设 `QCLab` 提供了一个高级的 RB 模块来处理这些逻辑。

```python
# randomized_benchmarking.py

import numpy as np
# 假设 QCLab 提供了 RB 工具集
from qclab.benchmarking import RandomizedBenchmarking
from qclab.execution import qclab_run

# 1. 初始化 RB 实验
# 指定要进行 RB 的比特
rb_experiment = RandomizedBenchmarking(qubit='Q0')

# 2. 设置 RB 参数
# 序列长度 m 的扫描列表
sequence_lengths = [2, 4, 8, 16, 32, 64, 128, 256]
# 每个长度 m 重复的随机序列个数 k
num_sequences_per_length = 50

# 3. 生成 RB 序列
# 这个函数会处理所有的 Clifford 群运算和反转门计算
# 它返回一个列表，每个元素都是一个可以直接被 qlisp 执行的脉冲序列
all_pulse_sequences = rb_experiment.generate_sequences(
    lengths=sequence_lengths, 
    num_repeats=num_sequences_per_length
)

# 4. 执行所有序列
all_results = []
for seq in all_pulse_sequences:
    # 每个序列都需要多次平均以获得概率
    result = qclab_run(seq, num_averages=500)
    all_results.append(result)

# 5. 数据分析
# 分析模块会根据序列长度对结果进行分组，计算存活概率，并进行拟合
survival_probabilities = rb_experiment.analyze_results(all_results)

# (此处省略绘图和拟合代码)
# 对 survival_probabilities vs. sequence_lengths 数据进行指数衰减拟合：
# y = A * p^m + B
# 拟合得到的衰减率 p 与平均门保真度 F 的关系为：
# F = 1 - (1 - p) * (d - 1) / d  (其中 d=2，因为是单比特)

# rb_fit = fit_rb_decay(sequence_lengths, survival_probabilities)
# gate_fidelity = 1 - (1 - rb_fit.p) / 2
# print(f"Average Clifford Gate Fidelity: {gate_fidelity * 100:.3f}%")

print("Randomized Benchmarking 完成。")

```

**3. 代码讲解**

*   `RandomizedBenchmarking(qubit='Q0')`: 我们假设有一个专门的类来处理 RB 的复杂逻辑。用户只需要指定目标比特。
*   `generate_sequences(...)`: 这是 RB 的核心。它封装了所有的数学细节：随机选择 Clifford 元素、将它们相乘、计算逆元素、然后将这些抽象的门操作编译成具体的、经过校准的 `qlisp` 脉冲序列（例如，使用 DRAG 脉冲）。
*   **执行循环**: RB 实验需要执行大量的序列。代码需要遍历 `generate_sequences` 生成的所有脉冲序列，并逐一运行。
*   `analyze_results(...)`: 分析过程同样被抽象。它负责将原始的测量结果（0或1）与它们所属的序列长度 `m` 对应起来，计算出每个 `m` 点的平均存活概率。
*   **拟合与保真度计算**: 最终的拟合公式 `y = A * p^m + B` 中，`A` 和 `B` 与 SPAM 误差有关，而 `p` 则反映了每个 Clifford 门的平均去极化（depolarizing）概率。通过公式 `F = 1 - (1 - p)/2`，我们可以将 `p` 转换为我们最终关心的平均门保真度 `F`。

RB 是一个强大的工具，它给出的数字是衡量和改进量子处理器性能的黄金标准。

### 5.3 双比特门介绍与校准

**1. 物理原理与目的**

单比特门只能操控单个量子比特，要实现通用的量子计算，我们必须能够让比特之间产生**纠缠**，这需要通过**双比特门**来实现。双比特门是量子算法（如 Shor 算法、Grover 算法）的基石，也是构建更复杂量子处理器的最大挑战之一。

**CPHASE (Controlled-Phase) 门简介:**

CPHASE 门是一种基础的双比特门。它的作用是：当**控制比特**处于 `|1⟩` 态时，给**目标比特**的 `|1⟩` 态施加一个额外的相位 `φ`。其矩阵表示为：

```
[[1, 0, 0, 0],
 [0, 1, 0, 0],
 [0, 0, 1, 0],
 [0, 0, 0, exp(iφ)]]
```

当 `φ = π` 时，这个门被称为 **CZ (Controlled-Z)** 门，是通用量子计算所需的一组标准门之一。

**物理实现:**

在超导比特中，实现 CPHASE 门的一种常见方法是：通过外部控制（例如，快速调节其中一个比特的频率，或者打开一个耦合器），让两个原本独立的量子比特在一段时间内发生强烈的相互作用。通过精确控制相互作用的**强度**和**时间**，可以使得 `|11⟩` 这个状态（即两个比特都处于 `|1⟩` 态）相对于其他状态（`|00⟩`, `|01⟩`, `|10⟩`）累积一个特定的相位 `φ`。

**实验目的：**

*   **校准 CPHASE/CZ 门：** 找到合适的脉冲参数（如相互作用的幅度和时长），以实现一个高保真度的 CPHASE 或 CZ 门。

**实验过程（概念性）：**

校准双比特门是一个多维度的扫描过程，比单比特校准复杂得多。一个简化的校准流程（称为 **Chevron 图样**）如下：

1.  将两个比特（Q0, Q1）都初始化到 `|00⟩`。
2.  对其中一个比特（例如 Q1）施加一个 π 脉冲，将其制备到 `|01⟩` 态。
3.  施加一个**相互作用脉冲**，这个脉冲会暂时改变比特间的耦合强度或使它们的频率共振。我们需要扫描这个脉冲的两个关键参数：**幅度 `amp_int`** 和 **时长 `t_int`**。
4.  相互作用结束后，对 Q1 再次施加一个 π 脉冲。
5.  测量 Q1 的最终状态。

通过在 `(t_int, amp_int)` 这个二维平面上扫描并绘制 Q1 的最终状态，我们会得到一个特征性的“人”字形或“V”字形图样（Chevron Pattern）。这个图样的振荡模式揭示了两个比特是如何交换能量的。通过分析这个图样，我们可以找到实现特定操作（如 iSWAP 或 CPHASE）所需的参数点。

**2. `qlisp` 代码实现 (概念性 Chevron 扫描)**

```python
# chevron_pattern.py

import numpy as np
from qlisp import *
from qclab.sweeping import qclab_sweep_2d # 假设有2D扫描函数

# 前提：已知所有单比特参数
f_q0, f_q1 = 4.250e9, 4.150e9
pi_pulse_amp_q1 = 0.88

# 1. 定义双比特门校准序列
# 我们将扫描相互作用脉冲的幅度和时长
chevron_seq = [
    # 1. 将 Q1 制备到 |1> 态
    PULSE(channel='Qubit1_XY', waveform='gaussian_drag', ..., amplitude=pi_pulse_amp_q1),

    # 2. 施加相互作用脉冲 (例如，通过给 Q0 施加一个方波脉冲来拉动它的频率)
    PULSE(channel='Qubit0_Z', # 作用在 Z 控制线上，用于快速调频
          waveform='square',
          length=var('t_int'),    # 扫描时长
          amplitude=var('amp_int')), # 扫描幅度

    # 3. 测量 Q1 的状态 (这里省略了最后的 pi 脉冲以简化)
    PULSE(channel='Readout_Drive_Q1', ...),
    TRIG(channel='Measure_Trig_Q1', ...)
]

# 2. 设置二维扫描参数
t_int_sweep = np.linspace(10e-9, 200e-9, 51)
amp_int_sweep = np.linspace(-0.5, 0.5, 41)

# 3. 执行二维扫描
# sweep_vars 需要一个字典，key 是参数名，value 是扫描数组
scan_params, scan_results = qclab_sweep_2d(
    chevron_seq,
    sweep_vars={'t_int': t_int_sweep, 'amp_int': amp_int_sweep},
    num_averages=500
)

# 4. 数据分析
# scan_results 将是一个 2D 数组
# 使用 pcolormesh 或 imshow 绘制二维的 Chevron 图样
# (此处省略绘图代码)

# 从图样中找到目标操作（如 CZ 门）对应的 (t_int, amp_int) 参数点
# cz_params = find_cz_point(scan_params, scan_results)
# print(f"CZ gate parameters found at: t={cz_params.t_int}, amp={cz_params.amp_int}")

print("Chevron pattern scan 完成。")

```

**3. 代码讲解**

*   `qclab_sweep_2d`: 双比特门校准通常需要在多维参数空间中搜索，因此一个支持二维（甚至更高维度）扫描的函数是必不可少的。
*   `PULSE(channel='Qubit0_Z', ...)`: 这是一种实现相互作用的常见方式。通过在 Z 控制线上施加一个直流脉冲，我们可以快速地将 Q0 的频率“拉”到与 Q1 共振或接近共振的位置，从而“打开”它们之间的相互作用。
*   **二维扫描**: `sweep_vars` 现在包含两个键值对，`qclab_sweep_2d` 会执行一个嵌套循环，遍历 `t_int` 和 `amp_int` 的所有组合。
*   **从 Chevron 到门**: Chevron 图样本身只是一个诊断工具。要真正校准一个高保真度的 CZ 门，还需要在找到的参数点附近进行更精细的优化，例如使用双比特的 Randomized Benchmarking，但这已经超出了本入门手册的范围。

完成双比特门的初步校准，是从“物理”迈向“计算”的关键一步。它使得我们能够构建真正的量子算法，探索量子世界更深层的奥秘。
