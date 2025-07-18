import copy
import random
from dataclasses import dataclass, field

import numpy as np
from qlispc import (COMMAND, READ, SYNC, TRIG, WRITE, Capture, CommandList,
                    DataMap, QLispCode, RawData, Result, Signal)
from waveforms.waveform import Waveform, WaveVStack, square
from waveforms.waveform_parser import wave_eval


@dataclass
class ADTask():
    start: float = np.inf
    stop: float = 0
    trigger: str = ''
    triggerDelay: float = 0
    sampleRate: float = 1e9
    triggerClockCycle: float = 8e-9
    triggerLevel: float = 0
    triggerSlope: str = 'rising'
    triggerSource: str = 'external'
    triggerDelayAddress: str = ''
    triggerDration: float = 1e-6
    fList: list[float] = field(default_factory=list)
    tasks: list[Capture] = field(default_factory=list)
    wList: list = field(default_factory=list)
    wList_info: list = field(default_factory=list)
    coef_info: dict = field(default_factory=lambda: {
        'start': 0,
        'stop': 1024,
        'wList': []
    })
    probe_cfg: dict = field(default_factory=dict)


def _getADInfo(measures: dict[int | str, Capture]) -> dict[str, ADTask]:
    AD_tasks: dict[str, ADTask] = {}
    for cbit in sorted(measures.keys(),
                       key=lambda x: (0 if isinstance(x, int) else 1, x)):
        task = measures[cbit]
        ad = task.hardware.IQ.name
        if ad not in AD_tasks:
            mapping = dict(task.hardware.IQ.commandAddresses)
            triggerDelayAddress = mapping.get('triggerDelayAddress', '')
            AD_tasks[ad] = ADTask(
                trigger=task.hardware.IQ.trigger,
                triggerDelay=task.hardware.IQ.triggerDelay,
                sampleRate=task.hardware.IQ.sampleRate,
                triggerClockCycle=task.hardware.IQ.triggerClockCycle,
                triggerDelayAddress=triggerDelayAddress,
                probe_cfg=task.params.get('probe_cfg', {}))
        ad_task = AD_tasks[ad]
        ad_task.start = min(ad_task.start, task.time)
        # ad_task.start = np.floor_divide(ad_task.start,
        #                                task.hardware.IQ.triggerClockCycle
        #                                ) * task.hardware.IQ.triggerClockCycle
        ad_task.start = (round(ad_task.start * 1e15) //
                         round(task.hardware.IQ.triggerClockCycle *
                               1e15)) * task.hardware.IQ.triggerClockCycle
        ad_task.stop = max(ad_task.stop, task.time + task.params['duration'])
        ad_task.tasks.append(task)
    return AD_tasks


def _get_w_and_data_maps(AD_tasks: dict[str, ADTask]):
    dataMap = {'cbits': {}}

    for channel, ad_task in AD_tasks.items():
        ad_task.coef_info['start'] = ad_task.start
        ad_task.coef_info['stop'] = ad_task.stop

        for task in ad_task.tasks:
            Delta = task.params['frequency'] - task.hardware.lo_freq
            ad_task.fList.append(Delta)
            params = copy.copy(task.params)
            params['w'] = None
            dataMap['cbits'][task.cbit] = ('READ.' + channel,
                                           len(ad_task.fList) - 1, Delta,
                                           params, task.time, ad_task.start,
                                           ad_task.stop)

            ad_task.coef_info['wList'].append({
                'Delta':
                Delta,
                'phase':
                -2 * np.pi * Delta * task.shift,
                'weight':
                task.params.get('weight', 'one()'),
                'window':
                task.params.get('window', (0, 1024)),
                'w':
                task.params.get('w', None),
                't0':
                task.time,
                'phi':
                task.params.get('phi'),
                'threshold':
                task.params.get('threshold'),
            })
    return AD_tasks, dataMap


def _should_be_simplified(key: str, wav: Waveform | str) -> bool:
    if isinstance(wav, WaveVStack) and len(wav.wlist) < 50:
        return True
    return False


def _simplify(key: str, wav: Waveform | str) -> Waveform:
    if _should_be_simplified(key, wav):
        wav = wav.simplify()
    if isinstance(wav, WaveVStack):
        wav.wlist = [(tuple(np.round(bounds, 18)), seq)
                     for bounds, seq in wav.wlist]
    elif isinstance(wav, Waveform):
        wav.bounds = tuple(np.round(wav.bounds, 18))
    elif isinstance(wav, str):
        wav = wave_eval(wav)
    return wav


def _simplify_waveforms(
        wavforms: dict[str, Waveform | str]) -> dict[str, Waveform | str]:

    wavs = [(key, _simplify(key, wav))
            for key, wav in wavforms.items()]  # should be parallel

    for key, wav in wavs:
        wavforms[key] = wav
    return wavforms


def assembly_code(code: QLispCode,
                  context=None) -> tuple[CommandList, DataMap]:
    cmds = []

    _simplify_waveforms(code.waveforms)

    for key, wav in code.waveforms.items():
        cmds.append(WRITE(key, wav))

    ADInfo = _getADInfo(code.measures)
    ADInfo, dataMap = _get_w_and_data_maps(ADInfo)
    dataMap['signal'] = code.signal.value
    dataMap['arch'] = 'rcp'

    for channel, ad_task in ADInfo.items():
        delay = ad_task.start + ad_task.triggerDelay

        amp = ad_task.probe_cfg.get('setting', {}).get('JPA_pump_amp', 0)
        freq = ad_task.probe_cfg.get('setting', {}).get('JPA_pump_freq', 0)
        before = ad_task.probe_cfg.get('setting', {}).get('JPA_pump_before', 0)
        after = ad_task.probe_cfg.get('setting', {}).get('JPA_pump_after', 0)
        bias = ad_task.probe_cfg.get('setting', {}).get('JPA_bias', 0)

        from waveforms import cos, pi, square, step

        window = ((step(0) >>
                   (ad_task.start - before)) - (step(0) >>
                                                (ad_task.stop + after)))
        pump_pulse = amp * window * cos(2 * pi * freq)
        z_pulse = bias * window

        probe = ad_task.probe_cfg.get('probe', None)
        if probe:
            cmds.append(WRITE(f'{probe}.waveform.JPABIAS', z_pulse))

            pump_pulse <<= ad_task.start - before
            pump_pulse.start = 0
            pump_pulse.stop = (ad_task.stop + after) - (ad_task.start - before)
            cmds.append(WRITE(f'{probe}.waveform.JPAPUMP', pump_pulse))

            if 'JPAPUMP' in ad_task.probe_cfg.get('channel', {}):
                ch = ad_task.probe_cfg['channel']['JPAPUMP']
                if ch is not None:
                    cmds.append(WRITE(ch + '.Delay', ad_task.start - before))

        if ad_task.trigger:
            cmds.append(
                WRITE(
                    ad_task.trigger,
                    square(ad_task.triggerDration) >>
                    ad_task.triggerDration / 2))
        cmds.append(WRITE(channel + '.Shot', code.shots))
        cmds.append(WRITE(channel + '.Coefficient', ad_task.coef_info))
        # cmds.append(WRITE(channel + '.Classify', code.signal.value))
        if ad_task.triggerDelayAddress == "":
            cmds.append(WRITE(channel + '.TriggerDelay', delay))
        else:
            cmds.append(
                WRITE(ad_task.triggerDelayAddress + '.TriggerDelay', delay))

    mode_pointer = capture_pointer = len(cmds)

    for channel in ADInfo:
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

    if (code.signal & Signal.remote_count) == Signal.remote_count:
        cmds.append(READ(channel + '.Counts'))

    return cmds, dataMap
