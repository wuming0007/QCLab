import time

import numpy as np
from quark.app import Recipe, s

s.login()


def circuit(qubits: list[str], ctx=None) -> list:
    cc = [(('Measure', i, ), q) for i, q in enumerate(qubits)]
    return cc


def calibrate(qubits: list[str]) -> list:
    qubits = [f'Q{i}' for i in [999]]
    rcp = Recipe('s21', signal='iq_avg')
    rcp.lib = 'lib.gates.u3rcp'
    rcp.arch = 'rcp'
    rcp.circuit = circuit

    rcp['qubits'] = tuple(qubits)
    # rcp['amp'] = np.linspace(0,0.05,21)
    rcp['freq'] = np.linspace(-10, 10, 101) * 1e6
    # rcp['state'] = ['0', '1']

    for q in qubits:
        # rcp[f'gate.Measure.{q}.params.amp'] = rcp['amp']
        rcp[f'{q}.Measure.frequency'] = rcp['freq'] + \
            s.query(f'{q}.Measure.frequency')
        # rcp[f'gate.Measure.{q}.default_type'] = 'default'

    # for i in range(100):
    s21 = s.submit(rcp.export(), block=True, preview=['3M1'], plot=False)
    s21.bar(interval=1)
    return s21.result(), s21.tid


def analyze(result: dict, level: str = 'check') -> dict:
    fitted = {'Q0.param.frequency': 5e9}
    return fitted


def diagnose(result: dict, level: str = 'check', history: list = []) -> dict:

    def f(): return float((4.4 + np.random.randn(1)) * 1e9)

    summary = {'Q0': ('red', f()), 'Q1': ('green', f()),
               'Q5': ('green', f()), 'Q8': ('red', f())}  # 所有比特
    #    'adaptive_args': {'Q0': [], 'Q1': []}  # 下次扫描参数
    #   'group': ('Q0', 'Q1', 'Q5', 'Q8') # 动态分组备用
    #    }

    return summary


def update(summary: dict):
    """
    Update the summary of the calibration results.
    This function is a placeholder and does not perform any actual update.
    """
    # for t, (status, value) in summary.items():
    #     if status == 'green':
    #         exp.s.update()
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] updated!', summary)
