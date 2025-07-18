import copy
import random
from dataclasses import dataclass, field

import numpy as np
from qlispc import (COMMAND, READ, SYNC, TRIG, WRITE, Capture, CommandList,
                    DataMap, QLispCode, RawData, Result, Signal)

try:
    from qlispc.arch.baqis.assembly_code import _simplify_waveforms
except ImportError as e:
    from qlispc.arch.baqis.code import _simplify_waveforms

from waveforms.waveform import Waveform, WaveVStack, zero
from waveforms.waveform_parser import wave_eval


def group_captures(
    measures: dict[tuple[str, int], Capture]
) -> tuple[dict[str, list[Capture]], dict[str, list[Waveform | WaveVStack]],
           tuple[str, str]]:
    ret = {}
    da_ad = {}
    for k, capture in measures.items():
        if capture.hardware.IQ.name not in ret:
            ret[capture.hardware.IQ.name] = []
        ret[capture.hardware.IQ.name].append(capture)
        da_ad[capture.hardware.DA.name] = capture.hardware.IQ.name
    return ret, da_ad


def check_overlap(captures: list[Capture]) -> list[list[Capture]]:
    captures = sorted(captures, key=lambda x: x.time)
    ret = []
    for capture in captures:
        if not ret:
            ret.append([capture])
        else:
            if capture.time < max(
                [c.time + c.params['duration'] for c in ret[-1]]):
                ret[-1].append(capture)
            else:
                ret.append([capture])
    return ret


def collect_ad_info(code, capture_groups):
    data_map = {'signal': code.signal.value, 'arch': 'baqis2', 'cbits': {}}

    ad_cmds = {}

    for channel, captures in capture_groups.items():
        ad_cmds[channel] = {
            'start': np.inf,
            'stop': 0,
            'triggers': [],
            'triggerDelay': 0,
            'wList': [],
            'waveform': zero()
        }
        ad_cmds[channel]['triggers'] = [0]

        freqs = {}
        params = {}

        for capture in captures[0]:
            ad_cmds[channel]['triggerDelay'] = capture.hardware.IQ.triggerDelay
            duration = capture.params['duration']
            ad_cmds[channel]['start'] = min(ad_cmds[channel]['start'],
                                            capture.time)
            ad_cmds[channel]['stop'] = max(ad_cmds[channel]['stop'],
                                           capture.time + duration)
            Delta = capture.params['frequency'] - capture.hardware.lo_freq
            ad_cmds[channel]['wList'].append({
                'Delta':
                Delta,
                'phase':
                -2 * np.pi * Delta * capture.shift,
                'weight':
                capture.params.get('weight', 'one()'),
                't0':
                capture.time,
                'w':
                None,
                'phi':
                capture.params.get('phi', 0),
                'threshold':
                capture.params.get('threshold', 0),
            })
            freqs[Delta] = len(ad_cmds[channel]['wList']) - 1
            params[Delta] = {
                k: v
                for k, v in capture.params.items() if k not in ['pulse']
            }
            data_map['cbits'][capture.cbit] = ('READ.' + channel, 0,
                                               freqs[Delta], Delta,
                                               params[Delta], capture.time)

        # 将不同比特的读出波形合并
        for capture in captures[0]:
            ad_cmds[channel]['waveform'] += capture.params.get('pulse') >> (
                capture.time - ad_cmds[channel]['start'])

        ad_cmds[channel]['waveform'] = ad_cmds[channel]['waveform'].simplify()

        if len(captures) > 1:
            for k, capture_list in enumerate(captures[1:], start=1):
                start, stop = np.inf, 0
                for capture in capture_list:
                    duration = capture.params['duration']
                    start = min(start, capture.time)
                    stop = max(stop, capture.time + duration)
                    Delta = capture.params[
                        'frequency'] - capture.hardware.lo_freq
                    data_map['cbits'][capture.cbit] = ('READ.' + channel, k,
                                                       freqs[Delta], Delta,
                                                       params[Delta],
                                                       capture.time)

                ad_cmds[channel]['triggers'].append(start -
                                                    ad_cmds[channel]['start'])

    return ad_cmds, data_map


def align_delay(ad_cmd):
    # AD 的 trigger delay 对齐到 16 ns 的整数倍
    start_ns = round(ad_cmd['start'] * 1e9)
    triggerDelay_ns = round(ad_cmd['triggerDelay'] * 1e9)
    pre_ns = (start_ns + triggerDelay_ns) % 16
    latestTriggerList_ns = [
        round((t + ad_cmd['start']) * 1e9) for t in ad_cmd['triggers']
    ]

    # 触发信号发射时机对齐到 800 ns 整数倍
    triggerList_ns = [(t // 800) * 800 for t in latestTriggerList_ns]

    wlist = []
    for d in ad_cmd['wList']:
        d['t0'] = d['t0'] - triggerList_ns[0] * 1e-9
        wlist.append(d)

    return {
        'start': (start_ns - pre_ns - triggerList_ns[0]) * 1e-9,
        'stop': ad_cmd['stop'] - triggerList_ns[0] * 1e-9,
        'triggers': [t * 1e-9 for t in triggerList_ns],
        'triggerDelay':
        (start_ns + triggerDelay_ns - triggerList_ns[0]) * 1e-9,
        'wList': wlist,
        'waveform': ad_cmd['waveform']
    }


def assembly_code(code: QLispCode,
                  context=None) -> tuple[CommandList, DataMap]:
    cmds = []

    _simplify_waveforms(code.waveforms)

    # 将读出任务按 AD 通道分组
    captures, da_ad = group_captures(code.measures)

    # 将每个 AD 通道中的读出任务按时间分组，有重叠的任务放在一组
    capture_groups = {k: check_overlap(v) for k, v in captures.items()}

    # 写入除读出之外的波形
    for key, wav in code.waveforms.items():
        if key not in da_ad:
            cmds.append(WRITE(key, wav))

    ad_cmds, data_map = collect_ad_info(code, capture_groups)
    ad_cmds = {channel: align_delay(ad) for channel, ad in ad_cmds.items()}

    # 设置解模系数
    for channel, ad in ad_cmds.items():
        cmds.append(WRITE(channel + '.Shot', code.shots * len(ad['triggers'])))
        cmds.append(
            WRITE(channel + '.Coefficient', {
                'start': 0,
                'stop': ad['stop'] - ad['start'],
                'wList': ad['wList']
            }))
    for i in range(1, 9):
        cmds.append(WRITE(f'NS_QSYNC.CH{i}.Shot', code.shots))

    # 写入读出波形
    for key, ad_channel in da_ad.items():
        if ad_channel.startswith('NS_DDS2.'):
            wav = ad_cmds[ad_channel]['waveform'] >> ad_cmds[ad_channel][
                'start']
        else:
            wav = ad_cmds[ad_channel]['waveform'] >> (
                ad_cmds[ad_channel]['triggers'][0] +
                ad_cmds[ad_channel]['start'])
        cmds.append(WRITE(key, wav))

    # 设置 AD 的 trigger delay
    triggerList = [0]
    for channel, ad in ad_cmds.items():
        if channel.startswith('NS_DDS2.'):
            cmds.append(WRITE(channel + '.TriggerDelay', ad['triggerDelay']))
            triggerList = ad['triggers']
        else:
            cmds.append(
                WRITE(channel + '.TriggerDelay',
                      ad['triggers'][0] + ad['triggerDelay']))

    # 设置 QSYNC 的 trigger delay
    for i in range(1, 8):
        cmds.append(WRITE(f'NS_QSYNC.CH{i}.TrigDelay', 0))

    cmds.append(WRITE('NS_QSYNC.CH8.SubTriggerCount', len(triggerList)))
    cmds.append(WRITE('NS_QSYNC.CH8.TrigDelayList', triggerList))

    mode_pointer = capture_pointer = len(cmds)

    for channel in ad_cmds:
        if code.signal & Signal.trace:
            cmds.append(READ(channel + '.TraceIQ'))
            cmds.insert(mode_pointer, WRITE(channel + '.CaptureMode', 'raw'))
        else:
            cmds.append(READ(channel + '.IQ'))
            cmds.insert(mode_pointer, WRITE(channel + '.CaptureMode', 'alg'))
        mode_pointer += 1
        capture_pointer += 1
        cmds.insert(
            capture_pointer,
            WRITE(channel + '.StartCapture', random.randint(0, 2**16 - 1)))
        capture_pointer += 1

    return cmds, data_map
