import numpy as np
from waveforms import drag, drag_sin, drag_sinx

from .u3 import *


def DRAG_new(t,
             shape,
             width,
             plateau,
             eps,
             amp,
             delta,
             freq,
             block_freq,
             phase,
             tab: float = 0.5):

    if shape in ['hanning', 'cosPulse', 'CosPulse']:
        return amp * drag(freq, width, plateau, delta, block_freq, phase,
                          t - width / 2 - plateau / 2)
    elif shape in ['drag_sin', 'dragSin', 'dragsin', 'DRAGSin']:
        return amp * drag_sin(freq, width, plateau, delta, block_freq, phase,
                              t - width / 2 - plateau / 2)
    elif shape in ['drag_sinx', 'dragSinX', 'dragsinx', 'DRAGSinX']:
        return amp * drag_sinx(freq,
                               width,
                               plateau,
                               delta,
                               block_freq,
                               phase,
                               t - width / 2 - plateau / 2,
                               tab=tab)
    elif shape in ['coshPulse', 'CoshPulse']:
        pulse = coshPulse(width, plateau=plateau, eps=eps)
    elif shape in ['square_cos', 'square_erf']:
        pulse = square(width=plateau+width/2, edge=width/2, type=shape.split('_')[-1])
    else:
        pulse = gaussian(width, plateau=plateau)
    if freq == 0 or freq is None:
        return amp * (pulse>>t)
    I, Q = mixing(amp * pulse, phase=phase, freq=delta, block_freq=block_freq)
    wav, _ = mixing(I >> t, Q >> t, freq=freq)
    return wav


def R(ctx, qubits, phi=0, level1=0, level2=1):
    qubit, = qubits

    freq, phase = get_frequency_phase(ctx, qubit, phi, level1, level2)

    amp = ctx.params.get('amp', 0.5)
    shape = ctx.params.get('shape', 'cosPulse')
    width = ctx.params.get('width', 5e-9)
    plateau = ctx.params.get('plateau', 0.0)
    buffer = ctx.params.get('buffer', 0)
    tab = ctx.params.get('tab', 0.5)

    duration = width + plateau + buffer
    if amp != 0:
        block_freq = ctx.params.get('block_freq', None)
        delta = ctx.params.get('delta', 0)
        eps = ctx.params.get('eps', 1)
        channel = ctx.params.get('channel', 'RF')
        t = duration / 2 + ctx.time[qubit]
        wav = DRAG_new(t, shape, width, plateau, eps, amp, delta, freq,
                       block_freq, phase, tab)
        yield ('!play', wav), (channel, qubit)
    yield ('!add_time', duration), qubit


@lib.opaque('R')
def _R(ctx, qubits, phi=0):
    yield from R(ctx, qubits, phi, 0, 1)


@lib.opaque('R12')
def _R12(ctx, qubits, phi=0):
    yield from R(ctx, qubits, phi, 1, 2)


@lib.opaque('R23')
def _R23(ctx, qubits, phi=0):
    yield from R(ctx, qubits, phi, 2, 3)


def _CZ_pulse(ctx, qubits, positive=1, cum_t=1):
    t = max(ctx.time[q] for q in qubits)

    width = ctx.params.get('width', 10e-9)
    ampc = ctx.params.get('ampc', 0)
    eps = ctx.params.get('eps', 1.0)
    plateau = ctx.params.get('plateau', 0.0)
    buffer = ctx.params.get('buffer', 0)
    before = ctx.params.get('before', buffer)
    after = ctx.params.get('after', buffer)
    shape = ctx.params.get('shape', 'coshPulse')
    freq = ctx.params.get('frequency', None)
    block_freq = ctx.params.get('block_freq', None)
    tab = ctx.params.get('tab', 0)

    for amp, target in zip([
            ampc,
    ], [
        ('coupler.Z', *qubits),
    ]):
        if amp != 0 and width + plateau > 0:
            pulse = DRAG_new(t + before + width / 2 + plateau / 2, shape,
                             width, plateau, eps, amp * positive, 0, freq,
                             block_freq, 0, tab)
            yield ('!play', pulse), target
    for qubit in qubits:
        yield ('!set_time', t + (before + width + plateau + after)*cum_t), qubit


@lib.opaque('CZ', type='v4')
def _CZ(ctx, qubits):
    yield from _CZ_pulse(ctx, qubits)
    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


@lib.opaque('CZ', type='v4_nz')
def _CZ_nz(ctx, qubits):
    t = max(ctx.time[q] for q in qubits)
    before = ctx.params.get('before_all', 0)
    if before>0:
        for qubit in qubits:
            yield ('!set_time', t + before), qubit
    coeff = ctx.params.get('coeff', (1, -1))
    for positive in coeff:
        yield from _CZ_pulse(ctx, qubits, positive=positive)
    t = max(ctx.time[q] for q in qubits)
    after = ctx.params.get('after_all', 0)
    if after>0:
        for qubit in qubits:
            yield ('!set_time', t + after), qubit
    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


@lib.opaque('CZ', type='v4_echo')
def _CZ_echo(ctx, qubits):
    t = max(ctx.time[q] for q in qubits)
    before = ctx.params.get('before_all', 0)
    if before>0:
        for qubit in qubits:
            yield ('!set_time', t + before), qubit
    
    coeff = ctx.params.get('coeff', (1, -1))
    q_params = [ctx.cfg.getGate('R', q)['params'] for q in qubits]
    for positive in coeff:
        yield from _CZ_pulse(ctx, qubits, positive=positive)
        for i, qubit in enumerate(qubits):
            ctx.scopes.append(q_params[i])
            yield from R(ctx, (qubit, ), 0)
            yield from R(ctx, (qubit, ), 0)
            ctx.scopes.pop()
    
    t = max(ctx.time[q] for q in qubits)
    after = ctx.params.get('after_all', 0)
    if after>0:
        for qubit in qubits:
            yield ('!set_time', t + after), qubit
            
    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


@lib.opaque('Reset')
def _CZ(ctx, qubits):
    with_R12 = ctx.params.get('withR12', True)
    if with_R12:
        ctx.scopes.append(ctx.cfg.getGate('R12', qubits[0])['params'])
        yield from R(ctx, qubits, 0)
        yield from R(ctx, qubits, 0)
        ctx.scopes.pop()
    with_R23 = ctx.params.get('withR23', False)
    if with_R23:
        ctx.scopes.append(ctx.cfg.getGate('R23', qubits[0])['params'])
        yield from R(ctx, qubits, 0)
        yield from R(ctx, qubits, 0)
        ctx.scopes.pop()
    couplers = ctx.params['qubits']
    yield from _CZ_pulse(ctx, couplers, cum_t=0)
    

@lib.opaque('CZ', type='v4_ac')
def _CZ(ctx, qubits):
    yield from _CZ_pulse(ctx, qubits)
    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


@lib.opaque('CZ', type='v4_ac_echo')
def _CZ(ctx, qubits):
    t = max(ctx.time[q] for q in qubits)
    before = ctx.params.get('before_all', 0)
    if before>0:
        for qubit in qubits:
            yield ('!set_time', t + before), qubit

    coeff = ctx.params.get('coeff', (1, -1))
    q_params = [ctx.cfg.getGate('R', q)['params'] for q in qubits]
    for positive in coeff:
        yield from _CZ_pulse(ctx, qubits, positive=positive)
        for i, qubit in enumerate(qubits):
            ctx.scopes.append(q_params[i])
            yield from R(ctx, (qubit, ), 0)
            yield from R(ctx, (qubit, ), 0)
            ctx.scopes.pop()

    t = max(ctx.time[q] for q in qubits)
    after = ctx.params.get('after_all', 0)
    if after>0:
        for qubit in qubits:
            yield ('!set_time', t + after), qubit
        
    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


def _CR_pulse(ctx, qubits, positive=1):
    t = max(ctx.time[q] for q in qubits)

    width = ctx.params.get('width', 10e-9)
    amp1 = ctx.params.get('amp1', 1)
    amp2 = ctx.params.get('amp2', 1)
    eps = ctx.params.get('eps', 1.0)
    plateau = ctx.params.get('plateau', 0.0)
    buffer = ctx.params.get('buffer', 0)
    before = ctx.params.get('before', buffer)
    after = ctx.params.get('after', buffer)
    shape = ctx.params.get('shape', 'coshPulse')
    freq = ctx.params.get('frequency', None)
    block_freq = ctx.params.get('block_freq', None)
    tab = ctx.params.get('tab', 0)

    global_phase = ctx.params.get('global_phase', 0)
    relative_phase = ctx.params.get('relative_phase', 0)

    for amp, target, phase in zip(
        [amp1, amp2], [('RF', qubits[0]), ('RF', qubits[1])], [
            global_phase + ctx.phases[qubits[1]],
            global_phase + ctx.phases[qubits[1] + relative_phase]
        ]):
        if amp != 0 and width + plateau > 0:
            pulse = DRAG_new(t + before + width / 2 + plateau / 2, shape,
                             width, plateau, eps, amp * positive, 0, freq,
                             block_freq, 0, tab)
            yield ('!play', pulse), target
    for qubit in qubits:
        yield ('!set_time', t + before + width + plateau + after), qubit


@lib.opaque('CZ', type='amcz')
def _CZ_amcz(ctx, qubits):
    yield from _CR_pulse(ctx, qubits)
    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


@lib.opaque('CZ', type='amcz_echo')
def _CZ_amcz_echo(ctx, qubits):
    t = max(ctx.time[q] for q in qubits)
    before = ctx.params.get('before_all', 0)
    if before>0:
        for qubit in qubits:
            yield ('!set_time', t + before), qubit

    coeff = ctx.params.get('coeff', (1, 1))
    q_params = [ctx.cfg.getGate('R', q)['params'] for q in qubits]
    for positive in coeff:
        yield from _CR_pulse(ctx, qubits, positive=positive)
        for i, qubit in enumerate(qubits):
            ctx.scopes.append(q_params[i])
            yield from R(ctx, (qubit, ), 0)
            yield from R(ctx, (qubit, ), 0)
            ctx.scopes.pop()

    t = max(ctx.time[q] for q in qubits)
    after = ctx.params.get('after_all', 0)
    if after>0:
        for qubit in qubits:
            yield ('!set_time', t + after), qubit

    yield ('!add_phase', ctx.params.get('phi1', 0)), qubits[0]
    yield ('!add_phase', ctx.params.get('phi2', 0)), qubits[1]


@lib.opaque('CR')
def _CR(ctx, qubits):
    yield from _CR_pulse(ctx, qubits)


def _measure_pulse(ctx, qubits, cbit=None):
    from waveforms.waveform import cos, pi, step
    from qlispc.libs.stdlib import extract_variable_and_index_if_match
    qubit, = qubits

    if cbit is None:
        if len(ctx.measures['result']) == 0:
            cbit = 0
        else:
            cbit = max(ctx.measures['result'].keys()) + 1

    if isinstance(cbit, int):
        cbit = ('result', cbit)
    elif isinstance(cbit, str):
        cbit = extract_variable_and_index_if_match(cbit)

    amp = np.abs(ctx.params['amp'])
    duration = ctx.params['duration']
    frequency = ctx.params['frequency']
    bias = ctx.params.get('bias', None)
    signal = ctx.params.get('signal', 'state')
    ring_up_amp = ctx.params.get('ring_up_amp', amp)
    ring_up_time = ctx.params.get('ring_up_time', 50e-9)
    rsing_edge_time = ctx.params.get('rsing_edge_time', 5e-9)
    ring_up_waist = ctx.params.get('ring_up_waist', 0)

    try:
        w = ctx.params['w']
        weight = None
    except:
        weight = ctx.params.get('weight',
                                f'square({duration}) >> {duration/2}')
        w = None

    t = ctx.time[qubit]

    pulse = (ring_up_amp * (step(rsing_edge_time) >>
                            (t + rsing_edge_time / 2)) -
             (ring_up_amp - ring_up_waist) *
             (step(rsing_edge_time) >>
              (t + rsing_edge_time / 2 + ring_up_time / 2)) +
             (amp - ring_up_waist) *
             (step(rsing_edge_time) >>
              (t + rsing_edge_time / 2 + ring_up_time)) -
             (amp * 2 - ring_up_waist) *
             (step(rsing_edge_time) >> (t + rsing_edge_time / 2 + duration)) +
             (ring_up_amp - ring_up_waist) *
             (step(rsing_edge_time) >>
              (t + rsing_edge_time / 2 + duration + ring_up_time / 2)) -
             (ring_up_amp - amp) *
             (step(rsing_edge_time) >>
              (t + rsing_edge_time / 2 + duration + ring_up_time)))

    yield ('!play', pulse * cos(2 * pi * frequency)), ('readoutLine.RF', qubit)

    params = {k: v for k, v in ctx.params.items()}
    params['w'] = w
    params['weight'] = weight
    if not (cbit[0] == 'result' and cbit[1] < 0):
        yield ('!capture', Capture(qubit, cbit, ctx.time[qubit], signal,
                                   params)), cbit
    yield ('!set_time', t + duration + ring_up_time*2+ring_up_time*2), qubit
    yield ('!set_phase', 0), qubit


@lib.opaque('Measure')
def _measure(ctx, qubits, cbit=None):
    yield from _measure_pulse(ctx, qubits, cbit)


@lib.opaque('Measure', type='e2f')
def _measure_e2f(ctx, qubits, cbit=None):
    ctx.scopes.append(ctx.cfg.getGate('R12', qubits[0])['params'])
    yield from R(ctx, qubits, 0)
    yield from R(ctx, qubits, 0)
    ctx.scopes.pop()
    yield from _measure_pulse(ctx, qubits, cbit)
