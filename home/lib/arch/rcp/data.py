import time

import numpy as np
from qlispc.base import Capture, QLispCode, Signal
from qlispc.commands import (COMMAND, READ, SYNC, TRIG, WRITE, CommandList,
                             DataMap, RawData, Result)
from qlispc.libs.readout import (classify_data, count_state, count_to_diag,
                                 install_classify_method)
from qlispc.tools.dicttree import flattenDictIter


def default_classify(data, params):
    """
    默认的分类方法
    """
    thr = params.get('threshold', 0)
    phi = params.get('phi', 0)
    return 1 + ((data * np.exp(-1j * phi)).real > thr)


install_classify_method("state", default_classify)


def _sort_cbits(raw_data, dataMap):
    ret = []
    gate_list = []
    cbits = sorted(dataMap)
    # min_shots = np.inf
    for cbit in cbits:
        ch, i, Delta, params, time, start, stop = dataMap[cbit]
        gate_list.append({'params': params})
        cbits[i] = cbit
        try:
            key = f'{ch}.IQ'
            if isinstance(raw_data[key], np.ndarray):
                ret.append(raw_data[key][..., i])
            else:
                raise ValueError('error on ad', str(raw_data[key]))
        except KeyError:
            key = f'{ch}.TraceIQ'
            ret.append(raw_data[key])
        # min_shots = min(min_shots, ret[-1].shape[0])

    # ret = [r[:min_shots] for r in ret]

    return np.asfortranarray(ret).T, gate_list, cbits


def _sort_data(raw_data, dataMap):
    ret = {}
    for label, channel in dataMap.items():
        if label in raw_data:
            ret[label] = raw_data['READ.' + channel]
    return ret


def _process_classify(data, gate_params_list, signal, classify):
    result = {}

    if signal & Signal._remote:
        if (signal & Signal.remote_trace_avg) == Signal.remote_trace_avg:
            result['remote_trace_avg'] = data
        elif (signal & Signal.remote_iq_avg) == Signal.remote_iq_avg:
            result['remote_iq_avg'] = data
        elif (signal & Signal.remote_count) == Signal.remote_count:
            pass
        elif (signal & Signal.remote_population) == Signal.remote_population:
            result['remote_population'] = data
        else:
            result['remote_state'] = data
        return result

    if signal & Signal.trace:
        if signal & Signal._avg_trace:
            result['trace_avg'] = data.mean(axis=-2)
        else:
            result['trace'] = data
        return result

    if signal & Signal.iq:
        if signal & Signal._avg_iq:
            result['iq_avg'] = data.mean(axis=-2)
        else:
            result['iq'] = data

    if signal & Signal.state:
        state = classify(data, gate_params_list, avg=False)
    if signal & Signal._count:
        count = count_state(state)

    if (signal & Signal.diag) == Signal.diag:
        result['diag'] = count_to_diag(count)
    elif (signal & Signal.count) == Signal.count:
        result['count'] = count
    elif (signal & Signal.population) == Signal.population:
        populations = np.array(
            [np.count_nonzero(state == 2**i, axis=-2) for i in range(8)])
        populations = populations / np.sum(populations, axis=0)
        result['population'] = []
        for gate_params, p in zip(gate_params_list, populations[1]):
            Pg, Pe = gate_params['params'].get('PgPe', [0, 1])
            p1 = (p - Pg) / (Pe - Pg)
            result['population'].append(p1)
        result['population'] = np.asarray(result['population'])
        for i in range(4):
            result[f'P{i}'] = populations[i]
        for i, gate_params in enumerate(gate_params_list):
            M = gate_params['params'].get('M', np.eye(4))
            q = np.linalg.inv(np.asarray(M)) @ populations[:M.shape[0], i]
            for j, v in enumerate(q):
                if f'Q{j}' in result:
                    result[f'Q{j}'].append(v)
                else:
                    result[f'Q{j}'] = [v]
    elif signal & Signal.state:
        result['state'] = state

    return result


def _get_classify_func(fun_name):
    dispatcher = {}
    try:
        return dispatcher[fun_name]
    except:
        return classify_data


def _sort_remote_count_data(raw_data, dataMap):

    def _resort(key, _data_mapping):
        return tuple([key[i] for i in _data_mapping])

    raw_count, sort_keys = None, []
    cbits = sorted(dataMap)
    for cbit in cbits:
        ch, i, Delta, params, time, start, stop = dataMap[cbit]
        sort_keys.append((ch, i, cbit))
        cbits[i] = cbit
        if ch + '.Counts' in raw_data.keys():
            raw_count = dict(raw_data[ch + '.Counts'])
    sort_rank = {k[-1]: i for i, k in enumerate(sorted(sort_keys))}
    sort_list = [sort_rank[cbit] for cbit in sorted(sort_rank)]

    ret = {}
    for item in raw_count.keys():
        ret[_resort(item, sort_list)] = raw_count[item]
    return ret, cbits


def assembly_data(raw_data: RawData, dataMap: DataMap) -> Result:
    if not dataMap:
        return raw_data

    result = {}

    def decode(value):
        if (isinstance(value, tuple) and len(value) == 2
                and isinstance(value[0], np.ndarray)
                and isinstance(value[1], np.ndarray)
                and value[0].shape == value[1].shape):
            return value[0] + 1j * value[1]
        else:
            return value

    try:
        ts = raw_data.pop('_ts_')
    except:
        ts = time.time_ns()

    raw_data = {k: decode(v) for k, v in flattenDictIter(raw_data)}
    if 'cbits' in dataMap:
        data, gate_params_list, cbits = _sort_cbits(raw_data, dataMap['cbits'])
        classify = _get_classify_func(gate_params_list[0].get(
            'classify', None))
        result.update(
            _process_classify(data, gate_params_list,
                              Signal(dataMap['signal']), classify))
        if (dataMap['signal']
                & Signal.remote_count.value) == Signal.remote_count.value:
            remote_count, cbits = _sort_remote_count_data(
                raw_data, dataMap['cbits'])
            result.update({'remote_count': remote_count})
    if 'data' in dataMap:
        result.update(_sort_data(raw_data, dataMap['data']))

    result['_ts_'] = [ts]

    return result
