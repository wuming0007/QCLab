import json
from pathlib import Path

import numpy as np


def dag():
    return {'task': get_task_graph(),
            'chip': {'group': {'0': ['Q0', 'Q1'], '1': ['Q5', 'Q8']}}
            }


def get_task_graph(name: str = 'Q0'):
    return {'nodes': {'s21': {'pos': (3, 1)},  # , 'pen': (135, 155, 75, 255, 5)
                      'Spectrum': {'pos': (3, 3)},
                      'Rabi': {'pos': (3, 5)},
                      'Ramsey': {'pos': (1, 8)},
                      'Scatter': {'pos': (5, 8)},
                      'RB': {'pos': (3, 10)}},

            'edges': {('s21', 'Spectrum'): {'name': ''},  # , 'pen': (155, 123, 255, 180, 2)
                      ('Spectrum', 'Rabi'): {'name': ''},
                      ('Rabi', 'Ramsey'): {'name': ''},
                      ('Rabi', 'Scatter'): {'name': ''},
                      ('Scatter', 'RB'): {'name': ''}},
            'check': {'period': 60, 'method': 'Ramsey'}
            }


def get_chip_graph():
    nodes = {}
    edges = {}
    for i in range(12):
        r, c = divmod(i, 3)
        nodes[f'Q{i}'] = {
            # 'name': f'Q{i}',
            # 'id': i,
            'pos': (r * 3, c * 3),
            'pen': (35, 155, 75, 255, 2),
            'value': {
                "params": {
                    "T1": 7.544957236854869e-05,
                    "T2_star": 1.9762589666408893e-05,
                    "T2_echo": 3.951455640774801e-05,
                    "chi": 0.525,
                    "Ec": None,
                    "T2star": 21.77932423416822
                }}}
        if i > 10 or i in [2, 5, 11]:
            continue
        edges[(f'Q{i}', f'Q{i + 1}')] = {'name': f'C{i}',
                                         'pen': (55, 123, 255, 180, 21),
                                         'value': {'b': np.random.random(1)[0] + 5, 'c': {'e': 134}, 'f': [(1, 2, 34)]}
                                         }
    return dict(nodes=nodes, edges=edges)


def get_history_data(path: str = ''):
    with open(Path.home() / 'Desktop/home/cfg/dag.json', 'r') as f:
        dag = json.loads(f.read())
        node, method = path.split('.')
        return np.array(dag[node][method]['history'])[:, -1].astype(float)
    return np.random.randn(101)
