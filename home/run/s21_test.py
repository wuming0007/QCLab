import time

import numpy as np
from quark.app import Recipe, s

s.login()


def circuit(qubits: list[str], ctx=None) -> list:
    """
    为给定的量子比特定义一个测量电路。
    
    Args:
        qubits (list[str]): 要测量的量子比特名称列表。
        ctx: 可选上下文，此处未使用。
    
    Returns:
        list: 电路描述，作为操作列表。
    """
    cc = [(('Measure', i, ), q) for i, q in enumerate(qubits)]
    return cc


def calibrate(qubits: list[str]) -> list:
    """
    在指定的量子比特上执行 S21 校准扫描。
    
    Args:
        qubits (list[str]): 要校准的量子比特列表。
    
    Returns:
        tuple: (结果字典, 任务 ID)
    """
    rcp = Recipe('s21', signal='iq_avg')
    rcp.lib = 'lib.gates.u3rcp'
    rcp.arch = 'rcp'
    rcp.circuit = circuit

    rcp['qubits'] = tuple(qubits)
    rcp['freq'] = np.linspace(-10, 10, 101) * 1e6

    for q in qubits:
        rcp[f'{q}.Measure.frequency'] = rcp['freq'] + \
            s.query(f'{q}.Measure.frequency')

    s21 = s.submit(rcp.export(), block=True, preview=['3M1'], plot=False)
    s21.bar(interval=1)
    return s21.result(), s21.tid


def analyze(result: dict, level: str = 'check') -> dict:
    """
    分析校准结果以拟合参数。
    
    Args:
        result (dict): 来自校准的原始结果。
        level (str): 分析级别，默认 'check'。
    
    Returns:
        dict: 每个量子比特的拟合参数。
    """
    fitted = {}
    for q in result['qubits']:
        # Placeholder for actual fitting logic
        fitted[f'{q}.param.frequency'] = 5e9 + np.random.randn() * 1e6
    return fitted


def diagnose(result: dict, level: str = 'check', history: list = []) -> dict:
    """
    基于结果诊断量子比特的状态。
    
    Args:
        result (dict): 校准结果。
        level (str): 诊断级别，默认 'check'。
        history (list): 可选历史，此处未使用。
    
    Returns:
        dict: 每个量子比特的状态和值摘要。
    """
    def f(): return float((4.4 + np.random.randn(1)) * 1e9)

    summary = {}
    for q in result['qubits']:
        status = 'green' if np.random.rand() > 0.3 else 'red'
        summary[q] = (status, f())
    return summary


def update(summary: dict):
    """
    基于诊断摘要更新系统参数。
    
    Args:
        summary (dict): 诊断摘要。
    """
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] updated!', summary)

def test_s21_functions():
    """简单的测试函数来验证脚本组件。"""
    test_qubits = ['QTest1', 'QTest2']
    # Mock result for testing
    mock_result = {'qubits': test_qubits, 'data': 'mock_data'}
    fitted = analyze(mock_result)
    assert len(fitted) == len(test_qubits), "Analyze failed"
    summary = diagnose(mock_result)
    assert len(summary) == len(test_qubits), "Diagnose failed"
    print("Tests passed!")

if __name__ == "__main__":
    # qubits = ['Q0', 'Q1']  # Example qubits
    # result, tid = calibrate(qubits)
    # fitted = analyze(result)
    # summary = diagnose(result)
    # update(summary)
    # print("S21 test completed.")
    test_s21_functions() 