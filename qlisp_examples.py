#!/usr/bin/env python3
"""
QLisp 使用示例脚本
演示各种量子电路的基本操作
"""

import qlisp
import qlisp.circuits as qc
import numpy as np

def demo_basic_gates():
    """演示基本量子门的使用"""
    print("=== 基本量子门演示 ===")
    
    # 单比特门
    single_qubit_circuit = [
        (qlisp.H, 'Q0'),
        (qlisp.sigmaX, 'Q1'),
        (qlisp.sigmaY, 'Q2'),
        (qlisp.sigmaZ, 'Q3'),
    ]
    
    print("单比特门电路:")
    for gate, qubit in single_qubit_circuit:
        gate_name = gate.__name__ if hasattr(gate, '__name__') else str(type(gate).__name__)
        print(f"  {gate_name} -> {qubit}")
    
    # 双比特门
    two_qubit_circuit = [
        (qlisp.CX, ('Q0', 'Q1')),
        (qlisp.CZ, ('Q1', 'Q2')),
        (qlisp.SWAP, ('Q2', 'Q3')),
    ]
    
    print("\n双比特门电路:")
    for gate, qubits in two_qubit_circuit:
        gate_name = gate.__name__ if hasattr(gate, '__name__') else str(type(gate).__name__)
        print(f"  {gate_name} -> {qubits}")

def demo_bell_states():
    """演示Bell态的制备"""
    print("\n=== Bell态演示 ===")
    
    # 制备Bell态 |Φ^+⟩
    bell_phi_plus = [
        (qlisp.H, 'Q0'),
        (qlisp.CX, ('Q0', 'Q1')),
    ]
    
    print("Bell态 |Φ^+⟩ 制备电路:")
    for gate, qubit in bell_phi_plus:
        gate_name = gate.__name__ if hasattr(gate, '__name__') else str(type(gate).__name__)
        if isinstance(qubit, tuple):
            print(f"  {gate_name} -> {qubit}")
        else:
            print(f"  {gate_name} -> {qubit}")
    
    # 测量Bell态
    measurement = [
        (qlisp.measure, 'Q0'),
        (qlisp.measure, 'Q1'),
    ]
    
    print("\n测量操作:")
    for op, qubit in measurement:
        op_name = op.__name__ if hasattr(op, '__name__') else str(type(op).__name__)
        print(f"  {op_name} -> {qubit}")

def demo_quantum_algorithms():
    """演示量子算法电路"""
    print("\n=== 量子算法演示 ===")
    
    # 量子隐形传态
    teleport_circuit = [
        # 步骤1：制备Bell态
        (qlisp.H, 'Q0'),
        (qlisp.CX, ('Q0', 'Q1')),
        
        # 步骤2：Alice的Bell测量
        (qlisp.CX, ('Q2', 'Q0')),
        (qlisp.H, 'Q2'),
        (qlisp.measure, 'Q2'),
        (qlisp.measure, 'Q0'),
        
        # 步骤3：Bob的条件操作
        (qlisp.sigmaX, 'Q1'),
        (qlisp.sigmaZ, 'Q1'),
    ]
    
    print("量子隐形传态电路:")
    for i, (gate, qubit) in enumerate(teleport_circuit):
        gate_name = gate.__name__ if hasattr(gate, '__name__') else str(type(gate).__name__)
        if isinstance(qubit, tuple):
            print(f"  {i+1:2d}. {gate_name} -> {qubit}")
        else:
            print(f"  {i+1:2d}. {gate_name} -> {qubit}")

def demo_predefined_circuits():
    """演示预定义电路"""
    print("\n=== 预定义电路演示 ===")
    
    # 动态解耦序列
    print("可用的动态解耦序列:")
    dd_sequences = ['XY4', 'XY8', 'XY16', 'Ramsey', 'SpinEcho', 'CPMG', 'UDD']
    for seq in dd_sequences:
        print(f"  - {seq}")
    
    # 量子层析
    print("\n可用的量子层析:")
    tomography_methods = ['QPT', 'QST']
    for method in tomography_methods:
        print(f"  - {method}")

def demo_circuit_operations():
    """演示电路操作"""
    print("\n=== 电路操作演示 ===")
    
    # 创建简单电路
    circuit = [
        (qlisp.H, 'Q0'),
        (qlisp.CX, ('Q0', 'Q1')),
        (qlisp.measure, 'Q0'),
        (qlisp.measure, 'Q1'),
    ]
    
    print("电路结构:")
    for i, (gate, qubit) in enumerate(circuit):
        gate_name = gate.__name__ if hasattr(gate, '__name__') else str(type(gate).__name__)
        if isinstance(qubit, tuple):
            print(f"  {i+1:2d}. {gate_name} -> {qubit}")
        else:
            print(f"  {i+1:2d}. {gate_name} -> {qubit}")
    
    # 电路长度
    print(f"\n电路深度: {len(circuit)}")
    
    # 统计门类型
    gate_counts = {}
    for gate, _ in circuit:
        gate_name = gate.__name__ if hasattr(gate, '__name__') else str(type(gate).__name__)
        gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1
    
    print("门统计:")
    for gate, count in gate_counts.items():
        print(f"  {gate}: {count}")

def demo_advanced_features():
    """演示高级特性"""
    print("\n=== 高级特性演示 ===")
    
    # 自定义门
    print("自定义门:")
    print("  - U: 通用单比特门")
    print("  - A, B: 自定义门")
    print("  - fSim: Fermionic Simulation门")
    
    # 特殊操作
    print("\n特殊操作:")
    print("  - KAK分解: kak_decomposition()")
    print("  - 电路转矩阵: seq2mat()")
    print("  - 电路绘制: draw()")
    print("  - 全局相位同步: synchronize_global_phase()")

def main():
    """主函数"""
    print("QLisp 量子线路语法演示")
    print("=" * 50)
    
    demo_basic_gates()
    demo_bell_states()
    demo_quantum_algorithms()
    demo_predefined_circuits()
    demo_circuit_operations()
    demo_advanced_features()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("\n使用提示:")
    print("1. 导入: import qlisp")
    print("2. 创建电路: circuit = [(gate, qubit), ...]")
    print("3. 使用预定义电路: import qlisp.circuits as qc")
    print("4. 参考完整语法指南: qlisp_syntax_guide.md")

if __name__ == "__main__":
    main() 