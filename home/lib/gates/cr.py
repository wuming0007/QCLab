import re

import numpy as np
from waveforms.waveform import (D, cos, cosPulse, gaussian, mixing, square,
                                step, zero)

from qlispc import Capture, libraries, stdlib

lib = libraries(stdlib)

EPS = 1e-9


def extract_variable_and_index_if_match(s):
    pattern = r'^(\w+)\[(\d+)\]$'
    match = re.search(pattern, s)

    if match:
        name, index = match.groups()
        return (name, int(index))
    else:
        return (s, 0)


def _rfUnitary(ctx, qubits, theta, phi, level1=0, level2=1):

    from numpy import interp, mod, pi

    qubit, = qubits

    if theta < 0:
        theta = -theta
        phi += pi
    theta = mod(theta, 2 * pi)
    if theta > pi:
        theta = 2 * pi - theta
        phi += pi

    phi = mod(
        phi + ctx.phases_ext[qubit][level1] - ctx.phases_ext[qubit][level2],
        2 * pi)
    phi = phi if abs(level2 - level1) % 2 else phi - pi
    if phi > pi:
        phi -= 2 * pi
    phi = phi / (level2 - level1)

    shape = ctx.params.get('shape', 'CosPulse')
    buffer = ctx.params.get('buffer', 0)
    delta = ctx.params.get('delta', 0)

    phase = pi * interp(phi / pi, *ctx.params['phase'])

    pulseLib = {
        'CosPulse': cosPulse,
        'Gaussian': gaussian,
        'Square': square,
        'cosPulse': cosPulse,
        'gaussian': gaussian,
        'square': square,
        'DC': square,
    }

    block_freq = ctx.params.get('block_freq', None)
    freq = ctx.params['frequency']

    while theta > 0:
        if theta > pi / 2:
            theta1 = pi / 2
            theta -= pi / 2
        else:
            theta1 = theta
            theta = 0

        duration = interp(theta1 / pi, *ctx.params['duration'])
        amp = interp(theta1 / pi, *ctx.params['amp'])
        pulse = pulseLib[shape](duration)

        if duration > 0 and amp > 0:

            I, Q, c = pulse, None, 1
            if block_freq is not None:
                if isinstance(block_freq, tuple):
                    for bq in block_freq:
                        I, Q = mixing(I,
                                      Q,
                                      freq=0,
                                      block_freq=bq - freq - delta)
                else:
                    I, Q = mixing(I,
                                  Q,
                                  freq=0,
                                  block_freq=block_freq - freq - delta)
                    if shape in ['CosPulse', 'cosPulse']:
                        b = 1 / pi / 2 / (block_freq - freq - delta)
                        o = pi / duration
                        d21 = 4 * o**2 * b**2
                        d = np.sqrt(np.abs(d21 - 1))
                        if d21 < 1:
                            c = 0.5 * pi / (np.sqrt(1 - d) * np.sqrt(1 + d) +
                                            np.arcsin(d) / d)
                        else:
                            c = 0.5 * pi / (np.sqrt(d**2 + 1) + 0.5 * np.log(
                                (np.sqrt(d**2 + 1) + d) /
                                (np.sqrt(d**2 + 1) - d)) / d)

            t = (duration + buffer) / 2 + ctx.time[qubit]
            wav, _ = mixing(
                (amp * c * I) >> t,
                (amp * c * Q) >> t if Q is not None else None,
                freq=freq + delta,
                phase=phase + 2 * pi * delta * (ctx.time[qubit] + buffer / 2))
            yield ('!play', wav), ('RF', qubit)
            yield ('!add_time', duration + buffer), qubit
            # yield ('!add_phase', -duration*delta*pi*2), qubit


@lib.opaque('rfUnitary')
def rfUnitary(ctx, qubits, theta, phi):
    yield from _rfUnitary(ctx, qubits, theta, phi)


@lib.opaque('rfUnitary12')
def rfUnitary12(ctx, qubits, theta, phi):
    yield from _rfUnitary(ctx, qubits, theta, phi)


@lib.opaque('rfUnitary02')
def rfUnitary02(ctx, qubits, theta, phi):
    yield from _rfUnitary(ctx, qubits, theta, phi)


@lib.opaque('Measure')
def measure(ctx, qubits, cbit=None):

    from numpy import pi

    # if ctx.params.get('dressed', False):
    #     ori_params = ctx.params
    #     ctx.scopes[-1] = ctx.cfg.getGate('Dressed', qubits[0])['params']
    #     yield from dressed(ctx, qubits)
    #     ctx.scopes[-1] = ori_params

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
    rsing_edge_time = ctx.params.get('rsing_edge_time', 20e-9)
    ring_up_waist = ctx.params.get('ring_up_waist', 0)

    try:
        w = ctx.params['w']
        weight = None
    except:
        weight = ctx.params.get('weight',
                                f'square({duration}) >> {duration/2}')
        w = None

    t = ctx.time[qubit]

    # phi = 2 * np.pi * (lo - frequency) * t

    # pulse = (ring_up_amp * (step(rsing_edge_time) >> t) - (ring_up_amp - amp) *
    #          (step(rsing_edge_time) >>
    #           (t + ring_up_time)) - amp * (step(rsing_edge_time) >>
    #                                        (t + duration)))

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
    if bias is not None:
        yield ('!set_bias', bias), ('Z', qubit)

    # pulse = square(2 * duration) >> duration
    # ctx.channel['readoutLine.AD.trigger', qubit] |= pulse.marker

    params = {k: v for k, v in ctx.params.items()}
    params['w'] = w
    params['weight'] = weight
    if not (cbit[0] == 'result' and cbit[1] < 0):
        yield ('!capture', Capture(qubit, cbit, ctx.time[qubit], signal,
                                   params)), cbit
    yield ('!set_time', t + duration), qubit
    yield ('!set_phase', 0), qubit


@lib.gate(name='-X')
def X(q):
    yield (('u3', np.pi, 0, -np.pi), q)


@lib.gate(name='-Y')
def Y(q):
    yield (('u3', np.pi, -np.pi / 2, -np.pi / 2), q)


def _CR_pulse(ctx, qubits, positive=1):

    t = max(ctx.time[q] for q in qubits)

    duration = ctx.params['duration']
    amp1 = ctx.params['amp1']
    amp2 = ctx.params['amp2']
    global_phase = ctx.params['global_phase']
    relative_phase = ctx.params['relative_phase']

    edge_type = ctx.params.get('edge_type', 'cos')
    edge = ctx.params.get('edge', duration / 10)
    drag = ctx.params.get('drag', 0) * 1e-9
    skew = ctx.params.get('skew', 0) * 1e-9
    buffer = ctx.params.get('buffer', 10e-9)
    delta = ctx.params.get('delta', 0)

    pulse = square(width=duration, edge=edge,
                   type=edge_type) >> t + duration / 2 + edge / 2 + buffer / 2
    d_step_pulse = D(step(edge=edge, type=edge_type))
    drag_pulse = (d_step_pulse >> t +
                  (edge + buffer) / 2) - (d_step_pulse >> t +
                                          (edge + buffer) / 2 + duration)
    skew_pulse = (d_step_pulse >> t +
                  (edge + buffer) / 2) + (d_step_pulse >> t +
                                          (edge + buffer) / 2 + duration)

    if amp1 != 0 and duration > 0:
        wav, _ = mixing(amp1 * pulse,
                        phase=global_phase - ctx.phases[qubits[1]] +
                        2 * np.pi * delta * t,
                        freq=ctx.params['frequency'])
        yield ('!play', wav * positive), ('RF', qubits[0])
        yield ('!set_time', t + duration + edge + buffer), qubits[0]
        yield ('!set_time', t + duration + edge + buffer), qubits[1]

    if amp2 != 0 and duration > 0:
        I2, Q2 = amp2 * pulse, zero()
        if drag != 0:
            Q2 += drag * drag_pulse
        if skew != 0:
            Q2 += skew * skew_pulse
        wav, _ = mixing(I2,
                        Q2,
                        phase=global_phase + relative_phase -
                        ctx.phases[qubits[1]] + 2 * np.pi * delta * t,
                        freq=ctx.params['frequency'])

    yield ('!add_phase', ctx.params['phi1']), qubits[0]
    yield ('!add_phase', ctx.params['phi2']), qubits[1]


@lib.opaque(name='CR')
def _CR(ctx, qubits):
    yield from _CR_pulse(ctx, qubits, positive=1)


@lib.opaque(name='CR', type='echo')
def _CR_echo(ctx, qubits):

    ori_params = ctx.params

    q0_params = ctx.cfg.getGate('rfUnitary', qubits[0])['params']
    q1_params = ctx.cfg.getGate('rfUnitary', qubits[1])['params']

    yield from _CR_pulse(ctx, qubits, 1)

    if ori_params.get('echo', True):

        ctx.scopes.append(q0_params)
        yield from _rfUnitary(ctx, (qubits[0], ), np.pi, ctx.phases[qubits[1]])
        ctx.scopes.pop()

        yield from _CR_pulse(ctx, qubits, -1)

        ctx.scopes.append(q0_params)
        yield from _rfUnitary(ctx, (qubits[0], ), np.pi, ctx.phases[qubits[1]])
        yield from P(ctx, (qubits[0], ), np.pi / 2)
        ctx.scopes.pop()

    ctx.scopes.append(q1_params)
    yield from _rfUnitary(ctx, (qubits[1], ),
                          ori_params.get('theta2', np.pi / 2), 0)
    ctx.scopes.pop()


@lib.opaque(name='CR', type='direct')
def _CR_direct(ctx, qubits):

    ori_params = ctx.params

    yield from _CR_pulse(ctx, qubits, 1)

    ctx.scopes.append(ctx.cfg.getGate('rfUnitary', qubits[1])['params'])
    yield from _rfUnitary(ctx, (qubits[1], ), ori_params.get('theta2', 0), 0)
    ctx.scopes.pop()


@lib.opaque(name='Cnot')
def cnot(ctx, qubits):

    direction = ctx.params.get('direction', 'forward')
    base_gate = ctx.params.get('base', 'CR')

    act_qubits = qubits
    if direction == 'inverse':
        act_qubits = (
            qubits[1],
            qubits[0],
        )

    q0_params = ctx.cfg.getGate('rfUnitary', act_qubits[0])['params']
    q1_params = ctx.cfg.getGate('rfUnitary', act_qubits[1])['params']
    if direction != 'forward' or base_gate != 'CR':
        yield from P(ctx, (act_qubits[1], ), np.pi)
        ctx.scopes.append(q1_params)
        yield from _rfUnitary(ctx, (act_qubits[1], ), np.pi / 2, np.pi / 2)
        ctx.scopes.pop()

        if base_gate == 'CR':
            yield from P(ctx, (act_qubits[0], ), np.pi)
            ctx.scopes.append(q0_params)
            yield from _rfUnitary(ctx, (act_qubits[0], ), np.pi / 2, np.pi / 2)
            ctx.scopes.pop()

    if base_gate == 'CR':
        cr_type = ctx.cfg.getGate('CR', *act_qubits)['default_type']
        if cr_type == 'default':
            ctx.scopes.append(ctx.cfg.getGate('CR', *act_qubits)['params'])
            yield from _CR_pulse(ctx, act_qubits)
            ctx.scopes.pop()
        elif cr_type == 'echo':
            ctx.scopes.append(ctx.cfg.getGate('CR', *act_qubits)['echo'])
            yield from _CR_echo(ctx, act_qubits)
            ctx.scopes.pop()
        elif cr_type == 'direct':
            ctx.scopes.append(ctx.cfg.getGate('CR', *act_qubits)['direct'])
            yield from _CR_direct(ctx, act_qubits)
            ctx.scopes.pop()
        else:
            pass

    elif base_gate == 'AMCZ':
        ctx.scopes.append(ctx.cfg.getGate('AMCZ', *act_qubits)['params'])
        yield from _AMCZ_pulse(ctx, act_qubits)
        ctx.scopes.pop()
    else:
        pass

    if direction != 'forward' or base_gate != 'CR':
        yield from P(ctx, (act_qubits[1], ), np.pi)
        ctx.scopes.append(q1_params)
        yield from _rfUnitary(ctx, (act_qubits[1], ), np.pi / 2, np.pi / 2)
        ctx.scopes.pop()

        if base_gate == 'CR':
            yield from P(ctx, (act_qubits[0], ), np.pi)
            ctx.scopes.append(q0_params)
            yield from _rfUnitary(ctx, (act_qubits[0], ), np.pi / 2, np.pi / 2)
            ctx.scopes.pop()


@lib.opaque(name='CZ')
def cz(ctx, qubits):
    direction = ctx.params.get('direction', 'forward')
    base_gate = ctx.params.get('base', 'CR')

    act_qubits = qubits
    if direction == 'inverse':
        act_qubits = (
            qubits[1],
            qubits[0],
        )

    ori_params = ctx.params
    if base_gate == 'CR':
        yield from P(ctx, (act_qubits[1], ), np.pi)
        ctx.scopes[-1] = ctx.cfg.getGate('rfUnitary', act_qubits[1])['params']
        yield from _rfUnitary(ctx, (act_qubits[1], ), np.pi / 2, np.pi / 2)

        cr_type = ctx.cfg.getGate('CR', *act_qubits)['default_type']
        if cr_type == 'default':
            ctx.scopes[-1] = ctx.cfg.getGate('CR', *act_qubits)['params']
            yield from _CR_pulse(ctx, act_qubits)
        elif cr_type == 'echo':
            ctx.scopes[-1] = ctx.cfg.getGate('CR', *act_qubits)['echo']
            yield from _CR_echo(ctx, act_qubits)
        elif cr_type == 'direct':
            ctx.scopes[-1] = ctx.cfg.getGate('CR', *act_qubits)['direct']
            yield from _CR_direct(ctx, act_qubits)
        else:
            pass

        yield from P(ctx, (act_qubits[1], ), np.pi)
        ctx.scopes[-1] = ctx.cfg.getGate('rfUnitary', act_qubits[1])['params']
        yield from _rfUnitary(ctx, (act_qubits[1], ), np.pi / 2, np.pi / 2)

    elif base_gate == 'AMCZ':
        ctx.scopes[-1] = ctx.cfg.getGate('AMCZ', *act_qubits)['params']
        yield from _AMCZ_pulse(ctx, act_qubits)
    ctx.scopes[-1] = ori_params


@lib.opaque('P')
def P(ctx, qubits, phi):
    phi += ctx.phases[qubits[0]]
    yield ('!set_phase', phi), qubits[0]


@lib.opaque('Measure', type='e2f')
def measure_e2f(ctx, qubits, cbit=None):

    from waveforms import cos, pi, step

    if cbit is None:
        if len(ctx.measures['result']) == 0:
            cbit = 0
        else:
            cbit = max(ctx.measures['result'].keys()) + 1

    if isinstance(cbit, int):
        cbit = ('result', cbit)
    elif isinstance(cbit, str):
        cbit = extract_variable_and_index_if_match(cbit)

    ori_params = ctx.params
    ctx.scopes[-1] = ctx.cfg.getGate('rfUnitary12', qubits[0])['params']
    yield from _rfUnitary(ctx, qubits, pi / 2, 0)
    ctx.scopes[-1] = ori_params

    if ctx.params.get('dressed', False):
        ori_params = ctx.params
        ctx.scopes[-1] = ctx.cfg.getGate('Dressed', qubits[0])['params']
        yield from dressed(ctx, qubits)
        ctx.scopes[-1] = ori_params

    qubit, = qubits

    if cbit is None:
        if len(ctx.measures) == 0:
            cbit = 0
        else:
            cbit = max(ctx.measures.keys()) + 1

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

    # phi = 2 * np.pi * (lo - frequency) * t

    # pulse = (ring_up_amp * (step(rsing_edge_time) >> t) - (ring_up_amp - amp) *
    #          (step(rsing_edge_time) >>
    #           (t + ring_up_time)) - amp * (step(rsing_edge_time) >>
    #                                        (t + duration)))

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
    if bias is not None:
        yield ('!set_bias', bias), ('Z', qubit)

    params = {k: v for k, v in ctx.params.items()}
    params['w'] = w
    params['weight'] = weight
    if not (cbit[0] == 'result' and cbit[1] < 0):
        yield ('!capture', Capture(qubit, cbit, ctx.time[qubit], signal,
                                   params)), cbit
    yield ('!set_time', t + duration), qubit
    yield ('!set_phase', 0), qubit


@lib.opaque('Dressed')
def dressed(ctx, qubits):

    from waveforms import cos, pi, square
    qubit, = qubits

    t = ctx.time[qubit]

    amp = ctx.params.get('amp', 0)
    frequency = ctx.params.get('frequency', 3.8e9)
    edge_type = ctx.params.get('edge_type', 'erf')
    edge = ctx.params.get('edge', 50e-9)

    if amp > 0:
        pulse = amp * square(t + edge, edge=edge, type=edge_type) >> (t / 2)
        yield ('!play', pulse * cos(2 * pi * frequency)), ('RF', qubit)
        yield ('!add_time', edge), qubit


def _AMCZ_pulse(ctx, qubits):

    t = max(ctx.time[q] for q in qubits)

    duration = ctx.params['duration']
    amp1 = ctx.params['amp1']
    amp2 = ctx.params['amp2']
    delta1 = ctx.params['delta1']
    delta2 = ctx.params['delta2']
    relative_phase = ctx.params['relative_phase']

    edge_type = ctx.params.get('edge_type', 'cos')
    edge = ctx.params.get('edge', 50e-9)
    buffer = ctx.params.get('buffer', 10e-9)

    pulse = square(width=duration, edge=edge,
                   type=edge_type) >> t + duration / 2 + edge / 2 + buffer / 2

    if amp1 != 0 and duration > 0:
        wav, _ = mixing(amp1 * pulse,
                        phase=2 * np.pi * delta1 * t,
                        freq=ctx.params['frequency'])
        yield ('!play', wav), ('RF', qubits[0])
        yield ('!set_time', t + duration + edge + buffer), qubits[0]
        yield ('!set_time', t + duration + edge + buffer), qubits[1]

    if amp2 != 0 and duration > 0:
        wav, _ = mixing(amp2 * pulse,
                        phase=2 * np.pi * delta2 * t + relative_phase,
                        freq=ctx.params['frequency'])
        yield ('!play', wav), ('RF', qubits[1])

    yield ('!add_phase', ctx.params['phi1']), qubits[0]
    yield ('!add_phase', ctx.params['phi2']), qubits[1]


@lib.opaque(name='AMCZ')
def _AMCZ(ctx, qubits):
    yield from _AMCZ_pulse(ctx, qubits)
