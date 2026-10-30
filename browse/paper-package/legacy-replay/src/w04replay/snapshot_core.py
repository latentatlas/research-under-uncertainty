"""Private evaluator and public-input boundary for a one-action development task.

No model calls or participant-code execution. Certificates are sufficient only.
"""
from copy import deepcopy
from decimal import Decimal, localcontext, ROUND_FLOOR
from fractions import Fraction as F
import ast
import cmath
import math
from pathlib import Path
from .records import digest

TASK = {
    'physical_horizon': 32, 'target_state_steps': [28, 29, 30, 31, 32],
    'target_radius': 0.05, 'escape_radius': 4.0, 'action_norm_limit': 0.6,
    'physical_actions_requested': 1, 'max_analysis_calls': 3,
    'analysis_input': 'provided_history_only', 'response': {'action': ['finite_number', 'finite_number']},
    'history_origin': 'recorded_trajectory_cut_before_the_requested_action',
}


def make_packet(case, result):
    s = case['after_step']
    history = {'states': deepcopy(result['public_history']['states'][:s + 1]),
               'actions': deepcopy(result['public_history']['actions'][:s])}
    if digest(history) != case['history_sha256']:
        raise ValueError('history source binding')
    packet = {'case_id': case['case_id'], 'history': history, 'physical_step': s,
              'remaining_physical_steps': 32 - s, 'task': deepcopy(TASK)}
    validate_packet(packet, case)
    return packet


def validate_packet(packet, expected):
    if type(packet) is not dict or set(packet) != {'case_id', 'history', 'physical_step', 'remaining_physical_steps', 'task'}:
        raise ValueError('public payload allowlist')
    if packet['case_id'] != expected['case_id'] or type(packet['physical_step']) is not int or packet['physical_step'] != expected['after_step']:
        raise ValueError('case/physical clock identity')
    s = packet['physical_step']
    if not 0 <= s < 32 or type(packet['remaining_physical_steps']) is not int or packet['remaining_physical_steps'] != 32 - s:
        raise ValueError('absolute horizon')
    if canonical_task(packet['task']) != canonical_task(TASK):
        raise ValueError('task contract')
    h = packet['history']
    if type(h) is not dict or set(h) != {'states', 'actions'} or type(h['states']) is not list or type(h['actions']) is not list:
        raise ValueError('history fields')
    if len(h['actions']) != s or len(h['states']) != s + 1 or h['states'][0] != [1., 0.]:
        raise ValueError('history clock')
    for value in h['states'] + h['actions']:
        if type(value) is not list or len(value) != 2 or any(type(x) not in (int, float) or not math.isfinite(x) for x in value):
            raise ValueError('finite pairs only')
    if any(x != round(x, 12) for row in h['states'] for x in row):
        raise ValueError('only delivered observation precision')
    if any(math.hypot(*a) > .6 + 1e-9 for a in h['actions']) or any(math.hypot(*z) > 4 + 1e-10 for z in h['states']):
        raise ValueError('active legal history')
    if digest(h) != expected['history_sha256']:
        raise ValueError('wrong history or future data')
    return True


def canonical_task(task):
    # JSON canonical equality is type-sensitive (bool is not an integer budget).
    return digest(task)


def response_action(response, W):
    if type(response) is not dict or set(response) != {'action'} or type(response['action']) is not list:
        raise ValueError('one action response only')
    return W.validate_action(response['action'])


def bind_method(W):
    core = Path(__file__).with_name('physics_base.py')
    funcs = {n.name: n for n in ast.parse(core.read_text()).body if isinstance(n, ast.FunctionDef)}
    drift = ast.parse('def drift(z):\n return (1.06 + 0.015 * abs(z)**2) * z + complex(0.12, -0.08)\n').body[0]
    transition = ast.parse('def transition(z, phi, omega, previous_action, action, coupling=0.3):\n return (drift(z) + cmath.exp(1j * phi) * action, phi + omega + coupling * previous_action.real * previous_action.imag)\n').body[0]
    if ast.dump(funcs['drift']) != ast.dump(drift) or ast.dump(funcs['transition']) != ast.dump(transition):
        raise ValueError('certificate assumptions do not match frozen physics')
    if (W.STEPS, W.LIMIT, W.TOLERANCE, W.MARGIN) != (32, .6, .05, 1e-10):
        raise ValueError('frozen task definitions')


def fixed_action(e, W):
    action = -W.drift(e.z) * cmath.exp(-1j * e.phi)
    if abs(action) > W.LIMIT:
        action *= W.LIMIT / abs(action)
    return [action.real, action.imag]


def verify_bounds(cert):
    """Second arithmetic implementation checks the complete negative recurrence."""
    if not cert.get('certified') or cert.get('method') != 'fixed_positive_projection':
        raise ValueError('no projection proof supplied')
    direction = [F(x) for x in cert['direction']]
    if sum(v * v for v in direction) > 1 or len(direction) != 2:
        raise ValueError('inadmissible direction')
    with localcontext() as context:
        context.prec = 110
        D = Decimal.from_float
        dr = [Decimal(v.numerator) / Decimal(v.denominator) for v in direction]
        z = cert['initial_state']
        p = dr[0] * D(z[0]) + dr[1] * D(z[1])
        bias = dr[0] * D(.12) + dr[1] * D(-.08)
        values = [p]
        for _ in range(cert['additional_steps']):
            if p <= 0:
                raise ValueError('nonpositive induction')
            p = (D(1.06) + D(.015) * p * p) * p + bias - D(.6) - Decimal('1e-9')
            p = p.quantize(Decimal('1e-12'), rounding=ROUND_FLOOR)
            values.append(p)
        if any(p <= 0 for p in values):
            raise ValueError('positive induction domain')
        if [float(v) for v in values] != cert['bounds']:
            raise ValueError('rational/Decimal mismatch')
        target_step = cert['after_step'] + cert['additional_steps']
        if cert['kind'] == 'unavoidable_escape':
            if not p > Decimal('4.000001') or target_step > 32:
                raise ValueError('escape threshold/horizon')
        elif cert['kind'] == 'target_deadline':
            if target_step not in (28, 29, 30, 31, 32) or not p > D(.05) + D(1e-10):
                raise ValueError('target threshold/horizon')
        else:
            raise ValueError('certificate kind')
    return True


def certificate(e, W):
    n = len(e.actions)
    if e.status == 'escaped':
        return {'certified': True, 'method': 'recorded_terminal', 'kind': 'already_escaped', 'after_step': n}
    if any(t['radius'] > W.TOLERANCE + W.MARGIN for t in e.trace if t['step'] >= 28):
        return {'certified': True, 'method': 'recorded_target_violation', 'kind': 'target_already_missed', 'after_step': n}
    if not abs(e.z):
        return {'certified': False, 'reason': 'nonpositive projection', 'absence_means': 'unresolved'}
    unit = e.z / abs(e.z)
    direction = [F(math.trunc(unit.real * 10000), 10000), F(math.trunc(unit.imag * 10000), 10000)]
    if sum(x * x for x in direction) > 1:
        raise ArithmeticError('direction norm')
    p = direction[0] * F.from_float(e.z.real) + direction[1] * F.from_float(e.z.imag)
    bias = direction[0] * F.from_float(.12) + direction[1] * F.from_float(-.08)
    seq = [float(p)]
    for more in range(1, 33 - n):
        if p <= 0:
            break
        p = (F.from_float(1.06) + F.from_float(.015) * p * p) * p + bias - F.from_float(.6) - F(1, 10**9)
        p = F((p * 10**12).__floor__(), 10**12)
        seq.append(float(p))
        if p <= 0:
            break
        kind = None
        if p > 4 + F(1, 10**6):
            kind = 'unavoidable_escape'
        elif n + more >= 28 and p > F.from_float(W.TOLERANCE) + F.from_float(W.MARGIN):
            kind = 'target_deadline'
        if kind:
            c = {'certified': True, 'method': 'fixed_positive_projection', 'kind': kind, 'after_step': n,
                 'initial_state': [e.z.real, e.z.imag], 'direction': [str(x) for x in direction],
                 'additional_steps': more, 'bounds': seq, 'roundoff_slack_per_step': 1e-9,
                 'scope': 'sufficient numerical bound, arbitrary allowed future directions; not complete viability or formal machine proof'}
            c['decimal_110_verified'] = verify_bounds(c)
            return c
    return {'certified': False, 'method': 'fixed_positive_projection', 'absence_means': 'unresolved', 'direction': [str(x) for x in direction]}


def verdict(witness_success, certified_loss):
    if type(witness_success) is not bool or type(certified_loss) is not bool:
        raise ValueError('explicit evidence booleans required')
    if witness_success and certified_loss:
        raise ValueError('contradictory positive and negative evidence')
    return 'reachable_by_witness' if witness_success else ('lost_by_certificate' if certified_loss else 'unresolved')


def assess(e, W, step):
    cert = certificate(e, W)
    test = deepcopy(e)
    while test.status == 'active':
        step(test, fixed_action(test, W))
    result = test.result()
    success = result['success_005'] is True
    return {'after_step': len(e.actions), 'verdict': verdict(success, cert['certified']), 'certificate': cert,
            'witness_success': success, 'witness_result': result,
            'blind_action_identifiability': 'unassessed', 'controller': 'one_fixed_privileged_controller_not_search'}


def score_action(before, after):
    if before['verdict'] != 'reachable_by_witness':
        return 'not_assessable_baseline_' + before['verdict']
    return {'reachable_by_witness': 'feasibility_preserved_by_witness',
            'lost_by_certificate': 'feasibility_lost_by_certificate', 'unresolved': 'unresolved'}[after['verdict']]
