import numpy as np
from qlispc import (COMMAND, READ, SYNC, TRIG, WRITE, Capture, CommandList,
                    DataMap, QLispCode, RawData, Result, Signal)

try:
    from waveforms.dicttree import flattenDictIter
except ImportError as e:
    from qlispc.tools.dicttree import flattenDictIter

from waveforms.math.fit import (classify_data, count_state, count_to_diag,
                                install_classify_method)


def default_classify(data, params):
    """
    默认的分类方法
    """
    thr = params.get('threshold', 0)
    phi = params.get('phi', 0)
    return 1 + ((data * np.exp(-1j * phi)).real > thr)


install_classify_method("state", default_classify)


def _sort_cbits(raw_data, dataMap):
    cbits_shape = {}
    ad_shape = {}

    for (name, index), (ch, sub_trig, i, Delta, params,
                        time) in dataMap.items():
        if name not in cbits_shape:
            cbits_shape[name] = 0
        cbits_shape[name] = max(cbits_shape[name], index + 1)

        if ch not in ad_shape:
            ad_shape[ch] = [0, 0]
        ad_shape[ch] = [
            max(ad_shape[ch][0], sub_trig + 1),
            max(ad_shape[ch][1], i + 1)
        ]

    ret = {name: [0] * size for name, size in cbits_shape.items()}
    gate_list = {name: [{}] * size for name, size in cbits_shape.items()}

    for (name, index), (ch, sub_trig, i, Delta, params,
                        time) in dataMap.items():
        gate_list[name][index] = params
        try:
            key = f'{ch}.IQ'
            if isinstance(raw_data[key], np.ndarray):
                shape = raw_data[key].shape[:-2]
                d = raw_data[key].reshape(*shape, -1, *ad_shape[ch])
                ret[name][index] = d[..., sub_trig, i]
            else:
                raise ValueError('error on ad', str(raw_data[key]))
        except KeyError:
            key = f'{ch}.TraceIQ'
            ret[name][index] = raw_data[key][..., sub_trig, :]

    ret = {k: np.asfortranarray(v).T for k, v in ret.items()}
    return ret, gate_list


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

    raw_data = {k: decode(v) for k, v in flattenDictIter(raw_data)}
    if 'cbits' in dataMap:
        data, gate_params_list = _sort_cbits(raw_data, dataMap['cbits'])
        for k in data:
            classify = _get_classify_func(gate_params_list[k][0].get(
                'classify', None))
            ret = _process_classify(data[k], [{
                'params': p
            }
                                              for p in gate_params_list[k]],
                                    Signal(dataMap['signal']), classify)
            for kk, v in ret.items():
                if k == 'result':
                    result[kk] = v
                else:
                    result[f'{k}_{kk}'] = v

    return result
