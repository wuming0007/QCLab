# QLisp 量子线路语法指南

QLisp 是 QuarkStudio 项目中使用的量子线路语法规范，用于描述和操作量子计算电路。

## 目录
- [基本概念](#基本概念)
- [量子门](#量子门)
- [Bell态](#bell态)
- [电路表示](#电路表示)
- [测量操作](#测量操作)
- [预定义电路](#预定义电路)
- [工具函数](#工具函数)
- [示例](#示例)

## 基本概念

QLisp 使用列表（List）来表示量子电路，每个元素代表一个量子操作：
- 单比特门：`(gate, qubit)`
- 双比特门：`(gate, (qubit1, qubit2))`
- 测量操作：`(measure, qubit)`

## 量子门

### 单比特门

| 门 | 描述 | 矩阵表示 |
|---|---|---|
| `H` | Hadamard门 | $\frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$ |
| `sigmaX` | Pauli-X门 | $\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$ |
| `sigmaY` | Pauli-Y门 | $\begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}$ |
| `sigmaZ` | Pauli-Z门 | $\begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$ |
| `S` | S门 | $\begin{pmatrix} 1 & 0 \\ 0 & i \end{pmatrix}$ |
| `Sdag` | S门的共轭转置 | $\begin{pmatrix} 1 & 0 \\ 0 & -i \end{pmatrix}$ |
| `T` | T门 | $\begin{pmatrix} 1 & 0 \\ 0 & e^{i\pi/4} \end{pmatrix}$ |
| `Tdag` | T门的共轭转置 | $\begin{pmatrix} 1 & 0 \\ 0 & e^{-i\pi/4} \end{pmatrix}$ |

### 双比特门

| 门 | 描述 | 作用比特 |
|---|---|---|
| `CX` | CNOT门 | 控制比特 → 目标比特 |
| `CZ` | CZ门 | 控制比特 → 目标比特 |
| `SWAP` | SWAP门 | 交换两个比特 |
| `iSWAP` | iSWAP门 | 交换 + 相位 |
| `SQiSWAP` | 平方根iSWAP门 | iSWAP的平方根 |
| `CR` | 受控旋转门 | 控制比特 → 目标比特 |

### 特殊门

| 门 | 描述 |
|---|---|
| `U` | 通用单比特门 |
| `A`, `B` | 自定义门 |
| `fSim` | fSim门（Fermionic Simulation） |

## Bell态

QLisp 提供了预定义的 Bell 态：

| 态 | 描述 | 数学表示 |
|---|---|---|
| `phiplus` | $|\Phi^+\rangle$ | $\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$ |
| `phiminus` | $|\Phi^-\rangle$ | $\frac{1}{\sqrt{2}}(|00\rangle - |11\rangle)$ |
| `psiplus` | $|\Psi^+\rangle$ | $\frac{1}{\sqrt{2}}(|01\rangle + |10\rangle)$ |
| `psiminus` | $|\Psi^-\rangle$ | $\frac{1}{\sqrt{2}}(|01\rangle - |10\rangle)$ |
| `BellPhiP` | Bell态 $\Phi^+$ | 同 `phiplus` |
| `BellPhiM` | Bell态 $\Phi^-$ | 同 `phiminus` |
| `BellPsiP` | Bell态 $\Psi^+$ | 同 `psiplus` |
| `BellPsiM` | Bell态 $\Psi^-$ | 同 `psiminus` |

## 电路表示

### 基本语法

```python
import qlisp

# 单比特门
circuit = [
    (qlisp.H, 'Q0'),           # Hadamard门作用于Q0
    (qlisp.sigmaX, 'Q1'),      # X门作用于Q1
]

# 双比特门
circuit = [
    (qlisp.CX, ('Q0', 'Q1')),  # CNOT门：Q0控制Q1
    (qlisp.SWAP, ('Q1', 'Q2')), # SWAP门：交换Q1和Q2
]

# 混合电路
circuit = [
    (qlisp.H, 'Q0'),
    (qlisp.CX, ('Q0', 'Q1')),
    (qlisp.measure, 'Q0'),
    (qlisp.measure, 'Q1'),
]
```

### 复杂电路示例

```python
# Bell态制备电路
bell_circuit = [
    (qlisp.H, 'Q0'),
    (qlisp.CX, ('Q0', 'Q1')),
]

# 量子隐形传态电路
teleport_circuit = [
    # Alice和Bob共享Bell态
    (qlisp.H, 'Q0'),
    (qlisp.CX, ('Q0', 'Q1')),
    
    # Alice对要传输的量子比特和她的Bell态比特进行Bell测量
    (qlisp.CX, ('Q2', 'Q0')),
    (qlisp.H, 'Q2'),
    (qlisp.measure, 'Q2'),
    (qlisp.measure, 'Q0'),
    
    # Bob根据测量结果进行相应的操作
    (qlisp.sigmaX, 'Q1'),  # 条件操作
    (qlisp.sigmaZ, 'Q1'),  # 条件操作
]
```

## 测量操作

### 基本测量

```python
# 单比特测量
circuit = [
    (qlisp.measure, 'Q0'),
]

# 多比特测量
circuit = [
    (qlisp.measure, 'Q0'),
    (qlisp.measure, 'Q1'),
    (qlisp.measure, 'Q2'),
]
```

### 测量语法

- `(measure, qubit)`: 测量指定比特
- 测量结果通常以经典比特的形式返回
- 测量操作会坍缩量子态

## 预定义电路

QLisp 提供了多种预定义的电路模板：

### 量子过程层析 (QPT)
```python
import qlisp.circuits as qc

# 量子过程层析
qpt_circuit = qc.qpt(qubits=['Q0', 'Q1'])
```

### 量子态层析 (QST)
```python
# 量子态层析
qst_circuit = qc.qst(qubits=['Q0'])
```

### 动态解耦序列
```python
# XY4序列
xy4_circuit = qc.XY4(qubit='Q0', n_cycles=4)

# XY8序列
xy8_circuit = qc.XY8(qubit='Q0', n_cycles=4)

# XY16序列
xy16_circuit = qc.XY16(qubit='Q0', n_cycles=4)
```

### 其他序列
```python
# Ramsey序列
ramsey_circuit = qc.Ramsey(qubit='Q0')

# Spin Echo序列
spinecho_circuit = qc.SpinEcho(qubit='Q0')

# CPMG序列
cpmg_circuit = qc.CPMG(qubit='Q0', n_echoes=4)

# UDD序列
udd_circuit = qc.UDD(qubit='Q0', n_pulses=3)
```

## 工具函数

### 电路操作

| 函数 | 描述 |
|---|---|
| `draw(circuit)` | 绘制电路图 |
| `seq2mat(circuit)` | 将电路转换为矩阵 |
| `applySeq(circuit, state)` | 将电路应用于量子态 |

### 数学工具

| 函数 | 描述 |
|---|---|
| `kak_decomposition(matrix)` | KAK分解 |
| `kak_vector(matrix)` | 计算KAK向量 |
| `synchronize_global_phase(matrix1, matrix2)` | 同步全局相位 |

### 其他工具

| 函数 | 描述 |
|---|---|
| `make_immutable(obj)` | 使对象不可变 |
| `measure(qubit)` | 测量函数 |

## 示例

### 示例1：Bell态制备和测量

```python
import qlisp

# 制备Bell态 |Φ^+⟩
bell_circuit = [
    (qlisp.H, 'Q0'),
    (qlisp.CX, ('Q0', 'Q1')),
]

# 测量Bell态
measurement_circuit = [
    (qlisp.measure, 'Q0'),
    (qlisp.measure, 'Q1'),
]

# 完整电路
full_circuit = bell_circuit + measurement_circuit
```

### 示例2：量子隐形传态

```python
# 量子隐形传态电路
teleport_circuit = [
    # 步骤1：制备Bell态
    (qlisp.H, 'Q0'),
    (qlisp.CX, ('Q0', 'Q1')),
    
    # 步骤2：Alice的Bell测量
    (qlisp.CX, ('Q2', 'Q0')),
    (qlisp.H, 'Q2'),
    (qlisp.measure, 'Q2'),
    (qlisp.measure, 'Q0'),
    
    # 步骤3：Bob的条件操作（根据测量结果）
    (qlisp.X, 'Q1'),  # 如果Q2测量结果为1
    (qlisp.Z, 'Q1'),  # 如果Q0测量结果为1
]
```

### 示例3：量子傅里叶变换

```python
def qft_circuit(n_qubits):
    """n比特量子傅里叶变换电路"""
    circuit = []
    
    for i in range(n_qubits):
        circuit.append((qlisp.H, f'Q{i}'))
        for j in range(i + 1, n_qubits):
            # 添加受控相位门
            circuit.append((qlisp.CR, (f'Q{i}', f'Q{j}')))
    
    return circuit

# 3比特QFT
qft_3 = qft_circuit(3)
```

### 示例4：Grover算法

```python
def grover_oracle(marked_state):
    """Grover算法的Oracle"""
    circuit = []
    # 这里简化处理，实际需要根据marked_state构建Oracle
    circuit.append((qlisp.X, 'Q0'))
    circuit.append((qlisp.CZ, ('Q0', 'Q1')))
    circuit.append((qlisp.X, 'Q0'))
    return circuit

def grover_diffusion(n_qubits):
    """Grover算法的扩散算子"""
    circuit = []
    for i in range(n_qubits):
        circuit.append((qlisp.H, f'Q{i}'))
    for i in range(n_qubits):
        circuit.append((qlisp.X, f'Q{i}'))
    circuit.append((qlisp.CZ, ('Q0', 'Q1')))
    for i in range(n_qubits):
        circuit.append((qlisp.X, f'Q{i}'))
    for i in range(n_qubits):
        circuit.append((qlisp.H, f'Q{i}'))
    return circuit

# Grover算法电路
grover_circuit = grover_oracle('11') + grover_diffusion(2)
```

## 最佳实践

1. **命名规范**: 使用有意义的量子比特名称（如 'Q0', 'Q1', 'Alice', 'Bob'）
2. **电路结构**: 将复杂电路分解为子电路
3. **注释**: 为复杂的量子操作添加注释
4. **测试**: 使用小规模电路验证算法正确性
5. **优化**: 考虑电路深度和门数量优化

## 注意事项

1. **量子比特顺序**: 注意量子比特的编号和顺序
2. **门操作顺序**: 量子门的操作顺序很重要
3. **测量时机**: 测量会坍缩量子态，影响后续操作
4. **错误处理**: 考虑量子噪声和退相干效应
5. **硬件限制**: 考虑实际量子硬件的限制和约束

---

*本指南基于 QLisp 库的当前版本编写，如有更新请参考最新文档。* 